import httpx
import pytest

from app.services.client import fetch_json, NetworkError


class TestFetchJson:
    @pytest.mark.asyncio
    async def test_fetch_json_success(self, mock_http_client):
        """fetch_json returns parsed JSON on 200."""
        mock_http_client.get("https://test.namsuwon.com/api/test").respond(
            200, json={"items": [1, 2, 3]}
        )
        result = await fetch_json("https://test.namsuwon.com/api/test")
        assert result == {"items": [1, 2, 3]}

    @pytest.mark.asyncio
    async def test_fetch_json_with_params(self, mock_http_client):
        """fetch_json passes query params correctly."""
        mock_http_client.get("https://test.namsuwon.com/api/test").respond(
            200, json={"ok": True}
        )
        result = await fetch_json("https://test.namsuwon.com/api/test", {"lang": "ru", "page": "1"})
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_retries_on_connect_error(self, mock_http_client):
        """fetch_json retries on ConnectError and succeeds."""
        route = mock_http_client.get("https://test.namsuwon.com/api/test")
        route.side_effect = [
            httpx.ConnectError("connection refused"),
            httpx.Response(200, json={"retry": "ok"}),
        ]
        result = await fetch_json("https://test.namsuwon.com/api/test")
        assert result == {"retry": "ok"}

    @pytest.mark.asyncio
    async def test_raises_network_error_after_retries(self, mock_http_client):
        """fetch_json raises NetworkError after exhausting retries."""
        mock_http_client.get("https://test.namsuwon.com/api/test").side_effect = httpx.ConnectError("fail")
        with pytest.raises(NetworkError, match="Failed after 3 attempts"):
            await fetch_json("https://test.namsuwon.com/api/test")

    @pytest.mark.asyncio
    async def test_retries_on_http_500(self, mock_http_client):
        """fetch_json retries on HTTP 500 and succeeds."""
        route = mock_http_client.get("https://test.namsuwon.com/api/test")
        route.side_effect = [
            httpx.Response(500, json={"error": "server error"}),
            httpx.Response(200, json={"ok": True}),
        ]
        result = await fetch_json("https://test.namsuwon.com/api/test")
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_no_auth_headers(self, mock_http_client):
        """fetch_json does not send cookies or auth headers."""
        mock_http_client.get("https://test.namsuwon.com/api/test").respond(200, json={})
        await fetch_json("https://test.namsuwon.com/api/test")
        request = mock_http_client.calls[0].request
        assert "Cookie" not in request.headers

    @pytest.mark.asyncio
    async def test_retries_on_read_timeout(self, mock_http_client):
        """fetch_json retries on ReadTimeout."""
        route = mock_http_client.get("https://test.namsuwon.com/api/test")
        route.side_effect = [
            httpx.ReadTimeout("timeout"),
            httpx.Response(200, json={"ok": True}),
        ]
        result = await fetch_json("https://test.namsuwon.com/api/test")
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_returns_list(self, mock_http_client):
        """fetch_json can return a list response."""
        mock_http_client.get("https://test.namsuwon.com/api/test").respond(
            200, json=[{"id": 1}, {"id": 2}]
        )
        result = await fetch_json("https://test.namsuwon.com/api/test")
        assert isinstance(result, list)
        assert len(result) == 2
