import time
from unittest.mock import AsyncMock, patch

import pytest

from app.services import carmanager as cm_mod
from app.services.carmanager import (
    _build_form_fields,
    _evict_oldest,
    _fetch_and_cache_listings,
    SORT_MAP,
    DEFAULT_SIDO,
    DEFAULT_AREA,
)


# ── _build_form_fields (pure function) ───────────────────────


class TestBuildFormFields:
    def test_defaults(self):
        fields = _build_form_fields({})
        assert fields["cbxSearchSiDo"] == DEFAULT_SIDO
        assert fields["cbxSearchSiDoArea"] == DEFAULT_AREA
        assert fields["hdfDefaultSido"] == DEFAULT_SIDO
        assert fields["hdfDefaultCity"] == DEFAULT_AREA
        assert fields["sbxPageRowCount"] == "20"

    def test_sort_mapping(self):
        for name, code in SORT_MAP.items():
            fields = _build_form_fields({"PageSort": name})
            assert fields["sbxPageSort"] == code

    def test_asc_desc(self):
        asc = _build_form_fields({"PageAscDesc": "ASC"})
        assert asc["sbxPageAscDesc"] == "0"
        assert asc["isAscDesc"] == "0"

        desc = _build_form_fields({"PageAscDesc": "DESC"})
        assert desc["sbxPageAscDesc"] == "1"
        assert desc["isAscDesc"] == "1"


# ── _fetch_and_cache_listings — 0-listings retry ─────────────


class TestFetchAndCacheListings:
    @pytest.mark.asyncio
    async def test_zero_listings_retries(self):
        """0 listings + long HTML + not retried → invalidates session and retries."""
        big_html = "x" * 2000
        call_count = 0

        async def mock_post_form(path, data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return big_html
            return "<html><small>empty</small></html>"

        with patch("app.services.carmanager.post_form", side_effect=mock_post_form), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=0), \
             patch("app.services.carmanager.invalidate_session") as mock_invalidate:
            result = await _fetch_and_cache_listings("key1", {})
            assert mock_invalidate.called
            assert call_count == 2
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_zero_listings_already_retried(self):
        """_retried=True → logs warning, returns empty."""
        big_html = "x" * 2000

        async def mock_post_form(path, data):
            return big_html

        with patch("app.services.carmanager.post_form", side_effect=mock_post_form), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=0):
            result = await _fetch_and_cache_listings("key2", {}, _retried=True)
            assert result["listings"] == []

    @pytest.mark.asyncio
    async def test_zero_listings_short_html(self):
        """HTML <= 1000 → no retry (genuine empty result)."""
        short_html = "x" * 500

        async def mock_post_form(path, data):
            return short_html

        with patch("app.services.carmanager.post_form", side_effect=mock_post_form), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=0), \
             patch("app.services.carmanager.invalidate_session") as mock_invalidate:
            result = await _fetch_and_cache_listings("key3", {})
            assert not mock_invalidate.called
            assert result["listings"] == []

    @pytest.mark.asyncio
    async def test_zero_listings_nonzero_total(self):
        """total > 0 → no retry even with 0 listings (partial page)."""
        big_html = "x" * 2000

        async def mock_post_form(path, data):
            return big_html

        with patch("app.services.carmanager.post_form", side_effect=mock_post_form), \
             patch("app.services.carmanager.parse_car_listings", return_value=[]), \
             patch("app.services.carmanager.parse_total_count", return_value=50), \
             patch("app.services.carmanager.invalidate_session") as mock_invalidate:
            result = await _fetch_and_cache_listings("key4", {})
            assert not mock_invalidate.called


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
