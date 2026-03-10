import time

import httpx
import pytest
import respx

from app.services import session as session_mod
from app.services.client import NetworkError, fetch_with_auth, post_form, fetch_page


BASE = "https://test.carmanager.co.kr"


def _set_valid_session():
    """Pre-set a valid session so fetch_with_auth doesn't try to login."""
    session_mod._cached_cookies = "test-session-cookie"
    session_mod._cookie_expiry = time.time() + 3600
    session_mod._disk_loaded = True


class TestFetchWithAuth:
    @pytest.mark.asyncio
    async def test_fetch_success(self, mock_http_client):
        _set_valid_session()
        mock_http_client.get(f"{BASE}/some/path").respond(200, text="OK body")
        status, text = await fetch_with_auth("/some/path")
        assert status == 200
        assert text == "OK body"

    @pytest.mark.asyncio
    async def test_network_retry_succeeds(self, mock_http_client):
        _set_valid_session()
        route = mock_http_client.get(f"{BASE}/retry/path")
        route.side_effect = [
            httpx.ConnectError("fail 1"),
            httpx.ConnectError("fail 2"),
            respx.MockResponse(200, text="recovered"),
        ]
        status, text = await fetch_with_auth("/retry/path")
        assert status == 200
        assert text == "recovered"

    @pytest.mark.asyncio
    async def test_network_retry_exhausted(self, mock_http_client):
        _set_valid_session()
        mock_http_client.get(f"{BASE}/fail/path").mock(
            side_effect=httpx.ConnectError("always fail")
        )
        with pytest.raises(NetworkError, match="Failed after 3 attempts"):
            await fetch_with_auth("/fail/path")

    @pytest.mark.asyncio
    async def test_auth_302_retries(self, mock_http_client):
        _set_valid_session()
        route = mock_http_client.get(f"{BASE}/auth/path")
        route.side_effect = [
            respx.MockResponse(302, headers={"Location": "/User/Login"}),
            respx.MockResponse(200, text="after re-auth"),
        ]
        # Mock login for re-auth
        mock_http_client.post(f"{BASE}/User/Login").respond(
            302, headers={"Set-Cookie": "NewSession=fresh"}
        )
        status, text = await fetch_with_auth("/auth/path")
        assert status == 200
        assert text == "after re-auth"

    @pytest.mark.asyncio
    async def test_auth_401_retries(self, mock_http_client):
        _set_valid_session()
        route = mock_http_client.get(f"{BASE}/unauth/path")
        route.side_effect = [
            respx.MockResponse(401),
            respx.MockResponse(200, text="ok now"),
        ]
        mock_http_client.post(f"{BASE}/User/Login").respond(
            302, headers={"Set-Cookie": "Refreshed=yes"}
        )
        status, text = await fetch_with_auth("/unauth/path")
        assert status == 200
        assert text == "ok now"

    @pytest.mark.asyncio
    async def test_double_auth_failure(self, mock_http_client):
        _set_valid_session()
        mock_http_client.get(f"{BASE}/double/fail").respond(
            302, headers={"Location": "/User/Login"}
        )
        mock_http_client.post(f"{BASE}/User/Login").respond(
            302, headers={"Set-Cookie": "Fresh=yes"}
        )
        with pytest.raises(RuntimeError, match="Authentication failed after retry"):
            await fetch_with_auth("/double/fail")


class TestPostForm:
    @pytest.mark.asyncio
    async def test_post_form_urlencodes(self, mock_http_client):
        _set_valid_session()
        route = mock_http_client.post(f"{BASE}/form/path")
        route.respond(200, text="form ok")
        text = await post_form("/form/path", {"key": "value", "foo": "bar"})
        assert text == "form ok"
        req = route.calls[0].request
        assert b"key=value" in req.content
        assert b"foo=bar" in req.content
        assert req.headers["content-type"] == "application/x-www-form-urlencoded"


class TestFetchPage:
    @pytest.mark.asyncio
    async def test_fetch_page_returns_text(self, mock_http_client):
        _set_valid_session()
        mock_http_client.get(f"{BASE}/page").respond(200, text="<html>page</html>")
        text = await fetch_page("/page")
        assert text == "<html>page</html>"
