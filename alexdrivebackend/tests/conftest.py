import asyncio

import httpx
import pytest
import respx

from app.services import session as session_mod
from app.services import namsuwon as namsuwon_mod
from app.config import settings


@pytest.fixture(autouse=True)
def reset_session_globals():
    """Reset HTTP client before and after each test."""
    session_mod._http_client = None
    yield
    session_mod._http_client = None


@pytest.fixture(autouse=True)
def reset_namsuwon_globals():
    """Reset all caches and locks in namsuwon.py."""
    namsuwon_mod._makers_cache = None
    namsuwon_mod._colors_cache = None
    namsuwon_mod._models_cache = {}
    namsuwon_mod._series_cache = {}
    namsuwon_mod._maker_cho_map = {}
    namsuwon_mod._listing_cache = {}
    namsuwon_mod._detail_cache = {}
    namsuwon_mod._listing_refresh_keys = set()
    namsuwon_mod._detail_refresh_keys = set()
    namsuwon_mod._filter_lock = asyncio.Lock()
    namsuwon_mod._listing_lock = asyncio.Lock()
    namsuwon_mod._detail_locks = {}
    namsuwon_mod._detail_locks_guard = asyncio.Lock()
    namsuwon_mod._last_request_time = 0.0
    namsuwon_mod._throttle_lock = asyncio.Lock()
    namsuwon_mod._last_successful_fetch = 0.0
    yield
    namsuwon_mod._makers_cache = None
    namsuwon_mod._colors_cache = None
    namsuwon_mod._models_cache = {}
    namsuwon_mod._series_cache = {}
    namsuwon_mod._maker_cho_map = {}
    namsuwon_mod._listing_cache = {}
    namsuwon_mod._detail_cache = {}
    namsuwon_mod._listing_refresh_keys = set()
    namsuwon_mod._detail_refresh_keys = set()
    namsuwon_mod._detail_locks = {}
    namsuwon_mod._last_request_time = 0.0
    namsuwon_mod._last_successful_fetch = 0.0


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Provide test-safe settings values."""
    monkeypatch.setattr(settings, "namsuwon_base_url", "https://test.namsuwon.com")
    monkeypatch.setattr(settings, "admin_secret", "test-secret")
    monkeypatch.setattr(settings, "min_request_interval", 0.0)


@pytest.fixture
def mock_http_client():
    """Create a real httpx.AsyncClient wrapped by respx for mocking."""
    with respx.mock(assert_all_called=False) as router:
        client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        session_mod.set_http_client(client)
        yield router
