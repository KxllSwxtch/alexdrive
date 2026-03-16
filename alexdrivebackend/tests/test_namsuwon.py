import json
import time

import httpx
import pytest
import respx

from app.services import namsuwon as namsuwon_mod
from app.services.namsuwon import (
    get_filter_data,
    get_models,
    get_series,
    get_car_listings,
    get_car_detail,
    _transform_listing,
    _transform_detail,
    _save_detail_cache_to_disk,
    _load_detail_cache_from_disk,
)

# ── Sample API responses ─────────────────────────────────────

KOREAN_MAKERS = [
    {"bm_no": "5", "bm_name": "Hyundai", "bm_logoImage": "https://example.com/hyundai.png"},
    {"bm_no": "2", "bm_name": "KIA", "bm_logoImage": "https://example.com/kia.png"},
]

FOREIGN_MAKERS = [
    {"bm_no": "10", "bm_name": "BMW", "bm_logoImage": "https://example.com/bmw.png"},
    {"bm_no": "20", "bm_name": "Mercedes", "bm_logoImage": "https://example.com/merc.png"},
]

COLORS = [
    {"bc_no": "1", "bc_name": "Black", "bc_rgb1": "#000", "bc_rgb2": "#000"},
    {"bc_no": "2", "bc_name": "White", "bc_rgb1": "#FFF", "bc_rgb2": "#FFF"},
]

MODELS_RESPONSE = [
    {"bo_no": "100", "bo_name": "Sonata", "bo_faceImage": "", "bo_startDate": "2020", "bo_endDate": "2024", "bo_group": "Sonata"},
    {"bo_no": "101", "bo_name": "Tucson", "bo_faceImage": "", "bo_startDate": "2021", "bo_endDate": "2025", "bo_group": "Tucson"},
]

SERIES_RESPONSE = [
    {"bs_no": "200", "bs_name": "2.0 Gasoline", "bd": [{"bd_no": "300", "bd_name": "Modern"}, {"bd_no": "301", "bd_name": "Premium"}]},
]

LISTING_RESPONSE = {
    "total": 100,
    "items": [
        {
            "no": 6612064,
            "car_name": "Kia K5 2.0",
            "main_image": "https://example.com/img.jpg",
            "main_image_thum": "https://example.com/img_thum.jpg",
            "price": 32400000,
            "year": 2024,
            "year_month": "24.05",
            "mileage": 35983,
            "mileage_str": "35,983Km",
            "gearbox": "Автомат",
            "d_price_str": "3,240",
            "dealer_name": "Dealer",
            "dealer_hp": "010-1234-5678",
        },
    ],
}

DETAIL_RESPONSE = {
    "no": 6612064,
    "car_name": "Kia K5 2.0 Noblesse",
    "price_man": 3240,
    "description": "Great car",
    "photos": ["https://example.com/1.jpg", "https://example.com/2.jpg"],
    "info": {
        "Год": "2024",
        "Пробег": "35,983Km",
        "КПП": "Автомат",
        "Топливо": "Гибрид",
        "Цвет": "Белый",
        "Гос. номер": "123가4567",
    },
    "options": {
        "Экстерьер": "LED фары, Складные зеркала",
        "Салон": "Кожаный руль, Подогрев сидений",
    },
    "pricing": {"Цена нового": 36620000, "Цена продажи": 32400000},
    "specs": {"Объём (cc)": 1999, "Мощность (л.с.)": 152},
    "inspection": {},
}


# ── Tests ─────────────────────────────────────────────────────


class TestFilterData:
    @pytest.mark.asyncio
    async def test_fetches_and_merges_makers(self, mock_http_client):
        """get_filter_data fetches cho=1 and cho=2 makers and merges them."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/makers").mock(
            side_effect=[
                httpx.Response(200, json=KOREAN_MAKERS),
                httpx.Response(200, json=FOREIGN_MAKERS),
            ]
        )
        mock_http_client.get("https://test.namsuwon.com/api/proxy/colors").respond(200, json=COLORS)

        result = await get_filter_data()
        assert len(result["makers"]) == 4
        # Sorted alphabetically
        names = [m["bm_name"] for m in result["makers"]]
        assert names == sorted(names)
        assert len(result["colors"]) == 2
        assert len(result["fuels"]) == 8
        assert len(result["transmissions"]) == 5

    @pytest.mark.asyncio
    async def test_caches_filter_data(self, mock_http_client):
        """get_filter_data returns cached data on second call."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/makers").mock(
            side_effect=[
                httpx.Response(200, json=KOREAN_MAKERS),
                httpx.Response(200, json=FOREIGN_MAKERS),
            ]
        )
        mock_http_client.get("https://test.namsuwon.com/api/proxy/colors").respond(200, json=COLORS)

        result1 = await get_filter_data()
        result2 = await get_filter_data()
        assert result1 == result2
        # Only 3 calls total (2 makers + 1 colors), not 6
        assert len(mock_http_client.calls) == 3

    @pytest.mark.asyncio
    async def test_cho_map_populated(self, mock_http_client):
        """After get_filter_data, _maker_cho_map has correct entries."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/makers").mock(
            side_effect=[
                httpx.Response(200, json=KOREAN_MAKERS),
                httpx.Response(200, json=FOREIGN_MAKERS),
            ]
        )
        mock_http_client.get("https://test.namsuwon.com/api/proxy/colors").respond(200, json=COLORS)

        await get_filter_data()
        assert namsuwon_mod._maker_cho_map["5"] == 1  # Hyundai is Korean
        assert namsuwon_mod._maker_cho_map["10"] == 2  # BMW is Foreign


class TestModels:
    @pytest.mark.asyncio
    async def test_fetches_models(self, mock_http_client):
        """get_models fetches and caches models for a maker."""
        namsuwon_mod._maker_cho_map["5"] = 1
        mock_http_client.get("https://test.namsuwon.com/api/proxy/models").respond(200, json=MODELS_RESPONSE)

        result = await get_models("5")
        assert len(result) == 2
        assert result[0]["bo_name"] == "Sonata"

    @pytest.mark.asyncio
    async def test_caches_models(self, mock_http_client):
        """get_models returns cached data on second call."""
        namsuwon_mod._maker_cho_map["5"] = 1
        mock_http_client.get("https://test.namsuwon.com/api/proxy/models").respond(200, json=MODELS_RESPONSE)

        await get_models("5")
        await get_models("5")
        assert len(mock_http_client.calls) == 1


class TestSeries:
    @pytest.mark.asyncio
    async def test_fetches_series(self, mock_http_client):
        """get_series fetches series+trims for a model."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/series").respond(200, json=SERIES_RESPONSE)

        result = await get_series("100")
        assert len(result) == 1
        assert result[0]["bs_name"] == "2.0 Gasoline"
        assert len(result[0]["bd"]) == 2


class TestTransformListing:
    def test_transforms_listing_fields(self):
        """_transform_listing maps namsuwon fields to frontend shape."""
        item = LISTING_RESPONSE["items"][0]
        result = _transform_listing(item)

        assert result["encryptedId"] == "6612064"
        assert result["imageUrl"] == "https://example.com/img_thum.jpg"
        assert result["name"] == "Kia K5 2.0"
        assert result["year"] == "24.05"
        assert result["mileage"] == "35,983Km"
        assert result["transmission"] == "Автомат"
        assert result["price"] == "3,240 만원"
        assert result["priceMl"] == 3240
        assert result["dealer"] == ""


class TestTransformDetail:
    def test_transforms_detail_fields(self):
        """_transform_detail maps namsuwon detail to frontend shape."""
        result = _transform_detail(DETAIL_RESPONSE)

        assert result["encryptedId"] == "6612064"
        assert result["name"] == "Kia K5 2.0 Noblesse"
        assert len(result["images"]) == 2
        assert result["year"] == "2024"
        assert result["mileage"] == "35,983Km"
        assert result["fuel"] == "Гибрид"
        assert result["transmission"] == "Автомат"
        assert result["price"] == "3,240 만원"
        assert result["priceMl"] == 3240
        assert result["color"] == "Белый"
        assert result["carNumber"] == "123가4567"
        assert result["description"] == "Great car"
        assert len(result["options"]) == 2
        assert result["options"][0]["group"] == "Экстерьер"
        assert result["options"][0]["items"] == ["LED фары", "Складные зеркала"]


class TestListings:
    @pytest.mark.asyncio
    async def test_fetches_listings(self, mock_http_client):
        """get_car_listings fetches and transforms listings."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/cars").respond(200, json=LISTING_RESPONSE)

        result = await get_car_listings({"page": 1, "page_size": 20})
        assert result["total"] == 100
        assert len(result["listings"]) == 1
        assert result["listings"][0]["encryptedId"] == "6612064"
        assert result["hasNext"] is True

    @pytest.mark.asyncio
    async def test_caches_listings(self, mock_http_client):
        """get_car_listings returns cached data on second call."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/cars").respond(200, json=LISTING_RESPONSE)

        params = {"page": 1, "page_size": 20}
        await get_car_listings(params)
        await get_car_listings(params)
        assert len(mock_http_client.calls) == 1

    @pytest.mark.asyncio
    async def test_cache_eviction(self, mock_http_client):
        """Listing cache evicts oldest entries when max reached."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/cars").respond(200, json=LISTING_RESPONSE)

        namsuwon_mod.MAX_LISTING_CACHE_ENTRIES = 2
        try:
            await get_car_listings({"page": 1})
            await get_car_listings({"page": 2})
            await get_car_listings({"page": 3})
            assert len(namsuwon_mod._listing_cache) <= 2
        finally:
            namsuwon_mod.MAX_LISTING_CACHE_ENTRIES = 200


class TestDetail:
    @pytest.mark.asyncio
    async def test_fetches_detail(self, mock_http_client):
        """get_car_detail fetches and transforms detail."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/cars/6612064").respond(200, json=DETAIL_RESPONSE)

        result = await get_car_detail("6612064")
        assert result["encryptedId"] == "6612064"
        assert result["name"] == "Kia K5 2.0 Noblesse"
        assert len(result["images"]) == 2

    @pytest.mark.asyncio
    async def test_caches_detail(self, mock_http_client):
        """get_car_detail returns cached data on second call."""
        mock_http_client.get("https://test.namsuwon.com/api/proxy/cars/6612064").respond(200, json=DETAIL_RESPONSE)

        await get_car_detail("6612064")
        await get_car_detail("6612064")
        assert len(mock_http_client.calls) == 1

    @pytest.mark.asyncio
    async def test_serves_stale_on_error(self, mock_http_client):
        """get_car_detail serves stale cache on network error."""
        # First call succeeds
        mock_http_client.get("https://test.namsuwon.com/api/proxy/cars/6612064").mock(
            side_effect=[
                httpx.Response(200, json=DETAIL_RESPONSE),
            ]
        )
        result1 = await get_car_detail("6612064")

        # Expire the cache
        namsuwon_mod._detail_cache["6612064"]["expiry"] = 0

        # Second call fails
        mock_http_client.get("https://test.namsuwon.com/api/proxy/cars/6612064").mock(
            side_effect=httpx.ConnectError("fail")
        )

        result2 = await get_car_detail("6612064")
        assert result2["encryptedId"] == result1["encryptedId"]


class TestDiskPersistence:
    def test_save_and_load(self, tmp_path, monkeypatch):
        """Detail cache can be saved and loaded from disk."""
        cache_path = str(tmp_path / "cache.json")
        monkeypatch.setattr(namsuwon_mod, "DETAIL_CACHE_PATH", cache_path)

        namsuwon_mod._detail_cache["123"] = {
            "data": {"encryptedId": "123", "name": "Test"},
            "expiry": time.time() + 600,
        }

        _save_detail_cache_to_disk()
        namsuwon_mod._detail_cache.clear()

        loaded = _load_detail_cache_from_disk()
        assert loaded == 1
        assert "123" in namsuwon_mod._detail_cache

    def test_skip_expired(self, tmp_path, monkeypatch):
        """Expired entries are not loaded from disk."""
        cache_path = str(tmp_path / "cache.json")
        monkeypatch.setattr(namsuwon_mod, "DETAIL_CACHE_PATH", cache_path)

        namsuwon_mod._detail_cache["expired"] = {
            "data": {"encryptedId": "expired"},
            "expiry": time.time() - 100,
        }

        _save_detail_cache_to_disk()
        namsuwon_mod._detail_cache.clear()

        loaded = _load_detail_cache_from_disk()
        assert loaded == 0
