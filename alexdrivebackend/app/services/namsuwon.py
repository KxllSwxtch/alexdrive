import asyncio
import hashlib
import json
import os
import time

from app.config import settings
from app.services.client import NetworkError, fetch_json

# ── Static data ──────────────────────────────────────────────

FUELS = [
    {"value": "gasoline", "label": "Бензин"},
    {"value": "diesel", "label": "Дизель"},
    {"value": "lpg", "label": "Газ (LPG)"},
    {"value": "gasoline_lpg", "label": "Бензин+Газ"},
    {"value": "hybrid", "label": "Гибрид"},
    {"value": "electric", "label": "Электро"},
    {"value": "hydrogen", "label": "Водород"},
    {"value": "plug_in_hybrid", "label": "Плагин-гибрид"},
]

TRANSMISSIONS = [
    {"value": "automatic", "label": "Автомат"},
    {"value": "manual", "label": "Механика"},
    {"value": "cvt", "label": "Вариатор (CVT)"},
    {"value": "semi_auto", "label": "Полуавтомат"},
    {"value": "other", "label": "Другое"},
]

# ── Filter caches (24h TTL) ──────────────────────────────────

_makers_cache: dict | None = None  # {data: [...], expiry: float}
_models_cache: dict[str, dict] = {}  # bm_no -> {data: [...], expiry}
_series_cache: dict[str, dict] = {}  # bo_no -> {data: [...], expiry}
_colors_cache: dict | None = None  # {data: [...], expiry}
_filter_lock = asyncio.Lock()

FILTER_TTL = 24 * 60 * 60  # 24 hours

# Tracks which cho (1=Korean, 2=Foreign) each maker belongs to
_maker_cho_map: dict[str, int] = {}

# ── Listing cache (10min TTL) ────────────────────────────────

_listing_cache: dict[str, dict] = {}
_listing_lock = asyncio.Lock()
LISTING_TTL = 600  # 10 minutes
LISTING_REFRESH_AT = 480  # refresh after 80% of TTL
MAX_LISTING_CACHE_ENTRIES = 200
_listing_refresh_keys: set[str] = set()
LISTING_REFRESH_INTERVAL = 30 * 60  # 30 minutes

# ── Detail cache (10min TTL) ─────────────────────────────────

_detail_cache: dict[str, dict] = {}
_detail_locks: dict[str, asyncio.Lock] = {}
_detail_locks_guard = asyncio.Lock()
DETAIL_TTL = 600
MAX_DETAIL_CACHE_ENTRIES = 1000
DETAIL_REFRESH_AT = 480
_detail_refresh_keys: set[str] = set()

_last_successful_fetch: float = 0.0

# ── Throttling ───────────────────────────────────────────────

_last_request_time: float = 0.0
_throttle_lock = asyncio.Lock()


async def _throttle_request() -> None:
    """Enforce minimum interval between outbound requests."""
    global _last_request_time
    min_interval = settings.min_request_interval
    async with _throttle_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        _last_request_time = time.time()


def get_last_successful_fetch() -> float:
    return _last_successful_fetch


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


def _api_url(path: str) -> str:
    return f"{settings.namsuwon_base_url}{path}"


async def _fetch_makers() -> list[dict]:
    """Fetch and merge makers from cho=1 (Korean) and cho=2 (Foreign)."""
    global _makers_cache, _maker_cho_map

    await _throttle_request()
    korean = await fetch_json(_api_url("/api/proxy/makers"), {"lang": "ru", "cho": "1"})
    await _throttle_request()
    foreign = await fetch_json(_api_url("/api/proxy/makers"), {"lang": "ru", "cho": "2"})

    seen: set[str] = set()
    merged: list[dict] = []

    for maker in korean:
        bm_no = str(maker["bm_no"])
        if bm_no not in seen:
            seen.add(bm_no)
            merged.append(maker)
            _maker_cho_map[bm_no] = 1

    for maker in foreign:
        bm_no = str(maker["bm_no"])
        if bm_no not in seen:
            seen.add(bm_no)
            merged.append(maker)
            _maker_cho_map[bm_no] = 2
        elif bm_no not in _maker_cho_map:
            _maker_cho_map[bm_no] = 2

    merged.sort(key=lambda m: m["bm_name"])
    return merged


async def _fetch_colors() -> list[dict]:
    """Fetch color options."""
    await _throttle_request()
    return await fetch_json(_api_url("/api/proxy/colors"), {"lang": "ru"})


async def get_filter_data() -> dict:
    """Fetch merged makers and colors. Cache 24h."""
    global _makers_cache, _colors_cache

    now = time.time()
    if (_makers_cache and now < _makers_cache["expiry"]
            and _colors_cache and now < _colors_cache["expiry"]):
        return {
            "makers": _makers_cache["data"],
            "colors": _colors_cache["data"],
            "fuels": FUELS,
            "transmissions": TRANSMISSIONS,
        }

    async with _filter_lock:
        now = time.time()
        if (_makers_cache and now < _makers_cache["expiry"]
                and _colors_cache and now < _colors_cache["expiry"]):
            return {
                "makers": _makers_cache["data"],
                "colors": _colors_cache["data"],
                "fuels": FUELS,
                "transmissions": TRANSMISSIONS,
            }

        try:
            print("[namsuwon] Fetching filter data...")
            makers = await _fetch_makers()
            colors = await _fetch_colors()

            _makers_cache = {"data": makers, "expiry": time.time() + FILTER_TTL}
            _colors_cache = {"data": colors, "expiry": time.time() + FILTER_TTL}

            print(f"[namsuwon] Filter data cached ({len(makers)} makers, {len(colors)} colors)")
            return {
                "makers": makers,
                "colors": colors,
                "fuels": FUELS,
                "transmissions": TRANSMISSIONS,
            }
        except NetworkError:
            if _makers_cache and _colors_cache:
                print("[namsuwon] Serving stale filter cache due to network error")
                return {
                    "makers": _makers_cache["data"],
                    "colors": _colors_cache["data"],
                    "fuels": FUELS,
                    "transmissions": TRANSMISSIONS,
                }
            raise


async def get_models(bm_no: str) -> list[dict]:
    """Fetch models for a maker. Cache 24h per bm_no."""
    now = time.time()
    cached = _models_cache.get(bm_no)
    if cached and now < cached["expiry"]:
        return cached["data"]

    cho = _maker_cho_map.get(bm_no, 1)
    await _throttle_request()
    data = await fetch_json(
        _api_url("/api/proxy/models"),
        {"bm_no": bm_no, "lang": "ru", "cho": str(cho)},
    )

    _models_cache[bm_no] = {"data": data, "expiry": time.time() + FILTER_TTL}
    print(f"[namsuwon] Cached {len(data)} models for maker {bm_no}")
    return data


async def get_series(bo_no: str) -> list[dict]:
    """Fetch series+trims for a model. Cache 24h per bo_no."""
    now = time.time()
    cached = _series_cache.get(bo_no)
    if cached and now < cached["expiry"]:
        return cached["data"]

    await _throttle_request()
    data = await fetch_json(
        _api_url("/api/proxy/series"),
        {"bo_no": bo_no, "lang": "ru"},
    )

    _series_cache[bo_no] = {"data": data, "expiry": time.time() + FILTER_TTL}
    print(f"[namsuwon] Cached {len(data)} series for model {bo_no}")
    return data


# ── Listing data ─────────────────────────────────────────────


def _transform_listing(item: dict) -> dict:
    """Map namsuwon listing fields to frontend CarListing shape."""
    price_raw = item.get("price", 0)
    d_price = item.get("d_price_str", "")

    return {
        "encryptedId": str(item.get("no", "")),
        "imageUrl": item.get("main_image_thum") or item.get("main_image", ""),
        "name": item.get("car_name", ""),
        "year": item.get("year_month", str(item.get("year", ""))),
        "mileage": item.get("mileage_str", ""),
        "fuel": "",  # not in listing response
        "transmission": item.get("gearbox", ""),
        "price": f"{d_price} 만원" if d_price else "",
        "priceMl": int(d_price.replace(",", "")) if d_price else 0,
        "dealer": "",
        "phone": "",
    }


async def _fetch_and_cache_listings(cache_key: str, params: dict) -> dict:
    """Fetch listings from namsuwon, transform, cache, and return."""
    global _last_successful_fetch

    # Build query params for the API
    api_params: dict[str, str] = {"lang": "ru"}

    # Page/size
    api_params["page"] = str(params.get("page", 1))
    api_params["page_size"] = str(params.get("page_size", 20))

    # Filter params — pass through as-is
    for key in [
        "bm_no", "bo_no", "bs_no", "bd_no",
        "yearFrom", "yearTo", "mileageFrom", "mileageTo",
        "priceFrom", "priceTo", "fuel", "transmission", "color",
        "keyword", "sort", "order",
        "extFlag1", "extFlag2", "extFlag3", "extFlag4", "extFlag5",
    ]:
        val = params.get(key)
        if val:
            api_params[key] = str(val)

    await _throttle_request()
    data = await fetch_json(_api_url("/api/proxy/cars"), api_params)

    items = data.get("items", []) if isinstance(data, dict) else []
    total = data.get("total", 0) if isinstance(data, dict) else 0

    listings = [_transform_listing(item) for item in items]

    page = int(params.get("page", 1))
    page_size = int(params.get("page_size", 20))
    has_next = (page * page_size) < total

    print(f"[namsuwon] Listings: {len(listings)}, total: {total}")

    if len(listings) > 0:
        status = "ok"
        _last_successful_fetch = time.time()
    else:
        status = "empty"

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
        print(f"[namsuwon] Background refresh OK ({cache_key[:8]})")
    except Exception as e:
        print(f"[namsuwon] Background refresh failed ({cache_key[:8]}): {e}")
    finally:
        _listing_refresh_keys.discard(cache_key)


async def listing_refresh_loop() -> None:
    """Proactively refresh the default listing cache."""
    default_params = {"page": 1, "page_size": 20, "sort": "date", "order": "desc"}
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
                    print(f"[namsuwon] Proactive refresh skipped (age={int(age)}s)")
                    continue

            await _fetch_and_cache_listings(cache_key, default_params)
            print("[namsuwon] Proactive default listing refresh OK")
        except Exception as e:
            print(f"[namsuwon] Proactive listing refresh failed: {e}")


async def get_car_listings(params: dict) -> dict:
    cache_key = hashlib.md5(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()

    cached = _listing_cache.get(cache_key)
    if cached:
        age = time.time() - (cached["expiry"] - LISTING_TTL)
        if age < LISTING_TTL:
            if age >= LISTING_REFRESH_AT and cache_key not in _listing_refresh_keys:
                asyncio.create_task(_refresh_listing_cache(cache_key, params))
            print(f"[namsuwon] Listing cache hit ({cache_key[:8]})")
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
                print(f"[namsuwon] Serving stale listing cache ({cache_key[:8]})")
                return cached["data"]
            raise


# ── Detail data ──────────────────────────────────────────────


def _transform_detail(data: dict) -> dict:
    """Map namsuwon detail to frontend CarDetail shape."""
    photos = data.get("photos", [])
    info = data.get("info", {})
    options_raw = data.get("options", {})
    pricing = data.get("pricing", {})
    specs = data.get("specs", {})
    inspection = data.get("inspection", {})

    # Transform options: {group: "comma,separated,items"} -> [{group, items: [...]}]
    options = []
    for group_name, items_str in options_raw.items():
        if items_str and isinstance(items_str, str):
            # Skip "options not registered" text
            if "не зарегистрированы" in items_str.lower():
                continue
            items = [item.strip() for item in items_str.split(",") if item.strip()]
            if items:
                options.append({"group": group_name, "items": items})

    price_man = data.get("price_man", 0)
    price_str = f"{price_man:,} 만원" if price_man else ""

    return {
        "encryptedId": str(data.get("no", "")),
        "name": data.get("car_name", ""),
        "images": photos,
        "year": info.get("Год", ""),
        "mileage": info.get("Пробег", ""),
        "fuel": info.get("Топливо", ""),
        "transmission": info.get("КПП", ""),
        "price": price_str,
        "priceMl": price_man,
        "color": info.get("Цвет", ""),
        "carNumber": info.get("Гос. номер", ""),
        "options": options,
        "dealer": "",
        "phone": "",
        "description": data.get("description", ""),
        "info": info,
        "pricing": pricing,
        "specs": specs,
        "inspection": inspection,
    }


async def _refresh_detail_cache(car_id: str) -> None:
    _detail_refresh_keys.add(car_id)
    try:
        await _throttle_request()
        data = await fetch_json(
            _api_url(f"/api/proxy/cars/{car_id}"),
            {"lang": "ru"},
        )
        result = _transform_detail(data)
        _detail_cache[car_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        print(f"[namsuwon] Detail background refresh OK ({car_id})")
    except Exception as e:
        print(f"[namsuwon] Detail background refresh failed ({car_id}): {e}")
    finally:
        _detail_refresh_keys.discard(car_id)


async def get_car_detail(car_id: str) -> dict:
    cached = _detail_cache.get(car_id)
    if cached:
        age = time.time() - (cached["expiry"] - DETAIL_TTL)
        if age < DETAIL_TTL:
            if age >= DETAIL_REFRESH_AT and car_id not in _detail_refresh_keys:
                asyncio.create_task(_refresh_detail_cache(car_id))
            print(f"[namsuwon] Detail cache hit ({car_id})")
            return cached["data"]

    lock = await _get_detail_lock(car_id)
    async with lock:
        cached = _detail_cache.get(car_id)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        await _throttle_request()
        try:
            data = await fetch_json(
                _api_url(f"/api/proxy/cars/{car_id}"),
                {"lang": "ru"},
            )
        except NetworkError:
            cached = _detail_cache.get(car_id)
            if cached:
                print(f"[namsuwon] Serving stale detail cache ({car_id})")
                return cached["data"]
            raise

        result = _transform_detail(data)
        _detail_cache[car_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
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
        print(f"[namsuwon] Saved {len(entries)} detail cache entries to disk")
    except Exception as e:
        print(f"[namsuwon] Failed to save detail cache to disk: {e}")


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
        print(f"[namsuwon] Loaded {loaded} detail cache entries from disk")
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

    print(f"[namsuwon] Warming {len(ids_to_warm)} detail caches (sequential)...")
    for eid in ids_to_warm:
        try:
            await get_car_detail(eid)
        except Exception:
            pass
