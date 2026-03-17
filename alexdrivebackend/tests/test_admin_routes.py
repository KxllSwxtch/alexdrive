import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.services import session as session_mod


def _make_app():
    """Create a minimal FastAPI app with just the admin router for testing."""
    from fastapi import FastAPI
    from app.routes.admin import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def app():
    return _make_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestSetSession:
    @pytest.mark.asyncio
    async def test_set_session_success(self, client):
        with patch("app.routes.admin.inject_cookies", new_callable=AsyncMock, return_value=True):
            resp = await client.post(
                "/api/admin/session",
                json={"cookies": "valid-cookie"},
                headers={"X-Admin-Secret": "test-secret"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_set_session_wrong_secret(self, client):
        resp = await client.post(
            "/api/admin/session",
            json={"cookies": "any"},
            headers={"X-Admin-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_set_session_missing_secret(self, client):
        resp = await client.post(
            "/api/admin/session",
            json={"cookies": "any"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_set_session_invalid_cookies(self, client):
        with patch("app.routes.admin.inject_cookies", new_callable=AsyncMock, return_value=False):
            resp = await client.post(
                "/api/admin/session",
                json={"cookies": "bad-cookie"},
                headers={"X-Admin-Secret": "test-secret"},
            )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_set_session_empty_admin_config(self, client, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "admin_secret", "")
        resp = await client.post(
            "/api/admin/session",
            json={"cookies": "any"},
            headers={"X-Admin-Secret": ""},
        )
        assert resp.status_code == 403


class TestGetSessionStatus:
    @pytest.mark.asyncio
    async def test_get_session_status(self, client):
        session_mod._cached_cookies = "test-cookie"
        session_mod._cookie_expiry = time.time() + 1800
        resp = await client.get(
            "/api/admin/session",
            headers={"X-Admin-Secret": "test-secret"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_cookies"] is True
        assert data["ttl_remaining_sec"] > 0

    @pytest.mark.asyncio
    async def test_get_session_wrong_secret(self, client):
        resp = await client.get(
            "/api/admin/session",
            headers={"X-Admin-Secret": "wrong"},
        )
        assert resp.status_code == 403
