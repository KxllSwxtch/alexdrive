import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.services import carmanager as cm_mod
from app.services.carmanager import (
    _build_datapart_params,
    _clear_rate_limit,
    _evict_oldest,
    _fetch_and_cache_listings,
    _throttle_request,
    get_car_listings,
    get_rate_limit_retry_after,
    is_rate_limited,
    SORT_MAP,
    DEFAULT_SIDO,
    DEFAULT_AREA,
    LISTING_TTL,
    MIN_REQUEST_INTERVAL,
    MAX_REQUEST_JITTER,
)


# ── _build_datapart_params (pure function) ───────────────────


class TestBuildDatapartParams:
    def test_defaults(self):
        body = _build_datapart_params({})
        para = body["para"]
        assert para["CarSiDoNo"] == DEFAULT_SIDO
        assert para["CarSiDoAreaNo"] == DEFAULT_AREA
        assert para["PageSize"] == "20"
        assert para["PageNow"] == 1
        assert para["CarMode"] == "0"

    def test_sort_mapping(self):
        for name, code in SORT_MAP.items():
            body = _build_datapart_params({"PageSort": name})
            assert body["para"]["PageSort"] == code

    def test_asc_desc(self):
        asc = _build_datapart_params({"PageAscDesc": "ASC"})
        assert asc["para"]["PageAscDesc"] == "0"

        desc = _build_datapart_params({"PageAscDesc": "DESC"})
        assert desc["para"]["PageAscDesc"] == "1"

    def test_search_params_mapping(self):
        body = _build_datapart_params({
            "SearchCarNo": "246욧4517",
            "SearchName": "소나타",
        })
        para = body["para"]
        assert para["CarNumber"] == "246욧4517"
        assert para["CarName"] == "소나타"

    def test_search_params_default_empty(self):
        body = _build_datapart_params({})
        para = body["para"]
        assert para["CarNumber"] == ""
        assert para["CarName"] == ""


# ── _fetch_and_cache_listings — 0-listings retry ─────────────


class TestFetchAndCacheListings:
    @pytest.mark.asyncio
    async def test_zero_listings_retries(self):
        """0 listings + long HTML + not retried → invalidates session and retries."""
        big_html = "x" * 2000
        call_count = 0

        async def mock_post_json(path, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return big_html
            return "<html><small>empty</small></html>"

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=0), \
             patch("app.services.carmanager.invalidate_session") as mock_invalidate:
            result = await _fetch_and_cache_listings("key1", {})
            assert mock_invalidate.called
            assert call_count == 2
            assert result["total"] == 0
            assert result["status"] == "empty"  # retry response is 33 bytes (<50)

    @pytest.mark.asyncio
    async def test_zero_listings_already_retried(self):
        """_retried=True → logs warning, returns empty."""
        big_html = "x" * 2000

        async def mock_post_json(path, data):
            return big_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=0):
            result = await _fetch_and_cache_listings("key2", {}, _retried=True)
            assert result["listings"] == []
            assert result["status"] == "parse_failure"

    @pytest.mark.asyncio
    async def test_zero_listings_short_html(self):
        """HTML <= 50 bytes → no retry (truly empty result), status=empty."""
        short_html = "x" * 30

        async def mock_post_json(path, data):
            return short_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=0), \
             patch("app.services.carmanager.invalidate_session") as mock_invalidate:
            result = await _fetch_and_cache_listings("key3", {})
            assert not mock_invalidate.called
            assert result["listings"] == []
            assert result["status"] == "empty"

    @pytest.mark.asyncio
    async def test_zero_listings_nonzero_total(self):
        """total > 0 → no retry even with 0 listings (partial page)."""
        big_html = "x" * 2000

        async def mock_post_json(path, data):
            return big_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=50), \
             patch("app.services.carmanager.invalidate_session") as mock_invalidate:
            result = await _fetch_and_cache_listings("key4", {})
            assert not mock_invalidate.called

    @pytest.mark.asyncio
    async def test_short_error_response_triggers_retry(self):
        """426-byte error page (>50 bytes, 0 listings) → triggers session invalidation + retry."""
        error_html = "x" * 426
        call_count = 0

        async def mock_post_json(path, data):
            nonlocal call_count
            call_count += 1
            return error_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=0), \
             patch("app.services.carmanager.invalidate_session") as mock_invalidate:
            result = await _fetch_and_cache_listings("key5", {})
            assert mock_invalidate.called
            assert call_count == 2
            assert result["status"] == "parse_failure"

    @pytest.mark.asyncio
    async def test_successful_parse_status_ok(self):
        """Listings found → status='ok'."""
        html = "x" * 5000
        fake_listing = {"encryptedId": "abc", "name": "Test Car"}

        async def mock_post_json(path, data):
            return html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json), \
             patch("app.services.carmanager.parse_car_listings", return_value=[fake_listing]), \
             patch("app.services.carmanager.parse_total_count", return_value=1):
            result = await _fetch_and_cache_listings("key6", {})
            assert result["status"] == "ok"
            assert len(result["listings"]) == 1



# ── Cache eviction ────────────────────────────────────────────


class TestCacheEviction:
    def test_caches_result(self):
        cache = {}
        cache["a"] = {"data": "value_a", "expiry": time.time() + 600}
        assert "a" in cache
        assert cache["a"]["data"] == "value_a"

    def test_evict_oldest(self):
        cache = {}
        for i in range(201):
            cache[f"key_{i}"] = {"data": f"val_{i}", "expiry": time.time() + i}
        assert len(cache) == 201
        _evict_oldest(cache, 200)
        assert len(cache) == 200
        assert "key_0" not in cache  # oldest by expiry

    def test_evict_no_op_under_limit(self):
        cache = {}
        for i in range(50):
            cache[f"key_{i}"] = {"data": f"val_{i}", "expiry": time.time() + i}
        _evict_oldest(cache, 200)
        assert len(cache) == 50


# ── Rate limiting ─────────────────────────────────────────────


class TestRateLimitHandling:
    @pytest.mark.asyncio
    async def test_rate_limited_serves_stale_cache_and_extends_ttl(self):
        """Rate-limited + stale cache → serves cached data and extends TTL."""
        rate_limit_html = '<div class="limits_box">Rate limited</div>'
        old_expiry = time.time() - 10  # expired

        cm_mod._listing_cache["rl_key"] = {
            "data": {"listings": [{"id": "1"}], "total": 1, "status": "ok"},
            "expiry": old_expiry,
        }

        async def mock_post_json(path, data):
            return rate_limit_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json):
            result = await _fetch_and_cache_listings("rl_key", {})
            assert len(result["listings"]) == 1
            # TTL should have been extended
            assert cm_mod._listing_cache["rl_key"]["expiry"] > old_expiry

    @pytest.mark.asyncio
    async def test_rate_limited_no_cache_returns_immediately(self):
        """Rate-limited + no cache → returns rate_limited immediately (no retries)."""
        rate_limit_html = '<div class="limits_box">Rate limited</div>'
        call_count = 0

        async def mock_post_json(path, data):
            nonlocal call_count
            call_count += 1
            return rate_limit_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json):
            result = await _fetch_and_cache_listings("rl_no_cache", {})
            assert result["status"] == "rate_limited"
            assert result["listings"] == []
            assert "retry_after" in result
            assert call_count == 1  # single attempt, no retries

    @pytest.mark.asyncio
    async def test_early_bailout_when_already_rate_limited(self):
        """When is_rate_limited() is true, bail out immediately without hitting carmanager."""
        cm_mod._last_rate_limit_time = time.time()
        cm_mod._rate_limit_count = 1

        with patch("app.services.carmanager.post_json", new_callable=AsyncMock) as mock_post:
            result = await _fetch_and_cache_listings("rl_bailout", {})
            mock_post.assert_not_called()  # should NOT hit carmanager
            assert result["status"] == "rate_limited"
            assert result["listings"] == []
            assert result["retry_after"] > 0

    @pytest.mark.asyncio
    async def test_early_bailout_serves_stale_cache(self):
        """When is_rate_limited() is true + stale cache exists, serve it without network."""
        cm_mod._last_rate_limit_time = time.time()
        cm_mod._rate_limit_count = 1
        old_expiry = time.time() - 10  # expired

        cm_mod._listing_cache["rl_stale"] = {
            "data": {"listings": [{"id": "1"}], "total": 1, "status": "ok"},
            "expiry": old_expiry,
        }

        with patch("app.services.carmanager.post_json", new_callable=AsyncMock) as mock_post:
            result = await _fetch_and_cache_listings("rl_stale", {})
            mock_post.assert_not_called()
            assert len(result["listings"]) == 1
            assert cm_mod._listing_cache["rl_stale"]["expiry"] > old_expiry

    @pytest.mark.asyncio
    async def test_rate_limit_sets_last_rate_limit_time(self):
        """Rate limiting sets _last_rate_limit_time."""
        rate_limit_html = '<div class="limits_box">Rate limited</div>'
        cm_mod._last_rate_limit_time = 0.0

        cm_mod._listing_cache["rl_time"] = {
            "data": {"listings": [{"id": "1"}], "total": 1, "status": "ok"},
            "expiry": time.time() + 100,
        }

        async def mock_post_json(path, data):
            return rate_limit_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json):
            await _fetch_and_cache_listings("rl_time", {})
            assert cm_mod._last_rate_limit_time > 0


class TestThrottle:
    @pytest.mark.asyncio
    async def test_throttle_enforces_minimum_interval(self):
        """Throttle should enforce minimum interval (with jitter) between calls."""
        cm_mod._last_request_time = time.time()  # just called

        sleep_called_with = []

        async def mock_sleep(duration):
            sleep_called_with.append(duration)
            # Don't actually sleep in tests

        with patch("app.services.carmanager.asyncio.sleep", side_effect=mock_sleep):
            await _throttle_request()

        assert len(sleep_called_with) == 1
        assert sleep_called_with[0] > 0
        # With jitter, delay can be up to MIN_REQUEST_INTERVAL + MAX_REQUEST_JITTER
        assert sleep_called_with[0] <= MIN_REQUEST_INTERVAL + MAX_REQUEST_JITTER

    @pytest.mark.asyncio
    async def test_throttle_no_delay_when_interval_passed(self):
        """Throttle should not delay if enough time has passed (beyond max jitter)."""
        cm_mod._last_request_time = time.time() - MIN_REQUEST_INTERVAL - MAX_REQUEST_JITTER - 1

        sleep_called = False

        async def mock_sleep(duration):
            nonlocal sleep_called
            sleep_called = True

        with patch("app.services.carmanager.asyncio.sleep", side_effect=mock_sleep):
            await _throttle_request()

        assert not sleep_called


class TestWarmDetailCacheSkipsOnRateLimit:
    @pytest.mark.asyncio
    async def test_skips_warming_when_recently_rate_limited(self):
        """warm_detail_cache_for_listings should skip when recently rate-limited."""
        from app.services.carmanager import warm_detail_cache_for_listings

        cm_mod._last_rate_limit_time = time.time()  # just rate-limited
        cm_mod._rate_limit_count = 1

        with patch("app.services.carmanager.get_car_detail", new_callable=AsyncMock) as mock_detail:
            await warm_detail_cache_for_listings([{"encryptedId": "abc"}])
            mock_detail.assert_not_called()


class TestScopeAwareRateLimitClearing:
    def test_listing_success_decrements_counter(self):
        """Successful listing request decrements rate-limit counter by 1."""
        cm_mod._rate_limit_count = 3
        _clear_rate_limit("listing")
        assert cm_mod._rate_limit_count == 2

    def test_detail_success_does_not_clear(self):
        """Successful detail request does NOT clear listing rate-limit state."""
        cm_mod._rate_limit_count = 3
        _clear_rate_limit("detail")
        assert cm_mod._rate_limit_count == 3  # unchanged

    def test_counter_does_not_go_negative(self):
        """Counter stays at 0 when already 0."""
        cm_mod._rate_limit_count = 0
        _clear_rate_limit("listing")
        assert cm_mod._rate_limit_count == 0


class TestGetCarListingsRateLimitGuard:
    @pytest.mark.asyncio
    async def test_returns_rate_limited_without_network_call(self):
        """get_car_listings() bails out immediately when rate-limited with no cache."""
        cm_mod._last_rate_limit_time = time.time()
        cm_mod._rate_limit_count = 1

        with patch("app.services.carmanager.post_json", new_callable=AsyncMock) as mock_post:
            result = await get_car_listings({"PageSize": 20})
            mock_post.assert_not_called()
            assert result["status"] == "rate_limited"
            assert result["retry_after"] > 0


class TestGetRateLimitRetryAfter:
    def test_returns_zero_when_not_rate_limited(self):
        cm_mod._last_rate_limit_time = 0.0
        assert get_rate_limit_retry_after() == 0

    def test_returns_remaining_seconds(self):
        cm_mod._rate_limit_count = 1
        cm_mod._last_rate_limit_time = time.time() - 100  # 100s ago
        remaining = get_rate_limit_retry_after()
        # Cooldown for count=1 is 300s, so remaining should be ~200s
        assert 190 <= remaining <= 210

    def test_returns_zero_after_cooldown_expires(self):
        cm_mod._rate_limit_count = 1
        cm_mod._last_rate_limit_time = time.time() - 400  # 400s ago, cooldown is 300s
        assert get_rate_limit_retry_after() == 0


# ── Route: 429 on rate-limited empty response ─────────────────


class TestCarsRoute429:
    @pytest.mark.asyncio
    async def test_returns_429_on_rate_limited(self):
        """GET /api/cars returns 429 when backend is rate-limited with no data."""
        from app.main import app

        rate_limited_response = {"listings": [], "total": 0, "status": "rate_limited", "retry_after": 120}

        with patch("app.routes.cars.get_car_listings", new_callable=AsyncMock, return_value=rate_limited_response):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/cars")
                assert resp.status_code == 429
                assert resp.headers["retry-after"] == "120"
                data = resp.json()
                assert data["status"] == "rate_limited"

    @pytest.mark.asyncio
    async def test_returns_200_on_normal_response(self):
        """GET /api/cars returns 200 with normal listings."""
        from app.main import app

        normal_response = {"listings": [{"id": "1"}], "total": 1, "status": "ok"}

        with patch("app.routes.cars.get_car_listings", new_callable=AsyncMock, return_value=normal_response), \
             patch("app.routes.cars.warm_detail_cache_for_listings", new_callable=AsyncMock):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/cars")
                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "ok"
