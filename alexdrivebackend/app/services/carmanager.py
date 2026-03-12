import asyncio
import hashlib
import json
import time

from app.parsers.detail_parser import parse_car_detail
from app.parsers.filter_parser import (
    parse_danjis_from_js,
    parse_filter_data_from_js,
    parse_select_options,
)
from app.parsers.listing_parser import parse_car_listings, parse_total_count
from app.services.client import NetworkError, fetch_page, post_form, post_json
from app.services.session import invalidate_session

_filter_cache: dict | None = None
_filter_lock = asyncio.Lock()

_listing_cache: dict[str, dict] = {}
_listing_lock = asyncio.Lock()
LISTING_TTL = 600  # 10 minutes
LISTING_REFRESH_AT = 480  # refresh after 80% of TTL (8 minutes)
MAX_LISTING_CACHE_ENTRIES = 200
_listing_refresh_keys: set[str] = set()  # tracks keys currently being refreshed

_detail_cache: dict[str, dict] = {}
_detail_locks: dict[str, asyncio.Lock] = {}
_detail_locks_guard = asyncio.Lock()
DETAIL_TTL = 600  # 10 minutes
MAX_DETAIL_CACHE_ENTRIES = 200
DETAIL_REFRESH_AT = 480  # refresh after 80% of TTL (8 minutes)
_detail_refresh_keys: set[str] = set()


async def _get_detail_lock(key: str) -> asyncio.Lock:
    """Get or create a per-key lock. Guard lock held only for dict access (microseconds)."""
    async with _detail_locks_guard:
        if key not in _detail_locks:
            _detail_locks[key] = asyncio.Lock()
            # Prune stale locks when dict grows too large
            if len(_detail_locks) > MAX_DETAIL_CACHE_ENTRIES * 2:
                stale = [
                    k for k in _detail_locks
                    if k not in _detail_cache and not _detail_locks[k].locked()
                ]
                for k in stale:
                    del _detail_locks[k]
        return _detail_locks[key]

DEFAULT_SIDO = "102"
DEFAULT_AREA = "1013"
DEFAULT_DANJI = ""
FILTER_TTL = 24 * 60 * 60  # 24 hours in seconds

SORT_MAP: dict[str, str] = {
    "ModDt": "5",
    "RegDt": "1",
    "CarPrice": "2",
    "CarYear": "3",
    "CarMileage": "4",
}

CAR_JS_FILES = [
    "/Scripts/Common/CarBaseMaker.js",
    "/Scripts/Common/CarBaseModel.js",
    "/Scripts/Common/CarBaseModelDetail.js",
    "/Scripts/Common/CarBaseGrade.js",
    "/Scripts/Common/CarBaseGradeDetail.js",
]


async def _fetch_filter_data_internal() -> dict:
    print("[carmanager] Fetching filter data...")

    # Fetch page HTML and all JS files in parallel for speed
    tasks = [fetch_page("/Car/Data")]
    tasks.extend(fetch_page(path) for path in CAR_JS_FILES)
    tasks.append(fetch_page("/Scripts/Common/BaseDanji.js"))
    results = await asyncio.gather(*tasks)
    page_html = results[0]
    car_js_contents = list(results[1:-1])
    danji_js = results[-1]

    combined_js = "\n".join(car_js_contents)
    page_filters = parse_filter_data_from_js(combined_js)

    danjis = parse_danjis_from_js(danji_js, DEFAULT_AREA)

    color_opts = parse_select_options(page_html, "cbxSearchColor")
    fuel_opts = parse_select_options(page_html, "cbxSearchFuel")
    mission_opts = parse_select_options(page_html, "cbxSearchMission")

    data = {
        **page_filters,
        "colors": [
            {"CKeyNo": int(o["value"]), "ColorName": o["label"]}
            for o in color_opts
        ],
        "fuels": [
            {"FKeyNo": int(o["value"]), "FuelName": o["label"]}
            for o in fuel_opts
        ],
        "missions": [
            {"MKeyNo": int(o["value"]), "MissionName": o["label"]}
            for o in mission_opts
        ],
        "danjis": danjis,
    }

    global _filter_cache
    _filter_cache = {"data": data, "expiry": time.time() + FILTER_TTL}
    print(f"[carmanager] Filter data cached ({len(data['makers'])} makers, {len(data['colors'])} colors)")
    return data


async def get_filter_data() -> dict:
    global _filter_cache

    if _filter_cache and time.time() < _filter_cache["expiry"]:
        return _filter_cache["data"]

    # Thundering-herd protection via asyncio.Lock (double-check pattern)
    async with _filter_lock:
        if _filter_cache and time.time() < _filter_cache["expiry"]:
            return _filter_cache["data"]
        try:
            return await _fetch_filter_data_internal()
        except NetworkError:
            if _filter_cache:
                print("[carmanager] Serving stale filter cache due to network error")
                return _filter_cache["data"]
            raise


def _evict_oldest(cache: dict[str, dict], max_entries: int) -> None:
    """Evict the entry with the earliest expiry when cache exceeds max size."""
    if len(cache) <= max_entries:
        return
    oldest_key = min(cache, key=lambda k: cache[k]["expiry"])
    del cache[oldest_key]


def _build_datapart_params(params: dict) -> dict:
    """Build /Car/DataPart JSON request body from query params."""
    year_from = params.get("CarYearFrom") or ""
    year_to = params.get("CarYearTo") or ""

    def _int_or_none(key: str) -> int | None:
        val = params.get(key)
        if val:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
        return None

    return {"para": {
        "PageNow": params.get("PageNow") or 1,
        "PageSize": str(params.get("PageSize") or 20),
        "PageSort": SORT_MAP.get(params.get("PageSort") or "", "5"),
        "PageAscDesc": "0" if params.get("PageAscDesc") == "ASC" else "1",
        "CarMode": "0",
        "CarSiDoNo": params.get("CarSiDoNo") or DEFAULT_SIDO,
        "CarSiDoAreaNo": params.get("CarSiDoAreaNo") or DEFAULT_AREA,
        "CarDanjiNo": params.get("DanjiNo") or DEFAULT_DANJI,
        "CarMakerNo": _int_or_none("CarMakerNo"),
        "CarModelNo": _int_or_none("CarModelNo"),
        "CarModelDetailNo": params.get("CarModelDetailNo") or "",
        "CarGradeNo": params.get("CarGradeNo") or "",
        "CarGradeDetailNo": params.get("CarGradeDetailNo") or "",
        "CarMakeSDate": f"{year_from}-01" if year_from else "",
        "CarMakeEDate": f"{year_to}-12" if year_to else "",
        "CarDriveSKm": _int_or_none("CarMileageFrom"),
        "CarDriveEKm": _int_or_none("CarMileageTo"),
        "CarMission": params.get("CarMissionNo") or "",
        "CarFuel": params.get("CarFuelNo") or "",
        "CarColor": params.get("CarColorNo") or "",
        "CarSMoney": _int_or_none("CarPriceFrom"),
        "CarEMoney": _int_or_none("CarPriceTo"),
        "CarIsLPG": "True" if params.get("CarLpg") else "False",
        "CarIsSago": "False",
        "CarIsPhoto": "True" if params.get("CarPhoto") else "False",
        "CarIsSaleAmount": "True" if params.get("CarSalePrice") else "False",
        "CarIsCarCheck": "True" if params.get("CarInspection") else "False",
        "CarIsLeaseCheck": "True" if params.get("CarLease") else "False",
        "CarName": "",
        "CarDealerName": "",
        "CarShopName": "",
        "CarDealerHP": "",
        "CarNumber": "",
        "CarOption": "",
        "CarTruckTonS": "",
        "CarTruckTonE": "",
    }}


async def _fetch_and_cache_listings(cache_key: str, json_body: dict, _retried: bool = False) -> dict:
    """Fetch listings from carmanager via /Car/DataPart JSON API, parse, cache, and return."""
    html = await post_json("/Car/DataPart", json_body)
    listings = parse_car_listings(html)
    total = parse_total_count(html)

    print(f"[carmanager] Listings: {len(listings)}/{total}, HTML length: {len(html)}")

    # 0 listings from non-empty HTML likely means expired session
    if len(listings) == 0 and total == 0 and len(html) > 1000 and not _retried:
        print("[carmanager] 0 listings from non-empty HTML — session likely expired, retrying...")
        invalidate_session()
        return await _fetch_and_cache_listings(cache_key, json_body, _retried=True)

    if len(listings) == 0 and len(html) > 1000 and _retried:
        print("[carmanager] WARNING: still 0 listings after re-auth — selectors may be outdated")

    result = {"listings": listings, "total": total}
    _listing_cache[cache_key] = {"data": result, "expiry": time.time() + LISTING_TTL}
    _evict_oldest(_listing_cache, MAX_LISTING_CACHE_ENTRIES)
    return result


async def _refresh_listing_cache(cache_key: str, json_body: dict) -> None:
    """Background refresh — errors are silently caught (stale data stays)."""
    _listing_refresh_keys.add(cache_key)
    try:
        await _fetch_and_cache_listings(cache_key, json_body)
        print(f"[carmanager] Background refresh OK ({cache_key[:8]})")
    except Exception as e:
        print(f"[carmanager] Background refresh failed ({cache_key[:8]}): {e}")
    finally:
        _listing_refresh_keys.discard(cache_key)


async def get_car_listings(params: dict) -> dict:
    json_body = _build_datapart_params(params)
    cache_key = hashlib.md5(json.dumps(json_body, sort_keys=True).encode()).hexdigest()

    # Check cache (fast path, no lock)
    cached = _listing_cache.get(cache_key)
    if cached:
        age = time.time() - (cached["expiry"] - LISTING_TTL)
        if age < LISTING_TTL:  # not expired
            if age >= LISTING_REFRESH_AT and cache_key not in _listing_refresh_keys:
                # Stale-while-revalidate: return cached, refresh in background
                asyncio.create_task(_refresh_listing_cache(cache_key, json_body))
            print(f"[carmanager] Listing cache hit ({cache_key[:8]})")
            return cached["data"]

    # Cache miss — blocking fetch
    async with _listing_lock:
        # Double-check under lock
        cached = _listing_cache.get(cache_key)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        try:
            return await _fetch_and_cache_listings(cache_key, json_body)
        except NetworkError:
            cached = _listing_cache.get(cache_key)
            if cached:
                print(f"[carmanager] Serving stale listing cache due to network error ({cache_key[:8]})")
                return cached["data"]
            raise


async def _refresh_detail_cache(encrypted_id: str) -> None:
    """Background refresh — errors caught silently (stale data stays)."""
    _detail_refresh_keys.add(encrypted_id)
    try:
        html = await post_form("/PopupFrame/CarDetailEnc", {"encarno": encrypted_id})
        result = parse_car_detail(html, encrypted_id)
        result["inspectionUrl"] = result.pop("inspectionUrl", None)
        _detail_cache[encrypted_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        print(f"[carmanager] Detail background refresh OK ({encrypted_id[:16]}...)")
    except Exception as e:
        print(f"[carmanager] Detail background refresh failed ({encrypted_id[:16]}...): {e}")
    finally:
        _detail_refresh_keys.discard(encrypted_id)


async def get_car_detail(encrypted_id: str) -> dict:
    # Check cache (fast path, no lock)
    cached = _detail_cache.get(encrypted_id)
    if cached:
        age = time.time() - (cached["expiry"] - DETAIL_TTL)
        if age < DETAIL_TTL:  # not expired
            if age >= DETAIL_REFRESH_AT and encrypted_id not in _detail_refresh_keys:
                asyncio.create_task(_refresh_detail_cache(encrypted_id))
            print(f"[carmanager] Detail cache hit ({encrypted_id[:16]}...)")
            return cached["data"]

    # Double-check under per-key lock
    lock = await _get_detail_lock(encrypted_id)
    async with lock:
        cached = _detail_cache.get(encrypted_id)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        try:
            html = await post_form("/PopupFrame/CarDetailEnc", {"encarno": encrypted_id})
        except NetworkError:
            cached = _detail_cache.get(encrypted_id)
            if cached:
                print(f"[carmanager] Serving stale detail cache due to network error ({encrypted_id[:16]}...)")
                return cached["data"]
            raise

        result = parse_car_detail(html, encrypted_id)

        # Pass inspection URL through (no external fetch needed)
        result["inspectionUrl"] = result.pop("inspectionUrl", None)

        _detail_cache[encrypted_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        return result
