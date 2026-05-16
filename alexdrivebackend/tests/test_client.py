import httpx
import pytest
import respx

from app.services import client as client_mod
from app.services.client import NetworkError, fetch_page, post_form, set_direct_client, set_http_client


class TestFetchPage:
    @pytest.mark.asyncio
    async def test_fetch_success(self, mock_http_client):
        mock_http_client.get("https://www.chasainmotors.com/page").respond(200, text="<html>OK</html>")
        text = await fetch_page("https://www.chasainmotors.com/page")
        assert text == "<html>OK</html>"

    @pytest.mark.asyncio
    async def test_network_retry_succeeds(self, mock_http_client):
        route = mock_http_client.get("https://www.chasainmotors.com/retry")
        route.side_effect = [
            httpx.ConnectError("fail 1"),
            httpx.ConnectError("fail 2"),
            respx.MockResponse(200, text="recovered"),
        ]
        text = await fetch_page("https://www.chasainmotors.com/retry")
        assert text == "recovered"

    @pytest.mark.asyncio
    async def test_network_retry_exhausted(self, mock_http_client):
        mock_http_client.get("https://www.chasainmotors.com/fail").mock(
            side_effect=httpx.ConnectError("always fail")
        )
        with pytest.raises(NetworkError, match="Failed after 3 attempts"):
            await fetch_page("https://www.chasainmotors.com/fail")


class TestProxyFailover:
    """When the primary client (via proxy) fails, fall back to direct client.

    respx patches httpx globally so both the primary and direct clients hit the same
    router. We differentiate calls by call sequence: first call = primary, second = direct.
    """

    @pytest.mark.asyncio
    async def test_proxy_612_falls_back_to_direct(self, mock_http_client):
        direct_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        set_direct_client(direct_client)
        try:
            route = mock_http_client.get("https://www.chasainmotors.com/p")
            route.side_effect = [
                respx.MockResponse(612, text="auth fail"),
                respx.MockResponse(200, text="real content"),
            ]
            text = await fetch_page("https://www.chasainmotors.com/p")
            assert text == "real content"
        finally:
            set_direct_client(None)
            await direct_client.aclose()

    @pytest.mark.asyncio
    async def test_proxy_error_exception_falls_back(self, mock_http_client):
        direct_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        set_direct_client(direct_client)
        try:
            route = mock_http_client.get("https://www.chasainmotors.com/perr")
            route.side_effect = [
                httpx.ProxyError("612 OK"),
                respx.MockResponse(200, text="recovered via direct"),
            ]
            text = await fetch_page("https://www.chasainmotors.com/perr")
            assert text == "recovered via direct"
        finally:
            set_direct_client(None)
            await direct_client.aclose()

    @pytest.mark.asyncio
    async def test_no_direct_client_raises_on_proxy_error(self, mock_http_client):
        set_direct_client(None)
        mock_http_client.get("https://www.chasainmotors.com/noFb").mock(
            side_effect=httpx.ProxyError("612 OK")
        )
        with pytest.raises(NetworkError):
            await fetch_page("https://www.chasainmotors.com/noFb")

    @pytest.mark.asyncio
    async def test_post_form_proxy_failover(self, mock_http_client):
        direct_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        set_direct_client(direct_client)
        try:
            route = mock_http_client.post("https://www.chasainmotors.com/api")
            route.side_effect = [
                respx.MockResponse(612, text="auth fail"),
                respx.MockResponse(200, text='{"ok":true}'),
            ]
            text = await post_form("https://www.chasainmotors.com/api", {"k": "v"})
            assert text == '{"ok":true}'
        finally:
            set_direct_client(None)
            await direct_client.aclose()

    @pytest.mark.asyncio
    async def test_destination_5xx_does_not_use_direct_client(self, mock_http_client):
        # A real 5xx from the origin is not a proxy issue. The primary client retries 3x
        # against the SAME route, never invoking the direct fallback.
        direct_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        set_direct_client(direct_client)
        try:
            route = mock_http_client.get("https://www.chasainmotors.com/origin500")
            route.respond(503, text="origin overloaded")
            text = await fetch_page("https://www.chasainmotors.com/origin500")
            # All 3 calls go to the primary route; the direct client is never reached.
            assert route.call_count == 3
            assert "origin overloaded" in text
        finally:
            set_direct_client(None)
            await direct_client.aclose()
