import asyncio

import httpx
import pytest
import respx

from app.services import session as session_mod
from app.services import jenya as jenya_mod
from app.config import settings


@pytest.fixture(autouse=True)
def reset_session_globals():
    """Reset HTTP client before and after each test."""
    session_mod._http_client = None
    yield
    session_mod._http_client = None


@pytest.fixture(autouse=True)
def reset_jenya_globals():
    """Reset all caches and locks in jenya.py."""
    jenya_mod._filter_cache = None
    jenya_mod._carcode_data = None
    jenya_mod._listing_cache = {}
    jenya_mod._detail_cache = {}
    jenya_mod._listing_refresh_keys = set()
    jenya_mod._detail_refresh_keys = set()
    jenya_mod._filter_lock = asyncio.Lock()
    jenya_mod._listing_lock = asyncio.Lock()
    jenya_mod._detail_locks = {}
    jenya_mod._detail_locks_guard = asyncio.Lock()
    jenya_mod._last_request_time = 0.0
    jenya_mod._throttle_lock = asyncio.Lock()
    yield
    jenya_mod._filter_cache = None
    jenya_mod._carcode_data = None
    jenya_mod._listing_cache = {}
    jenya_mod._detail_cache = {}
    jenya_mod._listing_refresh_keys = set()
    jenya_mod._detail_refresh_keys = set()
    jenya_mod._detail_locks = {}
    jenya_mod._last_request_time = 0.0


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Provide test-safe settings values."""
    monkeypatch.setattr(settings, "jenya_base_url", "https://test.jenya.co.kr")
    monkeypatch.setattr(settings, "jenya_carcode_url", "https://test.jenya.co.kr/as5/script/carcode2_en.js")
    monkeypatch.setattr(settings, "admin_secret", "test-secret")


@pytest.fixture
def mock_http_client():
    """Create a real httpx.AsyncClient wrapped by respx for mocking."""
    with respx.mock(assert_all_called=False) as router:
        client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        session_mod.set_http_client(client)
        yield router
