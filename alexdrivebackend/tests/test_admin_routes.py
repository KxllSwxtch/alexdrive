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
        mock_data = {
            "total": 100,
            "items": [
                {"no": 123, "car_name": "Test Car", "price": 10000000},
                {"no": 456, "car_name": "Test Car 2", "price": 20000000},
            ],
        }
        with patch("app.routes.admin.fetch_json", new_callable=AsyncMock, return_value=mock_data):
            resp = await client.get(
                "/api/admin/diagnose",
                headers={"X-Admin-Secret": "test-secret"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_cars"] == 100
        assert data["sample_count"] == 2
        assert data["status"] == "ok"

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
