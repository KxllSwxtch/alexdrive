import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.services import salecars as sc_mod
from app.services.salecars import (
    _build_listing_url,
    _evict_oldest,
    _fetch_and_cache_listings,
    _throttle_request,
    _clear_rate_limit,
    get_car_listings,
    get_rate_limit_retry_after,
    is_rate_limited,
    LISTING_TTL,
    MIN_REQUEST_INTERVAL,
    MAX_REQUEST_JITTER,
)
from app.parsers.listing_parser import parse_car_listings, parse_total_count
from app.parsers.detail_parser import parse_car_detail


# ── URL construction ─────────────────────────────────────────


class TestBuildListingUrl:
    def test_defaults(self):
        url = _build_listing_url({})
        assert "/search/model/all?" in url
        assert "country=all" in url
        assert "ascending=desc" in url

    def test_korean_category(self):
        url = _build_listing_url({"carnation": "1"})
        assert "/search/model/kor?" in url
        assert "country=kor" in url

    def test_foreign_category(self):
        url = _build_listing_url({"carnation": "2"})
        assert "/search/model/foreign?" in url

    def test_freight_category(self):
        url = _build_listing_url({"carnation": "3"})
        assert "/search/model/freight?" in url

    def test_pagination(self):
        url = _build_listing_url({"PageNow": 5})
        assert "/5?" in url

    def test_page_1_no_path_suffix(self):
        url = _build_listing_url({"PageNow": 1})
        assert "/1?" not in url

    def test_maker_param(self):
        url = _build_listing_url({"CarMakerNo": "10055"})
        assert "maker=10055" in url

    def test_price_range(self):
        url = _build_listing_url({"CarPriceFrom": "500", "CarPriceTo": "3000"})
        assert "price-min=500" in url
        assert "price-max=3000" in url

    def test_ascending(self):
        url = _build_listing_url({"PageAscDesc": "ASC"})
        assert "ascending=asc" in url


# ── Listing parser ───────────────────────────────────────────


class TestListingParser:
    def test_parse_total_count(self):
        html = '<div>전체 49,659대</div>'
        assert parse_total_count(html) == 49659

    def test_parse_total_count_no_match(self):
        assert parse_total_count("<html></html>") == 0

    def test_parse_listings_basic(self):
        html = '''
        <ul>
          <li>
            <a href="/search/detail/12345">
              <img src="https://img.carmanager.co.kr/photo.jpg" />
            </a>
            <div>
              <button><a href="/search/detail/12345">[현대]소나타 2.0</a></button>
              <ul>
                <li>2023-06</li>
                <li>15,000km</li>
                <li>휘발유</li>
                <li>흰색</li>
              </ul>
              <div>월 <strong>30만원</strong></div>
              <div>2,500만원</div>
            </div>
          </li>
        </ul>
        '''
        listings = parse_car_listings(html)
        assert len(listings) == 1
        assert listings[0]["id"] == "12345"
        assert listings[0]["name"] == "[현대]소나타 2.0"
        assert listings[0]["year"] == "2023-06"
        assert listings[0]["mileage"] == "15,000km"
        assert listings[0]["fuel"] == "휘발유"
        assert listings[0]["price"] == "2,500만원"

    def test_parse_empty_html(self):
        assert parse_car_listings("<html></html>") == []


# ── Detail parser ────────────────────────────────────────────


class TestDetailParser:
    def test_parse_basic_detail(self):
        html = '''
        <div class="car_name"><p>[폭스바겐]티구안 2.0 TDI</p></div>
        <div class="car_price">판매가 1,800만원</div>
        <table>
          <tr><th>연식</th><td>2018</td><th>최초등록일</th><td>2018.06.18</td></tr>
          <tr><th>연료</th><td>경유</td><th>변속기</th><td>오토</td></tr>
          <tr><th>색상</th><td>흰색</td><th>주행거리</th><td>82,170km</td></tr>
          <tr><th>차량번호</th><td>14고7168</td><th>차대번호</th><td>WVGZZZ5N</td></tr>
        </table>
        <table class="type02"><tr><th>이름</th><td>엄만호</td></tr></table>
        <div class="slick-slide"><img src="https://img.carmanager.co.kr/photo1.jpg" /></div>
        <div class="slick-slide"><img src="https://img.carmanager.co.kr/photo2.jpg" /></div>
        '''
        result = parse_car_detail(html, "12345")
        assert result["id"] == "12345"
        assert result["name"] == "[폭스바겐]티구안 2.0 TDI"
        assert result["price"] == "1,800만원"
        assert result["year"] == "2018"
        assert result["fuel"] == "경유"
        assert result["transmission"] == "오토"
        assert result["color"] == "흰색"
        assert result["mileage"] == "82,170km"
        assert result["carNumber"] == "14고7168"
        assert result["registrationDate"] == "2018.06.18"
        assert len(result["images"]) == 2
        assert result["dealer"] == ""  # suppressed
        assert result["phone"] == ""   # suppressed


# ── Cache eviction ────────────────────────────────────────────


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


# ── Rate limiting ─────────────────────────────────────────────


class TestRateLimitHandling:
    @pytest.mark.asyncio
    async def test_rate_limited_serves_stale_cache(self):
        sc_mod._last_rate_limit_time = time.time()
        sc_mod._rate_limit_count = 1

        sc_mod._listing_cache["rl_key"] = {
            "data": {"listings": [{"id": "1"}], "total": 1, "status": "ok"},
            "expiry": time.time() - 10,
        }

        with patch("app.services.salecars.fetch_page", new_callable=AsyncMock) as mock_fetch:
            result = await _fetch_and_cache_listings("rl_key", {})
            mock_fetch.assert_not_called()
            assert len(result["listings"]) == 1

    @pytest.mark.asyncio
    async def test_rate_limited_no_cache_returns_immediately(self):
        sc_mod._last_rate_limit_time = time.time()
        sc_mod._rate_limit_count = 1

        with patch("app.services.salecars.fetch_page", new_callable=AsyncMock) as mock_fetch:
            result = await _fetch_and_cache_listings("rl_no_cache", {})
            mock_fetch.assert_not_called()
            assert result["status"] == "rate_limited"
            assert "retry_after" in result

    @pytest.mark.asyncio
    async def test_get_car_listings_bails_when_rate_limited(self):
        sc_mod._last_rate_limit_time = time.time()
        sc_mod._rate_limit_count = 1

        with patch("app.services.salecars.fetch_page", new_callable=AsyncMock) as mock_fetch:
            result = await get_car_listings({"PageSize": 24})
            mock_fetch.assert_not_called()
            assert result["status"] == "rate_limited"


class TestScopeAwareClearing:
    def test_clear_decrements(self):
        sc_mod._rate_limit_count = 3
        _clear_rate_limit()
        assert sc_mod._rate_limit_count == 2

    def test_counter_stays_at_zero(self):
        sc_mod._rate_limit_count = 0
        _clear_rate_limit()
        assert sc_mod._rate_limit_count == 0


class TestGetRateLimitRetryAfter:
    def test_returns_zero_when_not_rate_limited(self):
        sc_mod._last_rate_limit_time = 0.0
        assert get_rate_limit_retry_after() == 0

    def test_returns_remaining_seconds(self):
        sc_mod._rate_limit_count = 1
        sc_mod._last_rate_limit_time = time.time() - 100
        remaining = get_rate_limit_retry_after()
        assert 190 <= remaining <= 210


class TestThrottle:
    @pytest.mark.asyncio
    async def test_throttle_enforces_minimum_interval(self):
        sc_mod._last_request_time = time.time()
        sleep_called_with = []

        async def mock_sleep(duration):
            sleep_called_with.append(duration)

        with patch("app.services.salecars.asyncio.sleep", side_effect=mock_sleep):
            await _throttle_request()

        assert len(sleep_called_with) == 1
        assert sleep_called_with[0] > 0
        assert sleep_called_with[0] <= MIN_REQUEST_INTERVAL + MAX_REQUEST_JITTER


# ── Route: 429 on rate-limited ───────────────────────────────


class TestCarsRoute429:
    @pytest.mark.asyncio
    async def test_returns_429_on_rate_limited(self):
        from app.main import app

        rate_limited_response = {"listings": [], "total": 0, "status": "rate_limited", "retry_after": 120}

        with patch("app.routes.cars.get_car_listings", new_callable=AsyncMock, return_value=rate_limited_response):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/cars")
                assert resp.status_code == 429
                assert resp.headers["retry-after"] == "120"

    @pytest.mark.asyncio
    async def test_returns_200_on_normal_response(self):
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
