import asyncio
import hashlib
import json
import os
import time
from urllib.parse import urlencode

from app.config import settings
from app.parsers.detail_parser import parse_car_detail
from app.parsers.filter_parser import (
    build_filter_hierarchy,
    parse_carcode_js,
    CATEGORIES,
    COLORS,
    FUELS,
    MISSIONS,
)
from app.parsers.listing_parser import parse_car_listings, parse_pagination, estimate_total
from app.services.client import NetworkError, fetch_page

_filter_cache: dict | None = None
_filter_lock = asyncio.Lock()

_listing_cache: dict[str, dict] = {}
_listing_lock = asyncio.Lock()
LISTING_TTL = 600  # 10 minutes
LISTING_REFRESH_AT = 480  # refresh after 80% of TTL (8 minutes)
MAX_LISTING_CACHE_ENTRIES = 200
_listing_refresh_keys: set[str] = set()
LISTING_REFRESH_INTERVAL = 30 * 60  # 30 minutes

_detail_cache: dict[str, dict] = {}
_detail_locks: dict[str, asyncio.Lock] = {}
_detail_locks_guard = asyncio.Lock()
DETAIL_TTL = 600  # 10 minutes
MAX_DETAIL_CACHE_ENTRIES = 1000
DETAIL_REFRESH_AT = 480
_detail_refresh_keys: set[str] = set()

_last_successful_parse: float = 0.0

# --- Global outbound request throttling ---
_last_request_time: float = 0.0
_throttle_lock = asyncio.Lock()
MIN_REQUEST_INTERVAL = 3.0  # seconds between ANY jenya request

FILTER_TTL = 24 * 60 * 60  # 24 hours

# Raw carcode data — cached separately so filter builds per carnation are fast
_carcode_data: list[list] | None = None

# Sort mapping: frontend PageSort → jenya ord_chk
SORT_MAP: dict[str, str] = {
    "ModDt": "6",       # recently registered
    "CarYear": "0",     # later models first
    "CarMileage": "2",  # low mileage first
    "CarPrice": "4",    # low price first
}

# Sort with direction: (PageSort, PageAscDesc) → jenya ord_chk
SORT_MAP_DIRECTED: dict[tuple[str, str], str] = {
    ("CarPrice", "ASC"): "4",   # low → high
    ("CarPrice", "DESC"): "5",  # high → low
    ("CarMileage", "ASC"): "2",   # low → high
    ("CarMileage", "DESC"): "3",  # high → low
    ("CarYear", "ASC"): "1",     # old → new
    ("CarYear", "DESC"): "0",    # new → old
}


async def _throttle_request() -> None:
    """Enforce minimum interval between ALL outbound requests."""
    global _last_request_time
    async with _throttle_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            await asyncio.sleep(MIN_REQUEST_INTERVAL - elapsed)
        _last_request_time = time.time()


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


def _evict_oldest(cache: dict[str, dict], max_entries: int) -> None:
    if len(cache) <= max_entries:
        return
    oldest_key = min(cache, key=lambda k: cache[k]["expiry"])
    del cache[oldest_key]


# ── Filter data ──────────────────────────────────────────────


async def _fetch_filter_data_internal() -> dict:
    """Fetch carcode2_en.js and build filter hierarchy."""
    global _filter_cache, _carcode_data
    print("[jenya] Fetching filter data...")

    await _throttle_request()
    js_content = await fetch_page(settings.jenya_carcode_url)
    carcode = parse_carcode_js(js_content)
    _carcode_data = carcode

    print(f"[jenya] Parsed {len(carcode)} carcode entries")

    # Build default hierarchy for carnation=1 (Korean)
    hierarchy = build_filter_hierarchy(carcode, 1)

    data = {
        **hierarchy,
        "colors": COLORS,
        "fuels": FUELS,
        "missions": MISSIONS,
        "categories": CATEGORIES,
    }

    _filter_cache = {"data": data, "carcode": carcode, "expiry": time.time() + FILTER_TTL}
    print(f"[jenya] Filter data cached ({len(data['makers'])} makers)")
    return data


async def get_filter_data(carnation: int = 1) -> dict:
    global _filter_cache

    if _filter_cache and time.time() < _filter_cache["expiry"]:
        carcode = _filter_cache.get("carcode", _carcode_data)
        if carcode and carnation != 1:
            hierarchy = build_filter_hierarchy(carcode, carnation)
            return {
                **hierarchy,
                "colors": COLORS,
                "fuels": FUELS,
                "missions": MISSIONS,
                "categories": CATEGORIES,
            }
        return _filter_cache["data"]

    async with _filter_lock:
        if _filter_cache and time.time() < _filter_cache["expiry"]:
            carcode = _filter_cache.get("carcode", _carcode_data)
            if carcode and carnation != 1:
                hierarchy = build_filter_hierarchy(carcode, carnation)
                return {
                    **hierarchy,
                    "colors": COLORS,
                    "fuels": FUELS,
                    "missions": MISSIONS,
                    "categories": CATEGORIES,
                }
            return _filter_cache["data"]
        try:
            data = await _fetch_filter_data_internal()
            if carnation != 1 and _carcode_data:
                hierarchy = build_filter_hierarchy(_carcode_data, carnation)
                return {
                    **hierarchy,
                    "colors": COLORS,
                    "fuels": FUELS,
                    "missions": MISSIONS,
                    "categories": CATEGORIES,
                }
            return data
        except NetworkError:
            if _filter_cache:
                print("[jenya] Serving stale filter cache due to network error")
                return _filter_cache["data"]
            raise


# ── Listing data ─────────────────────────────────────────────


def _build_listing_url(params: dict) -> str:
    """Build jenya listing URL from query params."""
    query: dict[str, str] = {"m": "sale", "s": "list"}

    # Carnation (category)
    carnation = params.get("carnation") or "1"
    query["carnation"] = carnation

    # Filter params mapping
    if params.get("CarMakerNo"):
        query["carinfo1"] = params["CarMakerNo"]
    if params.get("CarModelNo"):
        query["carseries"] = params["CarModelNo"]
    if params.get("CarModelDetailNo"):
        query["carinfo2"] = params["CarModelDetailNo"]
    if params.get("CarGradeNo"):
        query["carinfo3"] = params["CarGradeNo"]
    if params.get("CarGradeDetailNo"):
        query["carinfo4"] = params["CarGradeDetailNo"]
    if params.get("CarYearFrom"):
        query["caryear1"] = params["CarYearFrom"]
    if params.get("CarYearTo"):
        query["caryear2"] = params["CarYearTo"]
    if params.get("CarMileageFrom"):
        query["carkm1"] = params["CarMileageFrom"]
    if params.get("CarMileageTo"):
        query["carkm2"] = params["CarMileageTo"]
    if params.get("CarPriceFrom"):
        query["carmoney1"] = params["CarPriceFrom"]
    if params.get("CarPriceTo"):
        query["carmoney2"] = params["CarPriceTo"]
    if params.get("CarFuelNo"):
        query["oil_type"] = params["CarFuelNo"]
    if params.get("CarMissionNo"):
        query["carauto"] = params["CarMissionNo"]
    if params.get("CarColorNo"):
        query["carcolor"] = params["CarColorNo"]
    if params.get("SearchCarNo"):
        query["keyword"] = params["SearchCarNo"]

    # Sort
    sort_key = params.get("PageSort") or "ModDt"
    sort_dir = params.get("PageAscDesc") or "DESC"
    directed = SORT_MAP_DIRECTED.get((sort_key, sort_dir))
    if directed:
        query["ord_chk"] = directed
    else:
        query["ord_chk"] = SORT_MAP.get(sort_key, "6")

    # Pagination
    page = params.get("PageNow") or 1
    if isinstance(page, str):
        page = int(page) if page.isdigit() else 1
    if page > 1:
        query["p"] = str(page)

    return f"{settings.jenya_base_url}/?{urlencode(query)}"


def _build_detail_url(seq: str) -> str:
    return f"{settings.jenya_base_url}/?m=sale&s=detail&seq={seq}"


async def _fetch_and_cache_listings(cache_key: str, params: dict) -> dict:
    """Fetch listings from jenya, parse, cache, and return."""
    global _last_successful_parse

    url = _build_listing_url(params)
    await _throttle_request()
    html = await fetch_page(url)

    listings = parse_car_listings(html)
    pagination = parse_pagination(html)
    total = estimate_total(pagination)
    has_next = pagination["has_next"]

    print(f"[jenya] Listings: {len(listings)}, estimated total: {total}, HTML: {len(html)} bytes")

    if len(listings) > 0:
        status = "ok"
        _last_successful_parse = time.time()
    elif len(html) <= 50:
        status = "empty"
    else:
        status = "parse_failure"

    result = {
        "listings": listings,
        "total": total,
        "status": status,
        "hasNext": has_next,
    }
    _listing_cache[cache_key] = {"data": result, "expiry": time.time() + LISTING_TTL}
    _evict_oldest(_listing_cache, MAX_LISTING_CACHE_ENTRIES)
    return result


async def _refresh_listing_cache(cache_key: str, params: dict) -> None:
    _listing_refresh_keys.add(cache_key)
    try:
        await _fetch_and_cache_listings(cache_key, params)
        print(f"[jenya] Background refresh OK ({cache_key[:8]})")
    except Exception as e:
        print(f"[jenya] Background refresh failed ({cache_key[:8]}): {e}")
    finally:
        _listing_refresh_keys.discard(cache_key)


async def listing_refresh_loop() -> None:
    """Proactively refresh the default listing cache."""
    default_params = {
        "PageNow": 1,
        "PageSort": "ModDt",
        "PageAscDesc": "DESC",
        "carnation": "1",
    }
    while True:
        await asyncio.sleep(LISTING_REFRESH_INTERVAL)
        try:
            cache_key = hashlib.md5(
                json.dumps(default_params, sort_keys=True).encode()
            ).hexdigest()

            cached = _listing_cache.get(cache_key)
            if cached:
                age = time.time() - (cached["expiry"] - LISTING_TTL)
                if age < LISTING_REFRESH_AT:
                    print(f"[jenya] Proactive refresh skipped (age={int(age)}s)")
                    continue

            await _fetch_and_cache_listings(cache_key, default_params)
            print("[jenya] Proactive default listing refresh OK")
        except Exception as e:
            print(f"[jenya] Proactive listing refresh failed: {e}")


async def get_car_listings(params: dict) -> dict:
    cache_key = hashlib.md5(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()

    cached = _listing_cache.get(cache_key)
    if cached:
        age = time.time() - (cached["expiry"] - LISTING_TTL)
        if age < LISTING_TTL:
            if age >= LISTING_REFRESH_AT and cache_key not in _listing_refresh_keys:
                asyncio.create_task(_refresh_listing_cache(cache_key, params))
            print(f"[jenya] Listing cache hit ({cache_key[:8]})")
            return cached["data"]

    async with _listing_lock:
        cached = _listing_cache.get(cache_key)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        try:
            return await _fetch_and_cache_listings(cache_key, params)
        except NetworkError:
            cached = _listing_cache.get(cache_key)
            if cached:
                print(f"[jenya] Serving stale listing cache ({cache_key[:8]})")
                return cached["data"]
            raise


# ── Detail data ──────────────────────────────────────────────


async def _refresh_detail_cache(seq_id: str) -> None:
    _detail_refresh_keys.add(seq_id)
    try:
        url = _build_detail_url(seq_id)
        await _throttle_request()
        html = await fetch_page(url)
        result = parse_car_detail(html, seq_id)
        _detail_cache[seq_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        print(f"[jenya] Detail background refresh OK ({seq_id})")
    except Exception as e:
        print(f"[jenya] Detail background refresh failed ({seq_id}): {e}")
    finally:
        _detail_refresh_keys.discard(seq_id)


async def get_car_detail(seq_id: str) -> dict:
    cached = _detail_cache.get(seq_id)
    if cached:
        age = time.time() - (cached["expiry"] - DETAIL_TTL)
        if age < DETAIL_TTL:
            if age >= DETAIL_REFRESH_AT and seq_id not in _detail_refresh_keys:
                asyncio.create_task(_refresh_detail_cache(seq_id))
            print(f"[jenya] Detail cache hit ({seq_id})")
            return cached["data"]

    lock = await _get_detail_lock(seq_id)
    async with lock:
        cached = _detail_cache.get(seq_id)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        url = _build_detail_url(seq_id)
        await _throttle_request()
        try:
            html = await fetch_page(url)
        except NetworkError:
            cached = _detail_cache.get(seq_id)
            if cached:
                print(f"[jenya] Serving stale detail cache ({seq_id})")
                return cached["data"]
            raise

        result = parse_car_detail(html, seq_id)
        _detail_cache[seq_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        return result


# ── Disk persistence for detail cache ────────────────────────

DETAIL_CACHE_PATH = "/tmp/alexdrive_detail_cache.json"
DETAIL_CACHE_PERSIST_INTERVAL = 5 * 60  # 5 minutes


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
        print(f"[jenya] Saved {len(entries)} detail cache entries to disk")
    except Exception as e:
        print(f"[jenya] Failed to save detail cache to disk: {e}")


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
        print(f"[jenya] Loaded {loaded} detail cache entries from disk")
    return loaded


async def detail_cache_persist_loop() -> None:
    while True:
        await asyncio.sleep(DETAIL_CACHE_PERSIST_INTERVAL)
        _save_detail_cache_to_disk()


# ── Proactive detail cache warming ───────────────────────────

DETAIL_WARMING_MAX = 5


async def warm_detail_cache_for_listings(listings: list[dict]) -> None:
    """Background: warm detail cache for listing IDs not already cached."""
    ids_to_warm = [
        car["encryptedId"] for car in listings
        if car.get("encryptedId") and car["encryptedId"] not in _detail_cache
    ][:DETAIL_WARMING_MAX]

    if not ids_to_warm:
        return

    print(f"[jenya] Warming {len(ids_to_warm)} detail caches (sequential)...")
    for eid in ids_to_warm:
        try:
            await get_car_detail(eid)
        except Exception:
            pass
