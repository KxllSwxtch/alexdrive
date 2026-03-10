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
from app.services.client import NetworkError, fetch_page, post_form

_filter_cache: dict | None = None
_filter_lock = asyncio.Lock()

_listing_cache: dict[str, dict] = {}
_listing_lock = asyncio.Lock()
LISTING_TTL = 600  # 10 minutes
LISTING_REFRESH_AT = 480  # refresh after 80% of TTL (8 minutes)
MAX_LISTING_CACHE_ENTRIES = 200
_listing_refresh_keys: set[str] = set()  # tracks keys currently being refreshed

_detail_cache: dict[str, dict] = {}
_detail_lock = asyncio.Lock()
DETAIL_TTL = 600  # 10 minutes
MAX_DETAIL_CACHE_ENTRIES = 200

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

    page_html = await fetch_page("/Car/Data")

    # Fetch external JS files sequentially to avoid proxy connection limits
    car_js_contents: list[str] = []
    for path in CAR_JS_FILES:
        car_js_contents.append(await fetch_page(path))
    danji_js = await fetch_page("/Scripts/Common/BaseDanji.js")

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


def _build_form_fields(params: dict) -> dict[str, str]:
    """Build carmanager form fields from query params."""
    return {
        "cbxSearchSiDo": params.get("CarSiDoNo") or DEFAULT_SIDO,
        "cbxSearchSiDoArea": params.get("CarSiDoAreaNo") or DEFAULT_AREA,
        "cbxSearchDanji": params.get("DanjiNo") or DEFAULT_DANJI,
        "tbxSearchMaker": params.get("CarMakerNo") or "",
        "tbxSearchModel": params.get("CarModelNo") or "",
        "tbxSearchModelDetail": params.get("CarModelDetailNo") or "",
        "tbxSearchGrade": params.get("CarGradeNo") or "",
        "tbxSearchGradeDetail": params.get("CarGradeDetailNo") or "",
        "cbxSearchMission": params.get("CarMissionNo") or "",
        "cbxSearchFuel": params.get("CarFuelNo") or "",
        "cbxSearchColor": params.get("CarColorNo") or "",
        "cbxSearchMakeSYear": params.get("CarYearFrom") or "",
        "cbxSearchMakeSDay": "",
        "cbxSearchMakeEYear": params.get("CarYearTo") or "",
        "cbxSearchMakeEDay": "",
        "cbxSearchDriveS": params.get("CarMileageFrom") or "",
        "cbxSearchDriveE": params.get("CarMileageTo") or "",
        "cbxSearchMoneyS": params.get("CarPriceFrom") or "",
        "cbxSearchMoneyE": params.get("CarPriceTo") or "",
        "tbxSearchName": params.get("SearchName") or "",
        "cbxSearchCarOption": params.get("CarPhoto") or "",
        "cbxSearchCarInsurance": params.get("CarInsurance") or "",
        "cbxSearchCarInspection": params.get("CarInspection") or "",
        "cbxSearchCarLease": params.get("CarLease") or "",
        "cbxSearchLpg": params.get("CarLpg") or "",
        "cbxSearchCarSalePrice": params.get("CarSalePrice") or "",
        "tbxSearchCarNo": params.get("SearchCarNo") or "",
        "page": str(params["PageNow"]) if params.get("PageNow") is not None else "",
        "sbxPageSort": SORT_MAP.get(params.get("PageSort") or "", "5"),
        "sbxPageAscDesc": "0" if params.get("PageAscDesc") == "ASC" else "1",
        "sbxPageRowCount": str(params.get("PageSize") or 20),
        "hdfDefaultSido": DEFAULT_SIDO,
        "hdfDefaultCity": DEFAULT_AREA,
        "hdfDefaultDanji": DEFAULT_DANJI,
        "hdfUserGubunNo": "100",
        "multiSelectType": "1",
        "tbxOptionArr": "",
        "cbxSearchOption": "",
        "fristSetSido": "N",
        "fristSetCity": "N",
        "searchOptType": "001",
        "isAscDesc": "0" if params.get("PageAscDesc") == "ASC" else "1",
    }


async def _fetch_and_cache_listings(cache_key: str, form_fields: dict) -> dict:
    """Fetch listings from carmanager, parse, cache, and return."""
    html = await post_form("/Car/Data", form_fields)
    listings = parse_car_listings(html)
    total = parse_total_count(html)

    print(f"[carmanager] Listings: {len(listings)}/{total}, HTML length: {len(html)}")

    if len(listings) == 0 and len(html) > 1000:
        print("[carmanager] WARNING: 0 listings parsed from non-empty HTML — selectors may be outdated")

    result = {"listings": listings, "total": total}
    _listing_cache[cache_key] = {"data": result, "expiry": time.time() + LISTING_TTL}
    _evict_oldest(_listing_cache, MAX_LISTING_CACHE_ENTRIES)
    return result


async def _refresh_listing_cache(cache_key: str, form_fields: dict) -> None:
    """Background refresh — errors are silently caught (stale data stays)."""
    _listing_refresh_keys.add(cache_key)
    try:
        await _fetch_and_cache_listings(cache_key, form_fields)
        print(f"[carmanager] Background refresh OK ({cache_key[:8]})")
    except Exception as e:
        print(f"[carmanager] Background refresh failed ({cache_key[:8]}): {e}")
    finally:
        _listing_refresh_keys.discard(cache_key)


async def get_car_listings(params: dict) -> dict:
    form_fields = _build_form_fields(params)
    cache_key = hashlib.md5(json.dumps(form_fields, sort_keys=True).encode()).hexdigest()

    # Check cache (fast path, no lock)
    cached = _listing_cache.get(cache_key)
    if cached:
        age = time.time() - (cached["expiry"] - LISTING_TTL)
        if age < LISTING_TTL:  # not expired
            if age >= LISTING_REFRESH_AT and cache_key not in _listing_refresh_keys:
                # Stale-while-revalidate: return cached, refresh in background
                asyncio.create_task(_refresh_listing_cache(cache_key, form_fields))
            print(f"[carmanager] Listing cache hit ({cache_key[:8]})")
            return cached["data"]

    # Cache miss — blocking fetch
    async with _listing_lock:
        # Double-check under lock
        cached = _listing_cache.get(cache_key)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        try:
            return await _fetch_and_cache_listings(cache_key, form_fields)
        except NetworkError:
            cached = _listing_cache.get(cache_key)
            if cached:
                print(f"[carmanager] Serving stale listing cache due to network error ({cache_key[:8]})")
                return cached["data"]
            raise


async def get_car_detail(encrypted_id: str) -> dict:
    # Check cache (fast path, no lock)
    cached = _detail_cache.get(encrypted_id)
    if cached and time.time() < cached["expiry"]:
        print(f"[carmanager] Detail cache hit ({encrypted_id[:16]}...)")
        return cached["data"]

    # Double-check under lock
    async with _detail_lock:
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
