import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.services import carmanager as cm_mod
from app.services.carmanager import (
    _build_datapart_params,
    _evict_oldest,
    _fetch_and_cache_listings,
    _throttle_listing_request,
    SORT_MAP,
    DEFAULT_SIDO,
    DEFAULT_AREA,
    LISTING_TTL,
    MIN_REQUEST_INTERVAL,
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
    async def test_rate_limited_no_cache_retries_then_returns_rate_limited(self):
        """Rate-limited + no cache → retries twice, then returns rate_limited status."""
        rate_limit_html = '<div class="limits_box">Rate limited</div>'
        call_count = 0

        async def mock_post_json(path, data):
            nonlocal call_count
            call_count += 1
            return rate_limit_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json), \
             patch("app.services.carmanager.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch_and_cache_listings("rl_no_cache", {})
            assert result["status"] == "rate_limited"
            assert result["listings"] == []
            assert call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_rate_limited_succeeds_on_retry(self):
        """Rate-limited on first try, succeeds on retry."""
        rate_limit_html = '<div class="limits_box">Rate limited</div>'
        good_html = "<html>good</html>"
        call_count = 0

        async def mock_post_json(path, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_html
            return good_html

        fake_listing = {"encryptedId": "abc", "name": "Test"}

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json), \
             patch("app.services.carmanager.parse_car_listings", return_value=[fake_listing]), \
             patch("app.services.carmanager.parse_total_count", return_value=1), \
             patch("app.services.carmanager.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch_and_cache_listings("rl_retry_ok", {})
            assert result["status"] == "ok"
            assert len(result["listings"]) == 1
            assert call_count == 2

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
        """Throttle should enforce minimum interval between calls."""
        cm_mod._last_listing_request_time = time.time()  # just called

        sleep_called_with = []
        original_sleep = asyncio.sleep

        async def mock_sleep(duration):
            sleep_called_with.append(duration)
            # Don't actually sleep in tests

        with patch("app.services.carmanager.asyncio.sleep", side_effect=mock_sleep):
            await _throttle_listing_request()

        assert len(sleep_called_with) == 1
        assert sleep_called_with[0] > 0
        assert sleep_called_with[0] <= MIN_REQUEST_INTERVAL

    @pytest.mark.asyncio
    async def test_throttle_no_delay_when_interval_passed(self):
        """Throttle should not delay if enough time has passed."""
        cm_mod._last_listing_request_time = time.time() - MIN_REQUEST_INTERVAL - 1

        sleep_called = False

        async def mock_sleep(duration):
            nonlocal sleep_called
            sleep_called = True

        with patch("app.services.carmanager.asyncio.sleep", side_effect=mock_sleep):
            await _throttle_listing_request()

        assert not sleep_called


class TestWarmDetailCacheSkipsOnRateLimit:
    @pytest.mark.asyncio
    async def test_skips_warming_when_recently_rate_limited(self):
        """warm_detail_cache_for_listings should skip when recently rate-limited."""
        from app.services.carmanager import warm_detail_cache_for_listings

        cm_mod._last_rate_limit_time = time.time()  # just rate-limited

        with patch("app.services.carmanager.get_car_detail", new_callable=AsyncMock) as mock_detail:
            await warm_detail_cache_for_listings([{"encryptedId": "abc"}])
            mock_detail.assert_not_called()


# ── Route: 429 on rate-limited empty response ─────────────────


class TestCarsRoute429:
    @pytest.mark.asyncio
    async def test_returns_429_on_rate_limited(self):
        """GET /api/cars returns 429 when backend is rate-limited with no data."""
        from app.main import app

        rate_limited_response = {"listings": [], "total": 0, "status": "rate_limited"}

        with patch("app.routes.cars.get_car_listings", new_callable=AsyncMock, return_value=rate_limited_response):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/cars")
                assert resp.status_code == 429
                assert resp.headers["retry-after"] == "10"
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
