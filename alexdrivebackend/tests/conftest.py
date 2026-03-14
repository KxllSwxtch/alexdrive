import asyncio

import httpx
import pytest
import respx

from app.services import session as session_mod
from app.services import carmanager as cm_mod
from app.config import settings


@pytest.fixture(autouse=True)
def reset_session_globals():
    """Reset all module-level globals in session.py before and after each test."""
    session_mod._cached_cookies = ""
    session_mod._cookie_expiry = 0.0
    session_mod._http_client = None
    session_mod._disk_loaded = False
    session_mod._session_lock = asyncio.Lock()
    yield
    session_mod._cached_cookies = ""
    session_mod._cookie_expiry = 0.0
    session_mod._http_client = None
    session_mod._disk_loaded = False
    session_mod._session_lock = asyncio.Lock()


@pytest.fixture(autouse=True)
def reset_carmanager_globals():
    """Reset all caches and locks in carmanager.py."""
    cm_mod._filter_cache = None
    cm_mod._listing_cache = {}
    cm_mod._detail_cache = {}
    cm_mod._listing_refresh_keys = set()
    cm_mod._detail_refresh_keys = set()
    cm_mod._filter_lock = asyncio.Lock()
    cm_mod._listing_lock = asyncio.Lock()
    cm_mod._detail_locks = {}
    cm_mod._detail_locks_guard = asyncio.Lock()
    cm_mod._last_request_time = 0.0
    cm_mod._throttle_lock = asyncio.Lock()
    cm_mod._last_rate_limit_time = 0.0
    cm_mod._rate_limit_count = 0
    yield
    cm_mod._filter_cache = None
    cm_mod._listing_cache = {}
    cm_mod._detail_cache = {}
    cm_mod._listing_refresh_keys = set()
    cm_mod._detail_refresh_keys = set()
    cm_mod._detail_locks = {}
    cm_mod._last_request_time = 0.0
    cm_mod._last_rate_limit_time = 0.0
    cm_mod._rate_limit_count = 0


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Provide test-safe settings values."""
    monkeypatch.setattr(settings, "carmanager_username", "testuser")
    monkeypatch.setattr(settings, "carmanager_password", "testpass")
    monkeypatch.setattr(settings, "carmanager_base_url", "https://test.carmanager.co.kr")
    monkeypatch.setattr(settings, "admin_secret", "test-secret")


@pytest.fixture
def mock_http_client():
    """Create a real httpx.AsyncClient wrapped by respx for mocking."""
    with respx.mock(assert_all_called=False) as router:
        client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        session_mod.set_http_client(client)
        yield router


@pytest.fixture
def session_file(tmp_path, monkeypatch):
    """Point SESSION_FILE to a temp location so tests don't touch real disk."""
    path = tmp_path / "alexdrive_session.json"
    monkeypatch.setattr(session_mod, "SESSION_FILE", path)
    return path
