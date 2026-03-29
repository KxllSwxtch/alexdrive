import httpx
import pytest
import respx

from app.services.client import NetworkError, fetch_page, set_http_client


class TestFetchPage:
    @pytest.mark.asyncio
    async def test_fetch_success(self, mock_http_client):
        mock_http_client.get("https://www.salecars.co.kr/page").respond(200, text="<html>OK</html>")
        text = await fetch_page("https://www.salecars.co.kr/page")
        assert text == "<html>OK</html>"

    @pytest.mark.asyncio
    async def test_network_retry_succeeds(self, mock_http_client):
        route = mock_http_client.get("https://www.salecars.co.kr/retry")
        route.side_effect = [
            httpx.ConnectError("fail 1"),
            httpx.ConnectError("fail 2"),
            respx.MockResponse(200, text="recovered"),
        ]
        text = await fetch_page("https://www.salecars.co.kr/retry")
        assert text == "recovered"

    @pytest.mark.asyncio
    async def test_network_retry_exhausted(self, mock_http_client):
        mock_http_client.get("https://www.salecars.co.kr/fail").mock(
            side_effect=httpx.ConnectError("always fail")
        )
        with pytest.raises(NetworkError, match="Failed after 3 attempts"):
            await fetch_page("https://www.salecars.co.kr/fail")
