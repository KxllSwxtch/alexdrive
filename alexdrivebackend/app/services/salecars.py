import asyncio
import hashlib
import json
import os
import random
import time
from urllib.parse import urlencode

from app.config import settings
from app.parsers.detail_parser import parse_car_detail
from app.parsers.filter_parser import parse_filter_data_from_js
from app.parsers.listing_parser import parse_car_listings, parse_total_count
from app.services.client import NetworkError, fetch_page, post_form

_filter_cache: dict | None = None
_filter_lock = asyncio.Lock()

_listing_cache: dict[str, dict] = {}
_listing_lock = asyncio.Lock()
LISTING_TTL = 600  # 10 minutes
LISTING_REFRESH_AT = 480  # refresh after 80% of TTL (8 minutes)
MAX_LISTING_CACHE_ENTRIES = 200
_listing_refresh_keys: set[str] = set()
LISTING_REFRESH_INTERVAL = 30 * 60  # 30 minutes — proactive refresh

_detail_cache: dict[str, dict] = {}
_detail_locks: dict[str, asyncio.Lock] = {}
_detail_locks_guard = asyncio.Lock()
DETAIL_TTL = 600  # 10 minutes
MAX_DETAIL_CACHE_ENTRIES = 1000
DETAIL_REFRESH_AT = 480
_detail_refresh_keys: set[str] = set()

_last_successful_parse: float = 0.0

# --- Location-based filtering (strict Suwon whitelist) ---
ALLOWED_LOCATIONS: set[str] = {"수원"}
_excluded_car_ids: dict[str, float] = {}  # car_id → timestamp when excluded
_verified_suwon_ids: set[str] = set()  # car IDs confirmed in ALLOWED_LOCATIONS
EXCLUSION_SET_PATH = "/tmp/alexdrive_excluded_ids.json"
EXCLUSION_TTL = 7 * 24 * 60 * 60  # 7 days

# --- Location cache (for scanner — tracks ALL checked cars) ---
_location_cache: dict[str, tuple[str, float]] = {}  # car_id → (location, timestamp)
LOCATION_CACHE_PATH = "/tmp/alexdrive_location_cache.json"


def _update_location_tracking(car_id: str, location: str) -> None:
    """Update all location-tracking data structures after learning a car's location."""
    _location_cache[car_id] = (location, time.time())
    if location in ALLOWED_LOCATIONS:
        _verified_suwon_ids.add(car_id)
        _excluded_car_ids.pop(car_id, None)
    else:
        _excluded_car_ids[car_id] = time.time()
        _verified_suwon_ids.discard(car_id)

# --- Background location scanner ---
SCANNER_EXTRA_DELAY = 1.0  # extra sleep between scanner requests (yield to users)
SCANNER_RESCAN_INTERVAL = 2 * 60 * 60  # 2 hours between full passes
SCANNER_STARTUP_DELAY = 60  # wait for prewarm to finish

_RATE_LIMIT_MARKER = "limits_box"

# --- Global outbound request throttling ---
_last_request_time: float = 0.0
_throttle_lock = asyncio.Lock()
MIN_REQUEST_INTERVAL = 2.0  # was 0.3 — too aggressive, caused IP ban
MAX_REQUEST_JITTER = 1.0

# --- Rate-limit tracking ---
_last_rate_limit_time: float = 0.0
_RATE_LIMIT_COOLDOWN = 300.0
_rate_limit_count: int = 0

FILTER_TTL = 24 * 60 * 60  # 24 hours

# Carmanager public JS files for filter hierarchy (accessible without auth)
CAR_JS_FILES = [
    "/Scripts/Common/CarBaseMaker.js",
    "/Scripts/Common/CarBaseModel.js",
    "/Scripts/Common/CarBaseModelDetail.js",
    "/Scripts/Common/CarBaseGrade.js",
    "/Scripts/Common/CarBaseGradeDetail.js",
]

# Hardcoded filter options — these rarely change and avoid needing auth
# IDs must match salecars.co.kr search dropdown values (not carmanager)
STATIC_COLORS = [
    {"CKeyNo": 101, "ColorName": "검정색"},
    {"CKeyNo": 102, "ColorName": "흰색"},
    {"CKeyNo": 103, "ColorName": "진주색"},
    {"CKeyNo": 106, "ColorName": "빨간색"},
    {"CKeyNo": 108, "ColorName": "하늘색"},
    {"CKeyNo": 109, "ColorName": "주황색"},
    {"CKeyNo": 110, "ColorName": "회색"},
    {"CKeyNo": 111, "ColorName": "갈색"},
    {"CKeyNo": 114, "ColorName": "은색"},
    {"CKeyNo": 115, "ColorName": "녹색"},
    {"CKeyNo": 116, "ColorName": "보라색"},
    {"CKeyNo": 119, "ColorName": "금색"},
    {"CKeyNo": 124, "ColorName": "노란색"},
    {"CKeyNo": 129, "ColorName": "파란색"},
]
STATIC_FUELS = [
    {"FKeyNo": 101, "FuelName": "휘발유"},
    {"FKeyNo": 102, "FuelName": "경유"},
    {"FKeyNo": 103, "FuelName": "LPG"},
    {"FKeyNo": 104, "FuelName": "휘발유/LPG겸"},
    {"FKeyNo": 105, "FuelName": "휘발유/CNG겸"},
    {"FKeyNo": 106, "FuelName": "휘발유 하이브리드"},
    {"FKeyNo": 107, "FuelName": "LPG 하이브리드"},
    {"FKeyNo": 108, "FuelName": "경유 하이브리드"},
    {"FKeyNo": 109, "FuelName": "전기"},
    {"FKeyNo": 110, "FuelName": "CNG"},
    {"FKeyNo": 111, "FuelName": "수소"},
]
STATIC_MISSIONS = [
    {"MKeyNo": 1, "MissionName": "오토"},
    {"MKeyNo": 2, "MissionName": "수동"},
    {"MKeyNo": 3, "MissionName": "세미오토"},
    {"MKeyNo": 4, "MissionName": "CVT"},
]


async def _throttle_request() -> None:
    """Enforce minimum interval between outbound requests."""
    global _last_request_time
    async with _throttle_lock:
        now = time.time()
        interval = MIN_REQUEST_INTERVAL + random.uniform(0, MAX_REQUEST_JITTER)
        elapsed = now - _last_request_time
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)
        _last_request_time = time.time()


def _record_rate_limit() -> None:
    global _last_rate_limit_time, _rate_limit_count
    _last_rate_limit_time = time.time()
    _rate_limit_count += 1
    print(f"[salecars] Rate limit #{_rate_limit_count} recorded (cooldown={_get_cooldown()}s)")


def _get_cooldown() -> float:
    if _rate_limit_count <= 0:
        return _RATE_LIMIT_COOLDOWN
    return min(_RATE_LIMIT_COOLDOWN * (2 ** min(_rate_limit_count - 1, 2)), 1200.0)


def _clear_rate_limit() -> None:
    global _rate_limit_count
    if _rate_limit_count > 0:
        _rate_limit_count = max(0, _rate_limit_count - 1)
        print(f"[salecars] Rate limit decremented to {_rate_limit_count}")


def is_rate_limited() -> bool:
    if not _last_rate_limit_time:
        return False
    return time.time() - _last_rate_limit_time < _get_cooldown()


def get_rate_limit_retry_after() -> int:
    if not _last_rate_limit_time:
        return 0
    remaining = _get_cooldown() - (time.time() - _last_rate_limit_time)
    return max(int(remaining), 0)


def get_last_successful_parse() -> float:
    return _last_successful_parse


async def _get_detail_lock(key: str) -> asyncio.Lock:
    async with _detail_locks_guard:
        if key not in _detail_locks:
            _detail_locks[key] = asyncio.Lock()
            if len(_detail_locks) > MAX_DETAIL_CACHE_ENTRIES * 2:
                stale = [
                    k for k in _detail_locks
                    if k not in _detail_cache and not _detail_locks[k].locked()
                ]
                for k in stale:
                    del _detail_locks[k]
        return _detail_locks[key]


# --- Filter data ---


async def _fetch_filter_data_internal() -> dict:
    global _filter_cache
    print("[salecars] Fetching filter data from carmanager JS files...")

    # Fetch public JS files from carmanager in parallel (no auth needed)
    urls = [f"{settings.carmanager_base_url}{path}" for path in CAR_JS_FILES]
    car_js_contents = await asyncio.gather(*[fetch_page(url) for url in urls])

    combined_js = "\n".join(car_js_contents)
    page_filters = parse_filter_data_from_js(combined_js)

    data = {
        **page_filters,
        "colors": STATIC_COLORS,
        "fuels": STATIC_FUELS,
        "missions": STATIC_MISSIONS,
        "danjis": [],  # not supported by salecars
    }

    _filter_cache = {"data": data, "expiry": time.time() + FILTER_TTL}
    print(f"[salecars] Filter data cached ({len(data['makers'])} makers)")
    return data


async def get_filter_data() -> dict:
    global _filter_cache
    if _filter_cache and time.time() < _filter_cache["expiry"]:
        return _filter_cache["data"]

    async with _filter_lock:
        if _filter_cache and time.time() < _filter_cache["expiry"]:
            return _filter_cache["data"]
        try:
            return await _fetch_filter_data_internal()
        except NetworkError:
            if _filter_cache:
                print("[salecars] Serving stale filter cache due to network error")
                return _filter_cache["data"]
            raise


# --- URL construction ---


COUNTRY_MAP = {"1": "kor", "2": "foreign", "3": "freight"}


def _build_listing_url(params: dict) -> str:
    """Build salecars.co.kr listing URL from query params."""
    base = settings.salecars_base_url

    # Country/category
    carnation = str(params.get("carnation") or "")
    country = COUNTRY_MAP.get(carnation, "all")

    # Page number
    page = params.get("PageNow") or 1

    # Build query params
    qp = {
        "ascending": "asc" if params.get("PageAscDesc") == "ASC" else "desc",
        "view": "image",
        "customSelect": str(params.get("PageSize") or 24),
        "country": country,
        "tab": "model",
        "maker": params.get("CarMakerNo") or "",
        "model": params.get("CarModelNo") or "",
        "dmodel": params.get("CarModelDetailNo") or "",
        "grade": params.get("CarGradeNo") or "",
        "dgrade": params.get("CarGradeDetailNo") or "",
        "year-min": params.get("CarYearFrom") or "",
        "year-max": params.get("CarYearTo") or "",
        "usekm-min": params.get("CarMileageFrom") or "",
        "usekm-max": params.get("CarMileageTo") or "",
        "price-min": params.get("CarPriceFrom") or "",
        "price-max": params.get("CarPriceTo") or "",
        "fuel": params.get("CarFuelNo") or "",
        "mission": params.get("CarMissionNo") or "",
        "color": params.get("CarColorNo") or "",
        "carName": params.get("SearchName") or "",
        "carPlateNumber": params.get("SearchCarNo") or "",
    }

    # Sort mapping
    sort_map = {"ModDt": "", "RegDt": "", "CarPrice": "price", "CarYear": "year", "CarMileage": "usekm"}
    qp["order"] = sort_map.get(params.get("PageSort") or "", "")

    # Build query string (skip empty values)
    qs = urlencode({k: v for k, v in qp.items() if v})

    page_path = f"/{page}" if int(page) > 1 else ""
    return f"{base}/search/model/{country}{page_path}?{qs}"


def _evict_oldest(cache: dict[str, dict], max_entries: int) -> None:
    if len(cache) <= max_entries:
        return
    oldest_key = min(cache, key=lambda k: cache[k]["expiry"])
    del cache[oldest_key]


# --- Listing fetch ---


async def _fetch_and_cache_listings(cache_key: str, params: dict) -> dict:
    """Fetch listings from salecars.co.kr, parse, cache, and return."""
    global _last_successful_parse

    if is_rate_limited():
        existing = _listing_cache.get(cache_key)
        if existing and existing["data"].get("listings"):
            existing["expiry"] = time.time() + LISTING_TTL
            print(f"[salecars] Rate-limited, serving stale cache ({cache_key[:8]})")
            return existing["data"]
        remaining = get_rate_limit_retry_after()
        print(f"[salecars] Rate-limited, no cache, cooldown remaining: {remaining}s")
        return {"listings": [], "total": 0, "status": "rate_limited", "retry_after": remaining}

    url = _build_listing_url(params)
    await _throttle_request()
    html = await fetch_page(url)

    if _RATE_LIMIT_MARKER in html:
        _record_rate_limit()
        print("[salecars] Rate-limited (limits_box detected)")

        existing = _listing_cache.get(cache_key)
        if existing and existing["data"].get("listings"):
            existing["expiry"] = time.time() + LISTING_TTL
            print(f"[salecars] Serving stale cached listings ({len(existing['data']['listings'])} cars)")
            return existing["data"]

        remaining = get_rate_limit_retry_after()
        return {"listings": [], "total": 0, "status": "rate_limited", "retry_after": remaining}

    listings = parse_car_listings(html)
    total = parse_total_count(html)

    print(f"[salecars] Listings: {len(listings)}/{total}, HTML length: {len(html)}")

    if len(listings) > 0:
        status = "ok"
        _last_successful_parse = time.time()
        _clear_rate_limit()
    elif len(html) <= 50:
        status = "empty"
        print(f"[salecars] WARNING: Empty response ({len(html)} bytes) for {url}")
    else:
        status = "parse_failure"
        print(f"[salecars] WARNING: Parse failure for {url}, HTML start: {html[:300]!r}")

    result = {"listings": listings, "total": total, "status": status}

    if status == "ok":
        _listing_cache[cache_key] = {"data": result, "expiry": time.time() + LISTING_TTL}
        _evict_oldest(_listing_cache, MAX_LISTING_CACHE_ENTRIES)
        return result

    # Fetch failed — serve stale cache if available, do NOT cache the failure
    existing = _listing_cache.get(cache_key)
    if existing and existing["data"].get("listings"):
        existing["expiry"] = time.time() + LISTING_TTL
        print(f"[salecars] Serving stale cache after {status} ({cache_key[:8]})")
        return existing["data"]

    return result


async def _refresh_listing_cache(cache_key: str, params: dict) -> None:
    _listing_refresh_keys.add(cache_key)
    try:
        await _fetch_and_cache_listings(cache_key, params)
        print(f"[salecars] Background refresh OK ({cache_key[:8]})")
    except Exception as e:
        print(f"[salecars] Background refresh failed ({cache_key[:8]}): {e}")
    finally:
        _listing_refresh_keys.discard(cache_key)


async def listing_refresh_loop() -> None:
    """Proactively refresh the default listing cache."""
    default_params = {
        "PageNow": 1, "PageSize": 24,
        "PageSort": "ModDt", "PageAscDesc": "DESC",
    }
    while True:
        jittered = LISTING_REFRESH_INTERVAL + random.uniform(-5 * 60, 5 * 60)
        await asyncio.sleep(max(0.0, jittered))

        if is_rate_limited():
            print("[salecars] Proactive refresh skipped (rate-limited)")
            continue

        try:
            cache_key = hashlib.md5(
                json.dumps(default_params, sort_keys=True).encode()
            ).hexdigest()

            cached = _listing_cache.get(cache_key)
            if cached:
                age = time.time() - (cached["expiry"] - LISTING_TTL)
                if age < LISTING_REFRESH_AT:
                    continue

            await _fetch_and_cache_listings(cache_key, default_params)
            print("[salecars] Proactive default listing refresh OK")
        except Exception as e:
            print(f"[salecars] Proactive listing refresh failed: {e}")


async def _check_unknown_locations(car_ids: list[str]) -> None:
    """Check locations of unknown cars in background so they appear on next request if Suwon."""
    for car_id in car_ids:
        if car_id in _location_cache:
            continue
        if is_rate_limited():
            return
        try:
            await _check_car_location(car_id)
        except Exception as e:
            print(f"[salecars] Failed to check location for {car_id}: {e}")


def _filter_excluded_listings(data: dict) -> dict:
    """Strict whitelist: only keep cars verified as Suwon."""
    listings = data.get("listings")
    if not listings:
        return data

    verified = []
    unknown_ids = []
    for car in listings:
        car_id = car["id"]
        if car_id in _verified_suwon_ids:
            verified.append(car)
        elif car_id not in _location_cache:
            unknown_ids.append(car_id)
        # else: in _location_cache but not Suwon — drop

    if unknown_ids:
        asyncio.ensure_future(_check_unknown_locations(unknown_ids))

    removed = len(listings) - len(verified)
    if removed > 0:
        print(
            f"[salecars] Strict filter: kept {len(verified)}/{len(listings)} "
            f"({len(unknown_ids)} unknown, {removed - len(unknown_ids)} non-Suwon)"
        )
    return {**data, "listings": verified, "total": len(_verified_suwon_ids)}


async def get_car_listings(params: dict) -> dict:
    cache_key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()

    cached = _listing_cache.get(cache_key)
    if cached:
        age = time.time() - (cached["expiry"] - LISTING_TTL)
        if age < LISTING_TTL:
            if age >= LISTING_REFRESH_AT and cache_key not in _listing_refresh_keys:
                if not is_rate_limited():
                    asyncio.create_task(_refresh_listing_cache(cache_key, params))
            print(f"[salecars] Listing cache hit ({cache_key[:8]})")
            return _filter_excluded_listings(cached["data"])

    if is_rate_limited():
        remaining = get_rate_limit_retry_after()
        return {"listings": [], "total": 0, "status": "rate_limited", "retry_after": remaining}

    async with _listing_lock:
        cached = _listing_cache.get(cache_key)
        if cached and time.time() < cached["expiry"]:
            return _filter_excluded_listings(cached["data"])

        try:
            result = await _fetch_and_cache_listings(cache_key, params)
            return _filter_excluded_listings(result)
        except NetworkError:
            cached = _listing_cache.get(cache_key)
            if cached:
                print(f"[salecars] Serving stale listing cache due to network error ({cache_key[:8]})")
                return _filter_excluded_listings(cached["data"])
            raise


# --- Detail fetch ---


async def _fetch_detail_images(car_id: str) -> list[str]:
    """Fetch car images via AJAX endpoint (returns JSON)."""
    try:
        url = f"{settings.salecars_base_url}/search/imageList"
        text = await post_form(url, {"carNo": car_id})
        data = json.loads(text)
        return [
            img["CarImageFullName"]
            for img in data.get("info", [])
            if img.get("CarImageFullName") and "noimage" not in img["CarImageFullName"]
        ]
    except Exception as e:
        print(f"[salecars] Failed to fetch images for {car_id}: {e}")
        return []


async def _fetch_detail_options(car_id: str) -> list[dict]:
    """Fetch car options via AJAX endpoint (returns HTML with checkboxes)."""
    try:
        url = f"{settings.salecars_base_url}/search/optionList"
        html = await post_form(url, {"carNo": car_id})
        return _parse_options_html(html)
    except Exception as e:
        print(f"[salecars] Failed to fetch options for {car_id}: {e}")
        return []


def _parse_options_html(html: str) -> list[dict]:
    """Parse options HTML from AJAX response.

    Structure: <li><h5>Group</h5><ul><li>checkboxes...</li></ul></li>
    Checked checkboxes have 'checked' attribute; their labels follow immediately.
    """
    from selectolax.lexbor import LexborHTMLParser
    parser = LexborHTMLParser(html)

    # Collect all checked options as a flat list
    items: list[str] = []
    for checkbox in parser.css("input[type='checkbox'][checked]"):
        # Skip text/whitespace nodes to find the <label>
        sibling = checkbox.next
        while sibling and sibling.tag and sibling.tag.startswith("-"):
            sibling = sibling.next
        if sibling and sibling.tag == "label":
            text = sibling.text(strip=True)
            if text:
                items.append(text)

    if items:
        return [{"group": "옵션", "items": items}]
    return []


async def _refresh_detail_cache(car_id: str) -> None:
    _detail_refresh_keys.add(car_id)
    try:
        url = f"{settings.salecars_base_url}/search/detail/{car_id}"
        await _throttle_request()
        html = await fetch_page(url)
        if _RATE_LIMIT_MARKER in html:
            _record_rate_limit()
            return
        result = parse_car_detail(html, car_id)

        # Fetch images and options via AJAX (no throttle needed — different endpoints)
        images, options = await asyncio.gather(
            _fetch_detail_images(car_id),
            _fetch_detail_options(car_id),
        )
        result["images"] = images
        if options:
            result["options"] = options

        location = result.get("location", "")
        if location:
            _update_location_tracking(car_id, location)

        _detail_cache[car_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        _clear_rate_limit()
        print(f"[salecars] Detail background refresh OK ({car_id})")
    except Exception as e:
        print(f"[salecars] Detail background refresh failed ({car_id}): {e}")
    finally:
        _detail_refresh_keys.discard(car_id)


async def get_car_detail(car_id: str) -> dict:
    cached = _detail_cache.get(car_id)
    if cached:
        age = time.time() - (cached["expiry"] - DETAIL_TTL)
        if age < DETAIL_TTL:
            if age >= DETAIL_REFRESH_AT and car_id not in _detail_refresh_keys:
                asyncio.create_task(_refresh_detail_cache(car_id))
            print(f"[salecars] Detail cache hit ({car_id})")
            return cached["data"]

    lock = await _get_detail_lock(car_id)
    async with lock:
        cached = _detail_cache.get(car_id)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        url = f"{settings.salecars_base_url}/search/detail/{car_id}"
        await _throttle_request()
        try:
            html = await fetch_page(url)
        except NetworkError:
            cached = _detail_cache.get(car_id)
            if cached:
                print(f"[salecars] Serving stale detail cache ({car_id})")
                return cached["data"]
            raise

        if _RATE_LIMIT_MARKER in html:
            _record_rate_limit()
            cached = _detail_cache.get(car_id)
            if cached:
                cached["expiry"] = time.time() + DETAIL_TTL
                return cached["data"]
            raise NetworkError("Rate-limited on detail request, no cache available")

        result = parse_car_detail(html, car_id)

        # Fetch images and options via AJAX (parallel, no throttle)
        images, options = await asyncio.gather(
            _fetch_detail_images(car_id),
            _fetch_detail_options(car_id),
        )
        result["images"] = images
        result["blurDataUrl"] = result["blurDataUrl"] if images else None
        if options:
            result["options"] = options

        # Track location for strict Suwon whitelist filter
        location = result.get("location", "")
        if location:
            _update_location_tracking(car_id, location)

        _detail_cache[car_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        _clear_rate_limit()
        return result


# --- Disk persistence for detail cache ---

DETAIL_CACHE_PATH = "/tmp/alexdrive_detail_cache.json"
DETAIL_CACHE_PERSIST_INTERVAL = 5 * 60


def _save_detail_cache_to_disk() -> None:
    now = time.time()
    entries = {k: v for k, v in _detail_cache.items() if v["expiry"] > now}
    if not entries:
        return
    try:
        tmp_path = DETAIL_CACHE_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(entries, f)
        os.replace(tmp_path, DETAIL_CACHE_PATH)
        print(f"[salecars] Saved {len(entries)} detail cache entries to disk")
    except Exception as e:
        print(f"[salecars] Failed to save detail cache to disk: {e}")


def _load_detail_cache_from_disk() -> int:
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
        print(f"[salecars] Loaded {loaded} detail cache entries from disk")
    return loaded


def _save_excluded_ids_to_disk() -> None:
    if not _excluded_car_ids:
        return
    now = time.time()
    # Only save non-expired entries
    active = {k: v for k, v in _excluded_car_ids.items() if now - v < EXCLUSION_TTL}
    try:
        tmp_path = EXCLUSION_SET_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(active, f)
        os.replace(tmp_path, EXCLUSION_SET_PATH)
        print(f"[salecars] Saved {len(active)} excluded car IDs to disk")
    except Exception as e:
        print(f"[salecars] Failed to save excluded IDs to disk: {e}")


def _load_excluded_ids_from_disk() -> int:
    try:
        with open(EXCLUSION_SET_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0
    now = time.time()
    loaded = 0
    # Support both old format (list) and new format (dict with timestamps)
    if isinstance(data, list):
        for car_id in data:
            if car_id not in _excluded_car_ids:
                _excluded_car_ids[car_id] = now
                loaded += 1
    elif isinstance(data, dict):
        for car_id, ts in data.items():
            if now - ts < EXCLUSION_TTL and car_id not in _excluded_car_ids:
                _excluded_car_ids[car_id] = ts
                loaded += 1
    if loaded:
        print(f"[salecars] Loaded {loaded} excluded car IDs from disk")
    return loaded


async def detail_cache_persist_loop() -> None:
    while True:
        await asyncio.sleep(DETAIL_CACHE_PERSIST_INTERVAL)
        _save_detail_cache_to_disk()
        _save_excluded_ids_to_disk()
        _save_location_cache_to_disk()


# --- Location cache persistence ---


def _save_location_cache_to_disk() -> None:
    if not _location_cache:
        return
    now = time.time()
    active = {k: [loc, ts] for k, (loc, ts) in _location_cache.items() if now - ts < EXCLUSION_TTL}
    try:
        tmp_path = LOCATION_CACHE_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(active, f)
        os.replace(tmp_path, LOCATION_CACHE_PATH)
        print(f"[salecars] Saved {len(active)} location cache entries to disk")
    except Exception as e:
        print(f"[salecars] Failed to save location cache to disk: {e}")


def _load_location_cache_from_disk() -> int:
    try:
        with open(LOCATION_CACHE_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0
    now = time.time()
    loaded = 0
    for car_id, entry in data.items():
        if not isinstance(entry, list) or len(entry) != 2:
            continue
        loc, ts = entry[0], entry[1]
        if now - ts < EXCLUSION_TTL and car_id not in _location_cache:
            _location_cache[car_id] = (loc, ts)
            # Rebuild whitelist and exclusion set from loaded locations
            if loc and loc in ALLOWED_LOCATIONS:
                _verified_suwon_ids.add(car_id)
            elif loc and loc not in ALLOWED_LOCATIONS and car_id not in _excluded_car_ids:
                _excluded_car_ids[car_id] = ts
            loaded += 1
    if loaded:
        print(f"[salecars] Loaded {loaded} location cache entries from disk")
    return loaded


# --- Lightweight location checker (for scanner) ---


async def _check_car_location(car_id: str) -> str | None:
    """Fetch detail page HTML only, extract location from tooltip.

    Lightweight: does NOT fetch images/options, does NOT populate _detail_cache.
    Returns location string, or None if fetch failed.
    """
    # Check location cache first
    cached = _location_cache.get(car_id)
    if cached:
        loc, ts = cached
        if time.time() - ts < EXCLUSION_TTL:
            return loc

    if is_rate_limited():
        return None

    url = f"{settings.salecars_base_url}/search/detail/{car_id}"
    await _throttle_request()

    try:
        html = await fetch_page(url)
    except NetworkError:
        return None

    if _RATE_LIMIT_MARKER in html:
        _record_rate_limit()
        return None

    from selectolax.lexbor import LexborHTMLParser
    from app.parsers.detail_parser import _extract_location
    parser = LexborHTMLParser(html)
    location = _extract_location(parser)

    if location:
        _update_location_tracking(car_id, location)
    else:
        _location_cache[car_id] = ("", time.time())

    _clear_rate_limit()
    return location


# --- Background location scanner ---


async def _scan_page_locations(page_num: int) -> int:
    """Scan one listing page: fetch car IDs, check unchecked locations.
    Returns number of cars checked.
    """
    if is_rate_limited():
        remaining = get_rate_limit_retry_after()
        print(f"[scanner] Rate-limited, waiting {remaining}s")
        await asyncio.sleep(remaining)

    params = {
        "PageNow": page_num,
        "PageSize": 24,
        "PageSort": "ModDt",
        "PageAscDesc": "DESC",
    }
    url = _build_listing_url(params)
    await _throttle_request()

    try:
        html = await fetch_page(url)
    except NetworkError as e:
        print(f"[scanner] Failed to fetch page {page_num}: {e}")
        return 0

    if _RATE_LIMIT_MARKER in html:
        _record_rate_limit()
        return 0

    listings = parse_car_listings(html)
    _clear_rate_limit()

    checked = 0
    for car in listings:
        car_id = car.get("id")
        if not car_id:
            continue

        # Skip if already in location cache and not expired
        cached = _location_cache.get(car_id)
        if cached and time.time() - cached[1] < EXCLUSION_TTL:
            continue

        if is_rate_limited():
            remaining = get_rate_limit_retry_after()
            print(f"[scanner] Rate-limited during page {page_num}, waiting {remaining}s")
            await asyncio.sleep(remaining)

        await _check_car_location(car_id)
        checked += 1
        await asyncio.sleep(SCANNER_EXTRA_DELAY)

    return checked


async def location_scanner_loop() -> None:
    """Background loop: systematically scan all listing pages for car locations."""
    await asyncio.sleep(SCANNER_STARTUP_DELAY)
    print("[scanner] Starting background location scanner")

    while True:
        try:
            # Fetch page 1 to get total count
            params = {"PageNow": 1, "PageSize": 24, "PageSort": "ModDt", "PageAscDesc": "DESC"}
            url = _build_listing_url(params)
            await _throttle_request()
            html = await fetch_page(url)

            if _RATE_LIMIT_MARKER in html:
                _record_rate_limit()
                remaining = get_rate_limit_retry_after()
                print(f"[scanner] Rate-limited on start, waiting {remaining}s")
                await asyncio.sleep(remaining)
                continue

            total = parse_total_count(html)
            total_pages = max(1, -(-total // 24))  # ceil division
            print(f"[scanner] Starting full pass: {total} cars across {total_pages} pages")

            total_checked = 0
            total_excluded = 0

            for page in range(1, total_pages + 1):
                if is_rate_limited():
                    remaining = get_rate_limit_retry_after()
                    await asyncio.sleep(remaining)

                checked = await _scan_page_locations(page)
                total_checked += checked

                if page % 10 == 0 or page == total_pages:
                    print(
                        f"[scanner] Page {page}/{total_pages}, "
                        f"checked {total_checked} cars, "
                        f"{len(_excluded_car_ids)} excluded total, "
                        f"{len(_location_cache)} in location cache"
                    )

            print(
                f"[scanner] Full pass complete: checked {total_checked} new cars, "
                f"{len(_verified_suwon_ids)} verified Suwon, "
                f"{len(_excluded_car_ids)} excluded, "
                f"{len(_location_cache)} in location cache"
            )

            # Clean expired entries
            now = time.time()
            expired = [k for k, (_, ts) in _location_cache.items() if now - ts >= EXCLUSION_TTL]
            for k in expired:
                del _location_cache[k]
                _verified_suwon_ids.discard(k)
                _excluded_car_ids.pop(k, None)
            if expired:
                print(f"[scanner] Cleaned {len(expired)} expired location cache entries")

            _save_location_cache_to_disk()
            _save_excluded_ids_to_disk()

        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[scanner] Error during scan: {e}")

        await asyncio.sleep(SCANNER_RESCAN_INTERVAL)


# --- Detail cache warming ---

DETAIL_WARMING_MAX = 24


async def warm_detail_cache_for_listings(listings: list[dict]) -> None:
    if is_rate_limited():
        print("[salecars] Skipping detail cache warming (rate-limited)")
        return

    ids_to_warm = [
        car["id"] for car in listings
        if car.get("id") and car["id"] not in _detail_cache
    ][:DETAIL_WARMING_MAX]

    if not ids_to_warm:
        return

    print(f"[salecars] Warming {len(ids_to_warm)} detail caches...")
    for cid in ids_to_warm:
        if is_rate_limited():
            print("[salecars] Stopping detail warming (rate-limited)")
            break
        try:
            await get_car_detail(cid)
        except Exception:
            pass
