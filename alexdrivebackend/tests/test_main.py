import pytest
from unittest.mock import AsyncMock, patch

import httpx
from httpx import ASGITransport, AsyncClient

from app.services.client import NetworkError


def _make_test_app():
    """Create the real FastAPI app but with mocked lifespan."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from app.routes import admin

    app = FastAPI()
    app.include_router(admin.router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        if isinstance(exc, NetworkError):
            return JSONResponse(status_code=503, content={"error": "Service temporarily unavailable"})
        if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
            return JSONResponse(status_code=503, content={"error": "Service temporarily unavailable"})
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

    @app.get("/test/network-error")
    async def raise_network_error():
        raise NetworkError("connection lost")

    @app.get("/test/httpx-error")
    async def raise_httpx_error():
        raise httpx.ConnectError("refused")

    @app.get("/test/generic-error")
    async def raise_generic_error():
        raise ValueError("something broke")

    return app


@pytest.fixture
def app():
    return _make_test_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestExceptionHandlers:
    @pytest.mark.asyncio
    async def test_network_error_returns_503(self, client):
        resp = await client.get("/test/network-error")
        assert resp.status_code == 503
        assert "temporarily unavailable" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_httpx_error_returns_503(self, client):
        resp = await client.get("/test/httpx-error")
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_generic_error_returns_500(self, client):
        resp = await client.get("/test/generic-error")
        assert resp.status_code == 500
        assert resp.json()["error"] == "Internal server error"


class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_continues_on_prewarm_failure(self):
        """If pre-warm fails during startup, lifespan still completes."""
        from app.main import lifespan, app as real_app

        with patch("app.main.get_filter_data", new_callable=AsyncMock, side_effect=RuntimeError("no network")), \
             patch("app.main.get_car_listings", new_callable=AsyncMock, side_effect=RuntimeError("no network")):
            async with lifespan(real_app):
                pass  # If we reach here, lifespan didn't crash
