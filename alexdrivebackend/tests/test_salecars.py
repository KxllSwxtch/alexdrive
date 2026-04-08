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

    def test_skips_empty_values(self):
        url = _build_listing_url({"CarMakerNo": "10055"})
        assert "model=" not in url
        assert "dmodel=" not in url
        assert "grade=" not in url
        assert "fuel=" not in url

    def test_encodes_special_chars(self):
        url = _build_listing_url({"SearchName": "소나타"})
        assert "carName=%EC%86%8C%EB%82%98%ED%83%80" in url
        assert "소나타" not in url


# ── Listing parser ───────────────────────────────────────────


class TestListingParser:
    def test_parse_total_count(self):
        html = '<html><body><div>전체 49,659대</div></body></html>'
        assert parse_total_count(html) == 49659

    def test_parse_total_count_nested_spans(self):
        """Real salecars.co.kr HTML wraps the number in a span."""
        html = '<html><body><span>전체 <span class="txt-primary font-bold">30,804</span>대</span></body></html>'
        assert parse_total_count(html) == 30804

    def test_parse_total_count_no_match(self):
        assert parse_total_count("<html><body></body></html>") == 0

    def test_parse_listings_basic(self):
        html = '''
        <ul>
          <li>
            <a href="/search/detail/12345">
              <div class="car-img" style="background:url(https://img.carmanager.co.kr/photo.jpg)"></div>
            </a>
            <div>
              <button><a href="/search/detail/12345">[현대]소나타 2.0</a></button>
              <ul>
                <li>2023-06</li>
                <li>15,000km</li>
                <li>휘발유</li>
                <li>흰색</li>
              </ul>
              <span class="price">
                월 <strong class="representativeColor">
                  <span class="equalRepaymentOfPrincipalAndInterestPrice">30</span>만원
                </strong>
              </span>
              <span class="price"><span class="num">2,500</span>만원</span>
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


class TestExtractLocation:
    def test_suwon(self):
        from app.parsers.detail_parser import _extract_location
        from selectolax.lexbor import LexborHTMLParser
        html = '<html><body><span class="tooltip-box">(주)세일카(수원)</span></body></html>'
        assert _extract_location(LexborHTMLParser(html)) == "수원"

    def test_ansan(self):
        from app.parsers.detail_parser import _extract_location
        from selectolax.lexbor import LexborHTMLParser
        html = '<html><body><span class="tooltip-box">(주)건우(안산)</span></body></html>'
        assert _extract_location(LexborHTMLParser(html)) == "안산"

    def test_empty(self):
        from app.parsers.detail_parser import _extract_location
        from selectolax.lexbor import LexborHTMLParser
        html = '<html><body></body></html>'
        assert _extract_location(LexborHTMLParser(html)) == ""

    def test_detail_parser_uses_location(self):
        """parse_car_detail extracts location from tooltip."""
        html = '''
        <div class="car_name"><p>[현대]소나타</p></div>
        <div class="car_price">판매가 1,000만원</div>
        <table><tr><th>연식</th><td>2020</td></tr></table>
        <table class="type02">
          <tr><th>판매방식</th><td>알선판매<span class="tooltip-box">벧엘2(수원)</span></td></tr>
        </table>
        '''
        result = parse_car_detail(html, "99999")
        assert result["location"] == "수원"


# ── Listing exclusion filter ─────────────────────────────────


class TestFilterExcludedListings:
    def setup_method(self):
        from app.services import salecars
        self._orig_exc = dict(salecars._excluded_car_ids)
        self._orig_ver = set(salecars._verified_suwon_ids)
        self._orig_loc = dict(salecars._location_cache)
        salecars._excluded_car_ids.clear()
        salecars._verified_suwon_ids.clear()
        salecars._location_cache.clear()

    def teardown_method(self):
        from app.services import salecars
        salecars._excluded_car_ids.clear()
        salecars._excluded_car_ids.update(self._orig_exc)
        salecars._verified_suwon_ids.clear()
        salecars._verified_suwon_ids.update(self._orig_ver)
        salecars._location_cache.clear()
        salecars._location_cache.update(self._orig_loc)

    def test_only_verified_suwon_shown(self):
        """Only cars in _verified_suwon_ids pass through the filter."""
        import time
        from app.services.salecars import _filter_excluded_listings, _verified_suwon_ids, _location_cache, _excluded_car_ids
        _verified_suwon_ids.add("car_A")
        _location_cache["car_A"] = ("수원", time.time())
        _excluded_car_ids["car_B"] = time.time()
        _location_cache["car_B"] = ("안산", time.time())
        # car_C is unknown (not in any cache)

        data = {
            "listings": [{"id": "car_A"}, {"id": "car_B"}, {"id": "car_C"}],
            "total": 50,
            "status": "ok",
        }
        result = _filter_excluded_listings(data)
        assert len(result["listings"]) == 1
        assert result["listings"][0]["id"] == "car_A"

    def test_total_reflects_verified_count(self):
        """total should equal len(_verified_suwon_ids)."""
        import time
        from app.services.salecars import _filter_excluded_listings, _verified_suwon_ids, _location_cache
        _verified_suwon_ids.update({"s1", "s2", "s3"})
        _location_cache["s1"] = ("수원", time.time())
        _location_cache["car_A"] = ("수원", time.time())
        _verified_suwon_ids.add("car_A")

        data = {
            "listings": [{"id": "car_A"}],
            "total": 100,
            "status": "ok",
        }
        result = _filter_excluded_listings(data)
        assert result["total"] == 4  # s1, s2, s3, car_A

    def test_empty_listings_passes_through(self):
        from app.services.salecars import _filter_excluded_listings
        data = {"listings": [], "total": 0, "status": "ok"}
        result = _filter_excluded_listings(data)
        assert result["listings"] == []

    def test_all_unknown_returns_empty(self):
        """Cars with unknown location should be filtered out."""
        from app.services.salecars import _filter_excluded_listings
        data = {
            "listings": [{"id": "x"}, {"id": "y"}],
            "total": 10,
            "status": "ok",
        }
        result = _filter_excluded_listings(data)
        assert len(result["listings"]) == 0


# ── Location cache ───────────────────────────────────────────


class TestLocationCache:
    def setup_method(self):
        from app.services import salecars
        self._orig_loc = dict(salecars._location_cache)
        self._orig_exc = dict(salecars._excluded_car_ids)
        self._orig_ver = set(salecars._verified_suwon_ids)
        salecars._location_cache.clear()
        salecars._excluded_car_ids.clear()
        salecars._verified_suwon_ids.clear()

    def teardown_method(self):
        from app.services import salecars
        salecars._location_cache.clear()
        salecars._location_cache.update(self._orig_loc)
        salecars._excluded_car_ids.clear()
        salecars._excluded_car_ids.update(self._orig_exc)
        salecars._verified_suwon_ids.clear()
        salecars._verified_suwon_ids.update(self._orig_ver)

    def test_check_car_location_caches_result(self):
        """_check_car_location stores result in _location_cache."""
        import time as t
        from app.services.salecars import _location_cache
        # Simulate a cached entry
        _location_cache["test123"] = ("수원", t.time())
        from app.services.salecars import _check_car_location
        import asyncio
        loc = asyncio.get_event_loop().run_until_complete(_check_car_location("test123"))
        assert loc == "수원"

    def test_location_cache_persistence_roundtrip(self):
        """Save and load location cache preserves data and rebuilds whitelist."""
        import time as t
        import tempfile, os
        from app.services import salecars
        orig_path = salecars.LOCATION_CACHE_PATH
        try:
            # Use temp file
            fd, tmp = tempfile.mkstemp(suffix=".json")
            os.close(fd)
            salecars.LOCATION_CACHE_PATH = tmp

            salecars._location_cache["car1"] = ("수원", t.time())
            salecars._location_cache["car2"] = ("안산", t.time())
            salecars._save_location_cache_to_disk()

            salecars._location_cache.clear()
            salecars._excluded_car_ids.clear()
            salecars._verified_suwon_ids.clear()
            loaded = salecars._load_location_cache_from_disk()
            assert loaded == 2
            assert salecars._location_cache["car1"][0] == "수원"
            assert salecars._location_cache["car2"][0] == "안산"
            # Non-suwon car should be in exclusion set
            assert "car2" in salecars._excluded_car_ids
            assert "car1" not in salecars._excluded_car_ids
            # Suwon car should be in verified set
            assert "car1" in salecars._verified_suwon_ids
            assert "car2" not in salecars._verified_suwon_ids
        finally:
            salecars.LOCATION_CACHE_PATH = orig_path
            if os.path.exists(tmp):
                os.unlink(tmp)


# ── Location tracking helper ─────────────────────────────────


class TestUpdateLocationTracking:
    def setup_method(self):
        from app.services import salecars
        self._orig_loc = dict(salecars._location_cache)
        self._orig_exc = dict(salecars._excluded_car_ids)
        self._orig_ver = set(salecars._verified_suwon_ids)
        salecars._location_cache.clear()
        salecars._excluded_car_ids.clear()
        salecars._verified_suwon_ids.clear()

    def teardown_method(self):
        from app.services import salecars
        salecars._location_cache.clear()
        salecars._location_cache.update(self._orig_loc)
        salecars._excluded_car_ids.clear()
        salecars._excluded_car_ids.update(self._orig_exc)
        salecars._verified_suwon_ids.clear()
        salecars._verified_suwon_ids.update(self._orig_ver)

    def test_suwon_adds_to_verified(self):
        from app.services.salecars import _update_location_tracking, _verified_suwon_ids, _excluded_car_ids, _location_cache
        _update_location_tracking("car1", "수원")
        assert "car1" in _verified_suwon_ids
        assert "car1" not in _excluded_car_ids
        assert _location_cache["car1"][0] == "수원"

    def test_non_suwon_adds_to_excluded(self):
        from app.services.salecars import _update_location_tracking, _verified_suwon_ids, _excluded_car_ids, _location_cache
        _update_location_tracking("car2", "안산")
        assert "car2" not in _verified_suwon_ids
        assert "car2" in _excluded_car_ids
        assert _location_cache["car2"][0] == "안산"

    def test_location_change_updates_sets(self):
        """If a car's location changes, it moves between sets."""
        from app.services.salecars import _update_location_tracking, _verified_suwon_ids, _excluded_car_ids
        _update_location_tracking("car1", "수원")
        assert "car1" in _verified_suwon_ids
        _update_location_tracking("car1", "안산")
        assert "car1" not in _verified_suwon_ids
        assert "car1" in _excluded_car_ids


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

    @pytest.mark.asyncio
    async def test_returns_503_on_empty_status(self):
        from app.main import app

        empty_response = {"listings": [], "total": 0, "status": "empty"}

        with patch("app.routes.cars.get_car_listings", new_callable=AsyncMock, return_value=empty_response):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/cars")
                assert resp.status_code == 503
                assert resp.headers["retry-after"] == "30"
                assert resp.headers["cache-control"] == "no-cache"

    @pytest.mark.asyncio
    async def test_returns_503_on_parse_failure(self):
        from app.main import app

        failure_response = {"listings": [], "total": 0, "status": "parse_failure"}

        with patch("app.routes.cars.get_car_listings", new_callable=AsyncMock, return_value=failure_response):
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/cars")
                assert resp.status_code == 503


# ── Cache poisoning prevention ──────────────────────────────


class TestCachePoisoning:
    def setup_method(self):
        self._orig_cache = dict(sc_mod._listing_cache)
        sc_mod._listing_cache.clear()

    def teardown_method(self):
        sc_mod._listing_cache.clear()
        sc_mod._listing_cache.update(self._orig_cache)

    @pytest.mark.asyncio
    async def test_empty_response_not_cached(self):
        """Failed fetches (status=empty) should NOT be stored in the cache."""
        with patch("app.services.salecars.fetch_page", new_callable=AsyncMock, return_value=""), \
             patch("app.services.salecars._throttle_request", new_callable=AsyncMock), \
             patch("app.services.salecars.is_rate_limited", return_value=False):
            result = await _fetch_and_cache_listings("test_empty", {"PageSize": 24})
            assert result["status"] == "empty"
            assert "test_empty" not in sc_mod._listing_cache

    @pytest.mark.asyncio
    async def test_ok_response_is_cached(self):
        """Successful fetches (status=ok) should be stored in the cache."""
        html = '''<ul><li>
            <a href="/search/detail/12345">
              <div class="car-img" style="background:url(https://img.carmanager.co.kr/photo.jpg)"></div>
            </a>
            <div>
              <button><a href="/search/detail/12345">[현대]소나타</a></button>
              <ul><li>2023</li><li>10,000km</li><li>휘발유</li><li>흰색</li></ul>
              <span class="price"><span class="num">2,000</span>만원</span>
            </div>
          </li></ul>
          <div>전체 1대</div>'''

        with patch("app.services.salecars.fetch_page", new_callable=AsyncMock, return_value=html), \
             patch("app.services.salecars._throttle_request", new_callable=AsyncMock), \
             patch("app.services.salecars.is_rate_limited", return_value=False):
            result = await _fetch_and_cache_listings("test_ok", {"PageSize": 24})
            assert result["status"] == "ok"
            assert "test_ok" in sc_mod._listing_cache

    @pytest.mark.asyncio
    async def test_stale_cache_served_on_failure(self):
        """When a fetch fails but stale cache exists, serve the stale data."""
        # Pre-populate cache with stale data
        sc_mod._listing_cache["test_stale"] = {
            "data": {"listings": [{"id": "1"}], "total": 1, "status": "ok"},
            "expiry": time.time() - 100,  # expired
        }

        with patch("app.services.salecars.fetch_page", new_callable=AsyncMock, return_value=""), \
             patch("app.services.salecars._throttle_request", new_callable=AsyncMock), \
             patch("app.services.salecars.is_rate_limited", return_value=False):
            result = await _fetch_and_cache_listings("test_stale", {"PageSize": 24})
            assert result["status"] == "ok"  # stale data served
            assert len(result["listings"]) == 1
