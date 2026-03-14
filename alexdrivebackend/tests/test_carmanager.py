import time
from unittest.mock import AsyncMock, patch

import pytest

from app.services import carmanager as cm_mod
from app.services.carmanager import (
    _build_datapart_params,
    _evict_oldest,
    _fetch_and_cache_listings,
    is_rate_limited,
    SORT_MAP,
    DEFAULT_SIDO,
    DEFAULT_AREA,
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

    @pytest.mark.asyncio
    async def test_rate_limited_response(self):
        """Rate-limited HTML → status='rate_limited', no session invalidation, no retry."""
        rate_html = '<div class="limits_box"><p>검색량 초과로 사용이 제한된 상태입니다.</p></div>'

        async def mock_post_json(path, data):
            return rate_html

        with patch("app.services.carmanager.post_json", side_effect=mock_post_json) as mock_post, \
             patch("app.services.carmanager.invalidate_session") as mock_invalidate:
            # Reset cooldown state before test
            cm_mod._rate_limit_until = 0.0
            result = await _fetch_and_cache_listings("key_rl", {})
            assert result["status"] == "rate_limited"
            assert result["listings"] == []
            assert result["total"] == 0
            assert not mock_invalidate.called  # session NOT invalidated
            assert mock_post.call_count == 1  # no retry
            assert is_rate_limited()  # cooldown set
            # Clean up
            cm_mod._rate_limit_until = 0.0


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
