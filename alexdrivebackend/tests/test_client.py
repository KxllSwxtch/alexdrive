import httpx
import pytest
import respx

from app.services.client import fetch_page, NetworkError


class TestFetchPage:
    @pytest.mark.asyncio
    async def test_fetch_page_success(self, mock_http_client):
        """fetch_page returns HTML on 200."""
        mock_http_client.get("https://test.jenya.co.kr/page").respond(200, text="<html>OK</html>")
        result = await fetch_page("https://test.jenya.co.kr/page")
        assert result == "<html>OK</html>"

    @pytest.mark.asyncio
    async def test_retries_on_connect_error(self, mock_http_client):
        """fetch_page retries on ConnectError and succeeds."""
        route = mock_http_client.get("https://test.jenya.co.kr/page")
        route.side_effect = [
            httpx.ConnectError("connection refused"),
            httpx.Response(200, text="<html>Retry OK</html>"),
        ]
        result = await fetch_page("https://test.jenya.co.kr/page")
        assert result == "<html>Retry OK</html>"

    @pytest.mark.asyncio
    async def test_raises_network_error_after_retries(self, mock_http_client):
        """fetch_page raises NetworkError after exhausting retries."""
        mock_http_client.get("https://test.jenya.co.kr/page").side_effect = httpx.ConnectError("fail")
        with pytest.raises(NetworkError, match="Failed after 3 attempts"):
            await fetch_page("https://test.jenya.co.kr/page")

    @pytest.mark.asyncio
    async def test_retries_on_http_500(self, mock_http_client):
        """fetch_page retries on HTTP 500 and succeeds."""
        route = mock_http_client.get("https://test.jenya.co.kr/page")
        route.side_effect = [
            httpx.Response(500, text="Error"),
            httpx.Response(200, text="<html>OK</html>"),
        ]
        result = await fetch_page("https://test.jenya.co.kr/page")
        assert result == "<html>OK</html>"

    @pytest.mark.asyncio
    async def test_no_auth_headers(self, mock_http_client):
        """fetch_page does not send cookies or auth headers."""
        mock_http_client.get("https://test.jenya.co.kr/page").respond(200, text="ok")
        await fetch_page("https://test.jenya.co.kr/page")
        request = mock_http_client.calls[0].request
        assert "Cookie" not in request.headers

    @pytest.mark.asyncio
    async def test_retries_on_read_timeout(self, mock_http_client):
        """fetch_page retries on ReadTimeout."""
        route = mock_http_client.get("https://test.jenya.co.kr/page")
        route.side_effect = [
            httpx.ReadTimeout("timeout"),
            httpx.Response(200, text="<html>OK</html>"),
        ]
        result = await fetch_page("https://test.jenya.co.kr/page")
        assert result == "<html>OK</html>"
