import asyncio

import httpx

from app.services.session import get_http_client

MAX_NETWORK_RETRIES = 3
NETWORK_RETRY_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ru;q=0.6",
}


class NetworkError(Exception):
    """Raised when all network retry attempts are exhausted."""
    pass


async def fetch_page(url: str) -> str:
    """GET a URL with network retry. No auth needed."""
    client = get_http_client()
    last_exc = None
    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            resp = await client.get(url, headers=HEADERS)
            resp.raise_for_status()
            return resp.text
        except NETWORK_RETRY_ERRORS as exc:
            last_exc = exc
            print(f"[client] Network error on attempt {attempt}/{MAX_NETWORK_RETRIES}: {exc}")
            if attempt < MAX_NETWORK_RETRIES:
                await asyncio.sleep(0.5 * attempt)
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            print(f"[client] HTTP {exc.response.status_code} on attempt {attempt}/{MAX_NETWORK_RETRIES}: {url}")
            if attempt < MAX_NETWORK_RETRIES:
                await asyncio.sleep(0.5 * attempt)
    raise NetworkError(f"Failed after {MAX_NETWORK_RETRIES} attempts: {last_exc}") from last_exc
