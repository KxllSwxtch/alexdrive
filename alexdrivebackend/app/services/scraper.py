import asyncio
import hashlib
import json
import os
import random
import re
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
_listing_locks: dict[str, asyncio.Lock] = {}
_listing_locks_guard = asyncio.Lock()
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

_RATE_LIMIT_MARKER = "limits_box"

# --- Global outbound request throttling ---
MIN_REQUEST_INTERVAL = 2.0  # was 0.3 — too aggressive, caused IP ban
MAX_REQUEST_JITTER = 1.0
BG_EXTRA_DELAY = 1.0  # background requests wait an extra second


class ThrottleManager:
    """Two-priority-level outbound request throttle.

    Maintains a single shared timestamp to enforce minimum intervals
    (total outbound rate unchanged — no increased ban risk).
    Foreground requests (user-facing) preempt background requests.
    """

    def __init__(
        self,
        min_interval: float = MIN_REQUEST_INTERVAL,
        max_jitter: float = MAX_REQUEST_JITTER,
        bg_extra_delay: float = BG_EXTRA_DELAY,
    ):
        self.min_interval = min_interval
        self.max_jitter = max_jitter
        self.bg_extra_delay = bg_extra_delay
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()
        self._fg_waiting: int = 0

    async def foreground(self) -> None:
        """Acquire throttle slot for a user-facing request (high priority)."""
        self._fg_waiting += 1
        try:
            await self._acquire(extra_delay=0.0)
        finally:
            self._fg_waiting -= 1

    async def background(self) -> None:
        """Acquire throttle slot for a background request (low priority).

        Yields if any foreground requests are waiting.
        """
        while self._fg_waiting > 0:
            await asyncio.sleep(0.1)
        await self._acquire(extra_delay=self.bg_extra_delay)

    async def _acquire(self, extra_delay: float) -> None:
        async with self._lock:
            now = time.time()
            interval = self.min_interval + random.uniform(0, self.max_jitter) + extra_delay
            elapsed = now - self._last_request_time
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
            self._last_request_time = time.time()


_throttle = ThrottleManager()


async def _throttle_request() -> None:
    """Legacy wrapper — defaults to foreground priority."""
    await _throttle.foreground()


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

# Fallback filter options — used if AJAX calls fail
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


def _record_rate_limit() -> None:
    global _last_rate_limit_time, _rate_limit_count
    _last_rate_limit_time = time.time()
    _rate_limit_count += 1
    print(f"[scraper] Rate limit #{_rate_limit_count} recorded (cooldown={_get_cooldown()}s)")


def _get_cooldown() -> float:
    if _rate_limit_count <= 0:
        return _RATE_LIMIT_COOLDOWN
    return min(_RATE_LIMIT_COOLDOWN * (2 ** min(_rate_limit_count - 1, 2)), 1200.0)


def _clear_rate_limit() -> None:
    global _rate_limit_count
    if _rate_limit_count > 0:
        _rate_limit_count = max(0, _rate_limit_count - 1)
        print(f"[scraper] Rate limit decremented to {_rate_limit_count}")


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


async def _get_listing_lock(key: str) -> asyncio.Lock:
    async with _listing_locks_guard:
        if key not in _listing_locks:
            _listing_locks[key] = asyncio.Lock()
            if len(_listing_locks) > MAX_LISTING_CACHE_ENTRIES * 2:
                stale = [
                    k for k in _listing_locks
                    if k not in _listing_cache and not _listing_locks[k].locked()
                ]
                for k in stale:
                    del _listing_locks[k]
        return _listing_locks[key]


# --- Filter data ---


def _parse_ajax_filter(
    response_text: str,
    src_id_key: str,
    src_name_key: str,
    dst_id_key: str,
    dst_name_key: str,
) -> list[dict] | None:
    """Parse AJAX filter response from chasainmotors.

    Response format: {"status": 200, "data": [{"FUEL_NO": 101, "FUEL_NAME": "..."}, ...]}
    Maps source keys to destination keys matching our Pydantic models.
    """
    try:
        data = json.loads(response_text)
        items = data.get("data", [])
        if not isinstance(items, list) or not items:
            return None
        return [
            {dst_id_key: item[src_id_key], dst_name_key: item[src_name_key]}
            for item in items
            if src_id_key in item and src_name_key in item
        ]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


async def _fetch_filter_data_internal() -> dict:
    global _filter_cache
    print("[scraper] Fetching filter data...")

    # Fetch public JS files from carmanager in parallel (no auth needed)
    urls = [f"{settings.carmanager_base_url}{path}" for path in CAR_JS_FILES]
    car_js_contents = await asyncio.gather(*[fetch_page(url) for url in urls])

    combined_js = "\n".join(car_js_contents)
    page_filters = parse_filter_data_from_js(combined_js)

    # Fetch dynamic filter options from chasainmotors AJAX APIs
    base = settings.source_base_url
    fuels = None
    missions = None
    colors = None
    try:
        fuel_resp, mission_resp, color_resp = await asyncio.gather(
            post_form(f"{base}/search/getFuelList", {}),
            post_form(f"{base}/search/getMissionList", {}),
            post_form(f"{base}/search/getColorList", {}),
        )
        fuels = _parse_ajax_filter(fuel_resp, "FUEL_NO", "FUEL_NAME", "FKeyNo", "FuelName")
        missions = _parse_ajax_filter(mission_resp, "MISSION_NO", "MISSION_NAME", "MKeyNo", "MissionName")
        colors = _parse_ajax_filter(color_resp, "COLOR_NO", "COLOR_NAME", "CKeyNo", "ColorName")
    except Exception as e:
        print(f"[scraper] AJAX filter fetch failed, using static fallback: {e}")

    data = {
        **page_filters,
        "colors": colors or STATIC_COLORS,
        "fuels": fuels or STATIC_FUELS,
        "missions": missions or STATIC_MISSIONS,
        "danjis": [],
    }

    _filter_cache = {"data": data, "expiry": time.time() + FILTER_TTL}
    print(f"[scraper] Filter data cached ({len(data['makers'])} makers)")
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
                print("[scraper] Serving stale filter cache due to network error")
                return _filter_cache["data"]
            raise


# --- URL construction ---


COUNTRY_MAP = {"1": "kor", "2": "foreign", "3": "freight"}


def _build_listing_url(params: dict) -> str:
    """Build listing URL from query params."""
    base = settings.source_base_url

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
    sort_map = {"ModDt": "regDate", "RegDt": "regDate", "CarPrice": "price", "CarYear": "year", "CarMileage": "useKm"}
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


async def _fetch_and_cache_listings(cache_key: str, params: dict, *, _background: bool = False) -> dict:
    """Fetch listings, parse, cache, and return."""
    global _last_successful_parse

    if is_rate_limited():
        existing = _listing_cache.get(cache_key)
        if existing and existing["data"].get("listings"):
            existing["expiry"] = time.time() + LISTING_TTL
            print(f"[scraper] Rate-limited, serving stale cache ({cache_key[:8]})")
            return existing["data"]
        remaining = get_rate_limit_retry_after()
        print(f"[scraper] Rate-limited, no cache, cooldown remaining: {remaining}s")
        return {"listings": [], "total": 0, "status": "rate_limited", "retry_after": remaining}

    url = _build_listing_url(params)
    if _background:
        await _throttle.background()
    else:
        await _throttle.foreground()
    html = await fetch_page(url)

    if _RATE_LIMIT_MARKER in html:
        _record_rate_limit()
        print("[scraper] Rate-limited (limits_box detected)")

        existing = _listing_cache.get(cache_key)
        if existing and existing["data"].get("listings"):
            existing["expiry"] = time.time() + LISTING_TTL
            print(f"[scraper] Serving stale cached listings ({len(existing['data']['listings'])} cars)")
            return existing["data"]

        remaining = get_rate_limit_retry_after()
        return {"listings": [], "total": 0, "status": "rate_limited", "retry_after": remaining}

    listings = parse_car_listings(html)
    total = parse_total_count(html)

    print(f"[scraper] Listings: {len(listings)}/{total}, HTML length: {len(html)}")

    if len(listings) > 0:
        status = "ok"
        _last_successful_parse = time.time()
        _clear_rate_limit()
    elif len(html) <= 50:
        status = "empty"
        print(f"[scraper] WARNING: Empty response ({len(html)} bytes) for {url}")
    else:
        status = "parse_failure"
        print(f"[scraper] WARNING: Parse failure for {url}, HTML start: {html[:300]!r}")

    result = {"listings": listings, "total": total, "status": status}

    if status == "ok":
        _listing_cache[cache_key] = {"data": result, "expiry": time.time() + LISTING_TTL}
        _evict_oldest(_listing_cache, MAX_LISTING_CACHE_ENTRIES)
        return result

    # Fetch failed — serve stale cache if available, do NOT cache the failure
    existing = _listing_cache.get(cache_key)
    if existing and existing["data"].get("listings"):
        existing["expiry"] = time.time() + LISTING_TTL
        print(f"[scraper] Serving stale cache after {status} ({cache_key[:8]})")
        return existing["data"]

    return result


async def _refresh_listing_cache(cache_key: str, params: dict) -> None:
    _listing_refresh_keys.add(cache_key)
    try:
        await _fetch_and_cache_listings(cache_key, params, _background=True)
        print(f"[scraper] Background refresh OK ({cache_key[:8]})")
    except Exception as e:
        print(f"[scraper] Background refresh failed ({cache_key[:8]}): {e}")
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
            print("[scraper] Proactive refresh skipped (rate-limited)")
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

            await _fetch_and_cache_listings(cache_key, default_params, _background=True)
            print("[scraper] Proactive default listing refresh OK")
        except Exception as e:
            print(f"[scraper] Proactive listing refresh failed: {e}")


async def get_car_listings(params: dict) -> dict:
    """Fetch car listings with caching and rate-limit handling."""
    cache_key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()

    cached = _listing_cache.get(cache_key)
    if cached:
        age = time.time() - (cached["expiry"] - LISTING_TTL)
        if age < LISTING_TTL:
            if age >= LISTING_REFRESH_AT and cache_key not in _listing_refresh_keys:
                if not is_rate_limited():
                    asyncio.create_task(_refresh_listing_cache(cache_key, params))
            print(f"[scraper] Listing cache hit ({cache_key[:8]})")
            return cached["data"]

    if is_rate_limited():
        remaining = get_rate_limit_retry_after()
        return {"listings": [], "total": 0, "status": "rate_limited", "retry_after": remaining}

    lock = await _get_listing_lock(cache_key)
    async with lock:
        cached = _listing_cache.get(cache_key)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        try:
            return await _fetch_and_cache_listings(cache_key, params)
        except NetworkError:
            cached = _listing_cache.get(cache_key)
            if cached:
                print(f"[scraper] Serving stale listing cache due to network error ({cache_key[:8]})")
                return cached["data"]
            raise


# --- Detail fetch ---


async def _fetch_detail_images(car_id: str) -> list[str]:
    """Fetch car images via AJAX endpoint (returns JSON)."""
    try:
        url = f"{settings.source_base_url}/search/imageList"
        text = await post_form(url, {"carNo": car_id})
        data = json.loads(text)
        return [
            img["CarImageFullName"]
            for img in data.get("info", [])
            if img.get("CarImageFullName") and "noimage" not in img["CarImageFullName"]
        ]
    except Exception as e:
        print(f"[scraper] Failed to fetch images for {car_id}: {e}")
        return []


async def _fetch_detail_options(car_id: str) -> list[dict]:
    """Fetch car options via AJAX endpoint (returns HTML with checkboxes)."""
    try:
        url = f"{settings.source_base_url}/search/optionList"
        html = await post_form(url, {"carNo": car_id})
        return _parse_options_html(html)
    except Exception as e:
        print(f"[scraper] Failed to fetch options for {car_id}: {e}")
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
        url = f"{settings.source_base_url}/search/detail/{car_id}"
        await _throttle.background()
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

        _detail_cache[car_id] = {"data": result, "expiry": time.time() + DETAIL_TTL}
        _evict_oldest(_detail_cache, MAX_DETAIL_CACHE_ENTRIES)
        _clear_rate_limit()
        print(f"[scraper] Detail background refresh OK ({car_id})")
    except Exception as e:
        print(f"[scraper] Detail background refresh failed ({car_id}): {e}")
    finally:
        _detail_refresh_keys.discard(car_id)


async def get_car_detail(car_id: str, *, _background: bool = False) -> dict:
    cached = _detail_cache.get(car_id)
    if cached:
        age = time.time() - (cached["expiry"] - DETAIL_TTL)
        if age < DETAIL_TTL:
            if age >= DETAIL_REFRESH_AT and car_id not in _detail_refresh_keys:
                asyncio.create_task(_refresh_detail_cache(car_id))
            print(f"[scraper] Detail cache hit ({car_id})")
            return cached["data"]

    lock = await _get_detail_lock(car_id)
    async with lock:
        cached = _detail_cache.get(car_id)
        if cached and time.time() < cached["expiry"]:
            return cached["data"]

        url = f"{settings.source_base_url}/search/detail/{car_id}"
        if _background:
            await _throttle.background()
        else:
            await _throttle.foreground()
        try:
            html = await fetch_page(url)
        except NetworkError:
            cached = _detail_cache.get(car_id)
            if cached:
                print(f"[scraper] Serving stale detail cache ({car_id})")
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
        print(f"[scraper] Saved {len(entries)} detail cache entries to disk")
    except Exception as e:
        print(f"[scraper] Failed to save detail cache to disk: {e}")


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
        print(f"[scraper] Loaded {loaded} detail cache entries from disk")
    return loaded


async def detail_cache_persist_loop() -> None:
    while True:
        await asyncio.sleep(DETAIL_CACHE_PERSIST_INTERVAL)
        _save_detail_cache_to_disk()


# --- Detail cache warming ---

DETAIL_WARMING_MAX = 8


async def warm_detail_cache_for_listings(listings: list[dict]) -> None:
    if is_rate_limited():
        print("[scraper] Skipping detail cache warming (rate-limited)")
        return

    ids_to_warm = [
        car["id"] for car in listings
        if car.get("id") and car["id"] not in _detail_cache
    ][:DETAIL_WARMING_MAX]

    if not ids_to_warm:
        return

    print(f"[scraper] Warming {len(ids_to_warm)} detail caches...")
    for cid in ids_to_warm:
        if is_rate_limited():
            print("[scraper] Stopping detail warming (rate-limited)")
            break
        # Pause warming when foreground requests are waiting
        if _throttle._fg_waiting > 0:
            print("[scraper] Pausing detail warming (foreground request pending)")
            while _throttle._fg_waiting > 0:
                await asyncio.sleep(0.2)
        try:
            await get_car_detail(cid, _background=True)
        except Exception:
            pass
