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


class TestTransportFailover:
    """Regression tests for the 2026-08 outage.

    Production runs against a PLAIN-HTTP origin, which httpcore forward-proxies rather
    than tunnelling via CONNECT -- so `httpx.ProxyError` is structurally unreachable
    there. A hung or unreachable proxy instead surfaces as ReadTimeout / ConnectError /
    PoolTimeout. Those used to be retried 3x against the same dead proxy and never fail
    over (PoolTimeout escaped fetch_page entirely), which took the site down for 6 days
    while every existing failover test -- all of which use https:// -- kept passing.
    """

    @pytest.mark.asyncio
    async def test_hanging_proxy_over_plain_http_falls_back_to_direct(self, mock_http_client):
        direct_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        set_direct_client(direct_client)
        try:
            route = mock_http_client.get("http://www.chasainmotors.com/hang")
            route.side_effect = [
                httpx.ReadTimeout("proxy accepted then hung"),
                respx.MockResponse(200, text="direct content"),
            ]
            text = await fetch_page("http://www.chasainmotors.com/hang")
            assert text == "direct content"
            # Proves the DIRECT client served this, not a lucky proxy retry.
            assert client_mod._proxy_failure_logged is True
        finally:
            set_direct_client(None)
            await direct_client.aclose()

    @pytest.mark.asyncio
    async def test_pool_timeout_falls_back_to_direct(self, mock_http_client):
        """PoolTimeout previously escaped fetch_page with no retry and no failover."""
        direct_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        set_direct_client(direct_client)
        try:
            route = mock_http_client.get("http://www.chasainmotors.com/pool")
            route.side_effect = [
                httpx.PoolTimeout("connection pool exhausted"),
                respx.MockResponse(200, text="direct content"),
            ]
            text = await fetch_page("http://www.chasainmotors.com/pool")
            assert text == "direct content"
            assert client_mod._proxy_failure_logged is True
        finally:
            set_direct_client(None)
            await direct_client.aclose()

    @pytest.mark.asyncio
    async def test_pool_timeout_without_direct_client_raises_network_error(self, mock_http_client):
        """Must surface as NetworkError so scraper.py's stale-cache rescues can catch it."""
        set_direct_client(None)
        mock_http_client.get("http://www.chasainmotors.com/pool2").mock(
            side_effect=httpx.PoolTimeout("exhausted")
        )
        with pytest.raises(NetworkError):
            await fetch_page("http://www.chasainmotors.com/pool2")

    @pytest.mark.asyncio
    async def test_connect_error_does_not_retry_dead_proxy_when_direct_available(self, mock_http_client):
        """One proxy attempt, then straight to direct -- not 3x the full timeout."""
        direct_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        set_direct_client(direct_client)
        try:
            route = mock_http_client.get("http://www.chasainmotors.com/dead")
            route.side_effect = [
                httpx.ConnectError("proxy unreachable"),
                respx.MockResponse(200, text="direct content"),
            ]
            text = await fetch_page("http://www.chasainmotors.com/dead")
            assert text == "direct content"
            assert client_mod._proxy_failure_logged is True
            assert route.call_count == 2  # proxy once, direct once -- not 3 proxy retries
        finally:
            set_direct_client(None)
            await direct_client.aclose()

    @pytest.mark.asyncio
    async def test_post_form_hanging_proxy_falls_back_to_direct(self, mock_http_client):
        direct_client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        set_direct_client(direct_client)
        try:
            route = mock_http_client.post("http://www.chasainmotors.com/search/imageList")
            route.side_effect = [
                httpx.ReadTimeout("proxy hung"),
                respx.MockResponse(200, text='{"info": []}'),
            ]
            text = await post_form("http://www.chasainmotors.com/search/imageList", {"carNo": "1"})
            assert text == '{"info": []}'
            assert client_mod._proxy_failure_logged is True
        finally:
            set_direct_client(None)
            await direct_client.aclose()
