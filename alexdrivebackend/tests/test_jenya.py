import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.services import jenya as jenya_mod
from app.services.jenya import (
    _build_listing_url,
    _build_detail_url,
    _evict_oldest,
    _fetch_and_cache_listings,
    _throttle_request,
    get_car_listings,
    get_filter_data,
    get_car_detail,
    warm_detail_cache_for_listings,
    LISTING_TTL,
    MIN_REQUEST_INTERVAL,
    SORT_MAP,
    SORT_MAP_DIRECTED,
)


SAMPLE_JS = 'var carcode = [[1,"Hyundai","i30","New i30","1.6","Luxury","승용","준중형"],[2,"BMW","3 Series","320i","M Sport","","승용","중형"]];'


# ── URL building ──────────────────────────────────────────────


class TestBuildListingUrl:
    def test_default_url(self):
        url = _build_listing_url({})
        assert "m=sale" in url
        assert "s=list" in url
        assert "carnation=1" in url
        assert "ord_chk=6" in url

    def test_with_maker(self):
        url = _build_listing_url({"CarMakerNo": "Hyundai"})
        assert "carinfo1=Hyundai" in url

    def test_with_model(self):
        url = _build_listing_url({"CarModelNo": "Sonata"})
        assert "carseries=Sonata" in url

    def test_with_carnation(self):
        url = _build_listing_url({"carnation": "2"})
        assert "carnation=2" in url

    def test_with_pagination(self):
        url = _build_listing_url({"PageNow": 3})
        assert "p=3" in url

    def test_page_1_omits_p(self):
        url = _build_listing_url({"PageNow": 1})
        assert "p=" not in url

    def test_sort_directed(self):
        url = _build_listing_url({"PageSort": "CarPrice", "PageAscDesc": "DESC"})
        assert "ord_chk=5" in url

    def test_sort_price_asc(self):
        url = _build_listing_url({"PageSort": "CarPrice", "PageAscDesc": "ASC"})
        assert "ord_chk=4" in url

    def test_with_fuel(self):
        url = _build_listing_url({"CarFuelNo": "1"})
        assert "oil_type=1" in url

    def test_with_mission(self):
        url = _build_listing_url({"CarMissionNo": "오토"})
        assert "carauto=" in url

    def test_with_year_range(self):
        url = _build_listing_url({"CarYearFrom": "2020", "CarYearTo": "2024"})
        assert "caryear1=2020" in url
        assert "caryear2=2024" in url

    def test_with_price_range(self):
        url = _build_listing_url({"CarPriceFrom": "500", "CarPriceTo": "2000"})
        assert "carmoney1=500" in url
        assert "carmoney2=2000" in url


class TestBuildDetailUrl:
    def test_detail_url(self):
        url = _build_detail_url("0006687244")
        assert "m=sale" in url
        assert "s=detail" in url
        assert "seq=0006687244" in url


# ── Cache eviction ─────────────────────────────────────────────


class TestCacheEviction:
    def test_evict_oldest(self):
        cache = {}
        for i in range(201):
            cache[f"key_{i}"] = {"data": f"val_{i}", "expiry": time.time() + i}
        _evict_oldest(cache, 200)
        assert len(cache) == 200
        assert "key_0" not in cache

    def test_evict_no_op_under_limit(self):
        cache = {}
        for i in range(50):
            cache[f"key_{i}"] = {"data": f"val_{i}", "expiry": time.time() + i}
        _evict_oldest(cache, 200)
        assert len(cache) == 50


# ── Filter data ──────────────────────────────────────────────


class TestGetFilterData:
    @pytest.mark.asyncio
    async def test_fetches_and_caches_filters(self):
        async def mock_fetch(url):
            return SAMPLE_JS

        with patch("app.services.jenya.fetch_page", side_effect=mock_fetch):
            data = await get_filter_data(carnation=1)
            assert "makers" in data
            assert "colors" in data
            assert "fuels" in data
            assert "missions" in data
            assert "categories" in data
            maker_names = {m["MakerName"] for m in data["makers"]}
            assert "Hyundai" in maker_names

    @pytest.mark.asyncio
    async def test_returns_cached_data(self):
        jenya_mod._filter_cache = {
            "data": {"makers": [], "colors": [], "fuels": [], "missions": [], "categories": []},
            "carcode": [],
            "expiry": time.time() + 3600,
        }
        data = await get_filter_data()
        assert data == jenya_mod._filter_cache["data"]

    @pytest.mark.asyncio
    async def test_different_carnation(self):
        async def mock_fetch(url):
            return SAMPLE_JS

        with patch("app.services.jenya.fetch_page", side_effect=mock_fetch):
            data = await get_filter_data(carnation=2)
            maker_names = {m["MakerName"] for m in data["makers"]}
            assert "BMW" in maker_names
            assert "Hyundai" not in maker_names


# ── Listing fetch ────────────────────────────────────────────


SAMPLE_LISTING_HTML = '''
<html><body>
<ul>
  <li><a href="/?m=sale&s=detail&seq=001"><img src="https://photo5.autosale.co.kr/car.jpg">
    <div class="carmemo"><span class="carinfo">Test Car</span><span>2020/01 | 50,000km | 오토 | 휘발유</span></div>
    <strong>\\5,000,000</strong></a></li>
</ul>
</body></html>
'''


class TestFetchAndCacheListings:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        async def mock_fetch(url):
            return SAMPLE_LISTING_HTML

        with patch("app.services.jenya.fetch_page", side_effect=mock_fetch):
            result = await _fetch_and_cache_listings("key1", {"carnation": "1"})
            assert result["status"] == "ok"
            assert len(result["listings"]) >= 1

    @pytest.mark.asyncio
    async def test_empty_html(self):
        async def mock_fetch(url):
            return ""

        with patch("app.services.jenya.fetch_page", side_effect=mock_fetch):
            result = await _fetch_and_cache_listings("key2", {"carnation": "1"})
            assert result["listings"] == []
            assert result["status"] == "empty"


class TestGetCarListings:
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        jenya_mod._listing_cache["test_key"] = {
            "data": {"listings": [{"encryptedId": "1"}], "total": 1, "status": "ok", "hasNext": False},
            "expiry": time.time() + 300,
        }
        # Patch to ensure we get the right cache key
        with patch("app.services.jenya.hashlib") as mock_hash:
            mock_hash.md5.return_value.hexdigest.return_value = "test_key"
            result = await get_car_listings({"carnation": "1"})
            assert result["status"] == "ok"


# ── Detail fetch ─────────────────────────────────────────────


SAMPLE_DETAIL_HTML = '''
<html><body>
<div class="car_name">Test Car Detail</div>
<div class="car_price">\\5,000,000</div>
<table>
  <tr><th>Год выпуска</th><td>2020</td></tr>
  <tr><th>Пробег</th><td>50,000km</td></tr>
</table>
</body></html>
'''


class TestGetCarDetail:
    @pytest.mark.asyncio
    async def test_fetches_detail(self):
        async def mock_fetch(url):
            return SAMPLE_DETAIL_HTML

        with patch("app.services.jenya.fetch_page", side_effect=mock_fetch):
            result = await get_car_detail("0001234567")
            assert result["encryptedId"] == "0001234567"
            assert result["name"] == "Test Car Detail"

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        jenya_mod._detail_cache["cached_id"] = {
            "data": {"encryptedId": "cached_id", "name": "Cached"},
            "expiry": time.time() + 300,
        }
        result = await get_car_detail("cached_id")
        assert result["name"] == "Cached"


# ── Throttle ─────────────────────────────────────────────────


class TestThrottle:
    @pytest.mark.asyncio
    async def test_throttle_enforces_interval(self):
        jenya_mod._last_request_time = time.time()
        sleep_called_with = []

        async def mock_sleep(duration):
            sleep_called_with.append(duration)

        with patch("app.services.jenya.asyncio.sleep", side_effect=mock_sleep):
            await _throttle_request()
        assert len(sleep_called_with) == 1
        assert sleep_called_with[0] > 0

    @pytest.mark.asyncio
    async def test_throttle_no_delay(self):
        jenya_mod._last_request_time = time.time() - MIN_REQUEST_INTERVAL - 1
        sleep_called = False

        async def mock_sleep(duration):
            nonlocal sleep_called
            sleep_called = True

        with patch("app.services.jenya.asyncio.sleep", side_effect=mock_sleep):
            await _throttle_request()
        assert not sleep_called


# ── Detail warming ───────────────────────────────────────────


class TestWarmDetailCache:
    @pytest.mark.asyncio
    async def test_warms_uncached_ids(self):
        async def mock_fetch(url):
            return SAMPLE_DETAIL_HTML

        with patch("app.services.jenya.fetch_page", side_effect=mock_fetch):
            await warm_detail_cache_for_listings([
                {"encryptedId": "warm1"},
                {"encryptedId": "warm2"},
            ])
            assert "warm1" in jenya_mod._detail_cache
            assert "warm2" in jenya_mod._detail_cache

    @pytest.mark.asyncio
    async def test_skips_cached_ids(self):
        jenya_mod._detail_cache["already"] = {
            "data": {"name": "Cached"},
            "expiry": time.time() + 300,
        }
        call_count = 0
        original_get = get_car_detail

        async def counting_get(seq_id):
            nonlocal call_count
            call_count += 1

        with patch("app.services.jenya.get_car_detail", side_effect=counting_get):
            await warm_detail_cache_for_listings([
                {"encryptedId": "already"},
                {"encryptedId": "new_one"},
            ])
        assert call_count == 1  # only "new_one"


# ── Routes ───────────────────────────────────────────────────


class TestCarsRoute:
    @pytest.mark.asyncio
    async def test_returns_200(self):
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        normal_response = {"listings": [{"id": "1"}], "total": 1, "status": "ok", "hasNext": False}

        with patch("app.routes.cars.get_car_listings", new_callable=AsyncMock, return_value=normal_response), \
             patch("app.routes.cars.warm_detail_cache_for_listings", new_callable=AsyncMock):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/cars")
                assert resp.status_code == 200


class TestFiltersRoute:
    @pytest.mark.asyncio
    async def test_returns_200(self):
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        filter_data = {"makers": [], "colors": [], "fuels": [], "missions": [], "categories": []}

        with patch("app.routes.filters.get_filter_data", new_callable=AsyncMock, return_value=filter_data):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/filters")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_passes_carnation(self):
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        filter_data = {"makers": [], "colors": [], "fuels": [], "missions": [], "categories": []}

        with patch("app.routes.filters.get_filter_data", new_callable=AsyncMock, return_value=filter_data) as mock_fn:
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/api/filters?carnation=2")
                mock_fn.assert_called_with(carnation=2)


class TestHealthRoute:
    @pytest.mark.asyncio
    async def test_returns_ok(self):
        from app.main import app
        from httpx import ASGITransport, AsyncClient

        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
