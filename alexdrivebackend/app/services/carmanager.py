import asyncio
import hashlib
import json
import os
import random
import time

from app.parsers.detail_parser import parse_car_detail
from app.parsers.filter_parser import (
    parse_filter_data_from_js,
    parse_select_options,
)
from app.parsers.listing_parser import parse_car_listings, parse_total_count
from app.services.client import NetworkError, fetch_page, post_form, post_json, post_json_parsed
from app.services.session import invalidate_session

_filter_cache: dict | None = None
_filter_lock = asyncio.Lock()

_listing_cache: dict[str, dict] = {}
_listing_lock = asyncio.Lock()
LISTING_TTL = 600  # 10 minutes
LISTING_REFRESH_AT = 480  # refresh after 80% of TTL (8 minutes)
MAX_LISTING_CACHE_ENTRIES = 200
_listing_refresh_keys: set[str] = set()  # tracks keys currently being refreshed
LISTING_REFRESH_INTERVAL = 30 * 60  # 30 minutes — proactive refresh

_detail_cache: dict[str, dict] = {}
_detail_locks: dict[str, asyncio.Lock] = {}
_detail_locks_guard = asyncio.Lock()
DETAIL_TTL = 600  # 10 minutes
MAX_DETAIL_CACHE_ENTRIES = 1000
DETAIL_REFRESH_AT = 480  # refresh after 80% of TTL (8 minutes)
_detail_refresh_keys: set[str] = set()

_last_successful_parse: float = 0.0

_RATE_LIMIT_MARKER = "limits_box"

# --- Global outbound request throttling ---
_last_request_time: float = 0.0
_throttle_lock = asyncio.Lock()
MIN_REQUEST_INTERVAL = 3.0  # seconds between ANY carmanager request
MAX_REQUEST_JITTER = 3.0  # random 0-3s added to throttle interval

# --- Rate-limit tracking ---
_last_rate_limit_time: float = 0.0
_RATE_LIMIT_COOLDOWN = 300.0  # skip detail warming for 5 min after rate limit
_rate_limit_count: int = 0  # consecutive rate limits (for escalating backoff)


async def _throttle_request() -> None:
    """Enforce minimum interval (with random jitter) between ALL outbound requests to carmanager."""
    global _last_request_time
    async with _throttle_lock:
        now = time.time()
        interval = MIN_REQUEST_INTERVAL + random.uniform(0, MAX_REQUEST_JITTER)
        elapsed = now - _last_request_time
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)
        _last_request_time = time.time()


def _record_rate_limit() -> None:
    """Record a rate-limit event and escalate cooldown."""
    global _last_rate_limit_time, _rate_limit_count
    _last_rate_limit_time = time.time()
    _rate_limit_count += 1
    print(f"[carmanager] Rate limit #{_rate_limit_count} recorded (cooldown={_get_cooldown()}s)")


def _get_cooldown() -> float:
    """Get current cooldown duration, escalating with consecutive rate limits."""
    # 5min, 10min, 20min (capped)
    return min(_RATE_LIMIT_COOLDOWN * (2 ** min(_rate_limit_count - 1, 2)), 1200.0)


def _clear_rate_limit() -> None:
    """Clear rate-limit state after a successful request."""
    global _rate_limit_count
    if _rate_limit_count > 0:
        _rate_limit_count = 0
        print("[carmanager] Rate limit cleared (successful request)")


def is_rate_limited() -> bool:
    """Check if we're currently in rate-limit cooldown."""
    if not _last_rate_limit_time:
        return False
    return time.time() - _last_rate_limit_time < _get_cooldown()


def get_last_successful_parse() -> float:
    """Return timestamp of last successful listing parse (0.0 if never)."""
    return _last_successful_parse


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
    global _filter_cache
    print("[carmanager] Fetching filter data...")

    # 1. Fetch JS files sequentially with throttle
    car_js_contents = []
    for path in CAR_JS_FILES:
        await _throttle_request()
        car_js_contents.append(await fetch_page(path))

    combined_js = "\n".join(car_js_contents)
    page_filters = parse_filter_data_from_js(combined_js)

    # 2. Fetch danjis via JSON API (no JS parsing needed)
    await _throttle_request()
    danjis_raw = await post_json_parsed(f"/CodeBase/JsonBaseCodeDanji/{DEFAULT_AREA}")
    danjis = [
        {"DanjiNo": int(d["DanjiNo"]), "DanjiName": d["DanjiName"]}
        for d in danjis_raw
    ]

    # 3. Fetch /Car/Data HTML for color/fuel/mission select options
    await _throttle_request()
    page_html = await fetch_page("/Car/Data")

    # Check for rate limit on the Car/Data page itself
    if _RATE_LIMIT_MARKER in page_html:
        _record_rate_limit()
        print("[carmanager] Rate-limited on /Car/Data during filter fetch")
        # Still try to use the JS-based filters we already have
        if _filter_cache:
            return _filter_cache["data"]

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
        "CarName": params.get("SearchName") or "",
        "CarDealerName": "",
        "CarShopName": "",
        "CarDealerHP": "",
        "CarNumber": params.get("SearchCarNo") or "",
        "CarOption": "",
        "CarTruckTonS": "",
        "CarTruckTonE": "",
    }}


async def _fetch_and_cache_listings(
    cache_key: str, json_body: dict,
    _retried: bool = False, _rate_limit_attempt: int = 0,
) -> dict:
    """Fetch listings from carmanager via /Car/DataPart JSON API, parse, cache, and return."""
    global _last_successful_parse, _last_rate_limit_time

    await _throttle_request()
    html = await post_json("/Car/DataPart", json_body)

    # Rate-limit detection — not an auth issue, don't invalidate session or retry
    if _RATE_LIMIT_MARKER in html:
        _record_rate_limit()
        print("[carmanager] Rate-limited by carmanager.co.kr (limits_box detected)")

        # 1. Serve stale cache if available (and extend its TTL)
        existing = _listing_cache.get(cache_key)
        if existing and existing["data"].get("listings"):
            existing["expiry"] = time.time() + LISTING_TTL  # extend TTL
            print(f"[carmanager] Serving stale cached listings ({len(existing['data']['listings'])} cars)")
            return existing["data"]

        # 2. No cache → retry with backoff (max 2 retries)
        if _rate_limit_attempt < 2:
            delay = 3.0 * (2 ** _rate_limit_attempt)  # 3s, 6s
            print(f"[carmanager] No cache available, retrying in {delay}s (attempt {_rate_limit_attempt + 1}/2)")
            await asyncio.sleep(delay)
            return await _fetch_and_cache_listings(
                cache_key, json_body, _retried, _rate_limit_attempt + 1,
            )

        # 3. All retries exhausted
        print("[carmanager] Rate-limit retries exhausted, returning empty")
        return {"listings": [], "total": 0, "status": "rate_limited"}

    listings = parse_car_listings(html)
    total = parse_total_count(html)

    print(f"[carmanager] Listings: {len(listings)}/{total}, HTML length: {len(html)}")

    # 0 listings from any non-trivial HTML likely means expired session or endpoint issue
    html_suspicious = len(listings) == 0 and total == 0 and len(html) > 50

    if html_suspicious and not _retried:
        print(f"[carmanager] 0 listings from HTML ({len(html)} bytes) — retrying with fresh session...")
        invalidate_session()
        return await _fetch_and_cache_listings(cache_key, json_body, _retried=True)

    if html_suspicious and _retried:
        print(f"[carmanager] WARNING: still 0 listings after re-auth (HTML={len(html)} bytes)")
        print(f"[carmanager] HTML sample: {html[:500]}")

    # Determine result status
    if len(listings) > 0:
        status = "ok"
        _last_successful_parse = time.time()
        _clear_rate_limit()
    elif len(html) <= 50:
        status = "empty"
    else:
        status = "parse_failure"

    result = {"listings": listings, "total": total, "status": status}
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


async def listing_refresh_loop() -> None:
    """Proactively refresh the default listing cache so page 1 never goes cold."""
    default_params = {
        "PageNow": 1, "PageSize": 20,
        "PageSort": "ModDt", "PageAscDesc": "DESC",
    }
    while True:
        jittered = LISTING_REFRESH_INTERVAL + random.uniform(-5 * 60, 5 * 60)
        await asyncio.sleep(max(0.0, jittered))

        if is_rate_limited():
            print("[carmanager] Proactive refresh skipped (rate-limited)")
            continue

        try:
            json_body = _build_datapart_params(default_params)
            cache_key = hashlib.md5(
                json.dumps(json_body, sort_keys=True).encode()
            ).hexdigest()

            # Skip if cache is still fresh
            cached = _listing_cache.get(cache_key)
            if cached:
                age = time.time() - (cached["expiry"] - LISTING_TTL)
                if age < LISTING_REFRESH_AT:
                    print(f"[carmanager] Proactive refresh skipped (age={int(age)}s)")
                    continue

            result = await _fetch_and_cache_listings(cache_key, json_body)
            print("[carmanager] Proactive default listing refresh OK")
        except Exception as e:
            print(f"[carmanager] Proactive listing refresh failed: {e}")


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
        await _throttle_request()
        html = await post_form("/PopupFrame/CarDetailEnc", {"encarno": encrypted_id})
        if _RATE_LIMIT_MARKER in html:
            _record_rate_limit()
            print(f"[carmanager] Detail refresh rate-limited ({encrypted_id[:16]}...)")
            return
        result = parse_car_detail(html, encrypted_id)
        result["inspectionUrl"] = result.pop("inspectionUrl", None)
        _detail_cache[encrypted_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        _clear_rate_limit()
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

        await _throttle_request()
        try:
            html = await post_form("/PopupFrame/CarDetailEnc", {"encarno": encrypted_id})
        except NetworkError:
            cached = _detail_cache.get(encrypted_id)
            if cached:
                print(f"[carmanager] Serving stale detail cache due to network error ({encrypted_id[:16]}...)")
                return cached["data"]
            raise

        # Rate-limit detection on detail requests
        if _RATE_LIMIT_MARKER in html:
            _record_rate_limit()
            print(f"[carmanager] Detail request rate-limited ({encrypted_id[:16]}...)")
            cached = _detail_cache.get(encrypted_id)
            if cached:
                cached["expiry"] = time.time() + DETAIL_TTL
                return cached["data"]
            raise NetworkError("Rate-limited on detail request, no cache available")

        result = parse_car_detail(html, encrypted_id)

        # Pass inspection URL through (no external fetch needed)
        result["inspectionUrl"] = result.pop("inspectionUrl", None)

        _detail_cache[encrypted_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        _clear_rate_limit()
        return result


# --- Disk persistence for detail cache ---

DETAIL_CACHE_PATH = "/tmp/alexdrive_detail_cache.json"
DETAIL_CACHE_PERSIST_INTERVAL = 5 * 60  # 5 minutes


def _save_detail_cache_to_disk() -> None:
    """Write non-expired detail cache entries to disk."""
    now = time.time()
    entries = {
        k: v for k, v in _detail_cache.items()
        if v["expiry"] > now
    }
    if not entries:
        return
    try:
        tmp_path = DETAIL_CACHE_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(entries, f)
        os.replace(tmp_path, DETAIL_CACHE_PATH)
        print(f"[carmanager] Saved {len(entries)} detail cache entries to disk")
    except Exception as e:
        print(f"[carmanager] Failed to save detail cache to disk: {e}")


def _load_detail_cache_from_disk() -> int:
    """Load detail cache entries from disk. Returns count loaded."""
    try:
        with open(DETAIL_CACHE_PATH) as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

    now = time.time()
    loaded = 0
    for k, v in entries.items():
        if v.get("expiry", 0) > now and k not in _detail_cache:
            _detail_cache[k] = v
            loaded += 1

    if loaded:
        print(f"[carmanager] Loaded {loaded} detail cache entries from disk")
    return loaded


async def detail_cache_persist_loop() -> None:
    """Periodically save the detail cache to disk."""
    while True:
        await asyncio.sleep(DETAIL_CACHE_PERSIST_INTERVAL)
        _save_detail_cache_to_disk()


# --- Proactive detail cache warming ---


DETAIL_WARMING_MAX = 2  # warm at most 2 details per listing load


async def warm_detail_cache_for_listings(listings: list[dict]) -> None:
    """Background: warm detail cache for listing IDs not already cached.

    Requests are sequential (no concurrency) with global throttle between each,
    and warming stops immediately if a rate limit is detected.
    """
    if is_rate_limited():
        print("[carmanager] Skipping detail cache warming (rate-limited)")
        return

    ids_to_warm = [
        car["encryptedId"] for car in listings
        if car.get("encryptedId") and car["encryptedId"] not in _detail_cache
    ][:DETAIL_WARMING_MAX]

    if not ids_to_warm:
        return

    print(f"[carmanager] Warming {len(ids_to_warm)} detail caches (sequential)...")
    for eid in ids_to_warm:
        if is_rate_limited():
            print("[carmanager] Stopping detail warming (rate-limited)")
            break
        try:
            await get_car_detail(eid)
        except Exception:
            pass
