import asyncio

import httpx
import pytest
import respx

from app.services import scraper as sc_mod
from app.services import client as client_mod
from app.config import settings


@pytest.fixture(autouse=True)
def reset_scraper_globals():
    """Reset all caches and locks in scraper.py."""
    sc_mod._filter_cache = None
    sc_mod._listing_cache = {}
    sc_mod._detail_cache = {}
    sc_mod._listing_refresh_keys = set()
    sc_mod._detail_refresh_keys = set()
    sc_mod._filter_lock = asyncio.Lock()
    sc_mod._listing_lock = asyncio.Lock()
    sc_mod._detail_locks = {}
    sc_mod._detail_locks_guard = asyncio.Lock()
    sc_mod._last_request_time = 0.0
    sc_mod._throttle_lock = asyncio.Lock()
    sc_mod._last_rate_limit_time = 0.0
    sc_mod._rate_limit_count = 0
    sc_mod._last_successful_parse = 0.0
    yield
    sc_mod._filter_cache = None
    sc_mod._listing_cache = {}
    sc_mod._detail_cache = {}
    sc_mod._listing_refresh_keys = set()
    sc_mod._detail_refresh_keys = set()
    sc_mod._detail_locks = {}
    sc_mod._last_request_time = 0.0
    sc_mod._last_rate_limit_time = 0.0
    sc_mod._rate_limit_count = 0
    sc_mod._last_successful_parse = 0.0


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Provide test-safe settings values."""
    monkeypatch.setattr(settings, "source_base_url", "https://test.chasainmotors.com")
    monkeypatch.setattr(settings, "carmanager_base_url", "https://test.carmanager.co.kr")
    monkeypatch.setattr(settings, "admin_secret", "test-secret")


@pytest.fixture
def mock_http_client():
    """Create a real httpx.AsyncClient wrapped by respx for mocking."""
    with respx.mock(assert_all_called=False) as router:
        client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        client_mod.set_http_client(client)
        yield router
