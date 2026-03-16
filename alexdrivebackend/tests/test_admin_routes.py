from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


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


class TestDiagnoseEndpoint:
    @pytest.mark.asyncio
    async def test_diagnose_success(self, client):
        html = '<html><ul><li><a href="/?seq=001">Car</a></li></ul></html>'
        with patch("app.routes.admin.fetch_page", new_callable=AsyncMock, return_value=html):
            resp = await client.get(
                "/api/admin/diagnose",
                headers={"X-Admin-Secret": "test-secret"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "html_length" in data
        assert "diagnosis" in data

    @pytest.mark.asyncio
    async def test_diagnose_wrong_secret(self, client):
        resp = await client.get(
            "/api/admin/diagnose",
            headers={"X-Admin-Secret": "wrong"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_diagnose_missing_secret(self, client):
        resp = await client.get("/api/admin/diagnose")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_diagnose_disabled(self, client, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "admin_secret", "")
        resp = await client.get(
            "/api/admin/diagnose",
            headers={"X-Admin-Secret": ""},
        )
        assert resp.status_code == 403
