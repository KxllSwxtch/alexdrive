import asyncio
import random

import httpx

MAX_NETWORK_RETRIES = 3
NETWORK_RETRY_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

_http_client: httpx.AsyncClient | None = None


class NetworkError(Exception):
    """Raised when all network retry attempts are exhausted."""
    pass


def set_http_client(client: httpx.AsyncClient) -> None:
    global _http_client
    _http_client = client


def get_http_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("HTTP client not initialized")
    return _http_client


async def fetch_page(url: str) -> str:
    """Simple HTTP GET with retry. No authentication needed."""
    client = get_http_client()
    ua = random.choice(_USER_AGENTS)

    last_exc = None
    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            response = await client.get(
                url,
                headers={"User-Agent": ua, "Accept": "text/html,*/*"},
            )
            if response.status_code >= 400:
                print(f"[client] HTTP {response.status_code} for {url[:80]}")
                if response.status_code in {429, 500, 502, 503, 504} and attempt < MAX_NETWORK_RETRIES:
                    await asyncio.sleep(0.5 * attempt)
                    continue
            return response.text
        except NETWORK_RETRY_ERRORS as exc:
            last_exc = exc
            print(f"[client] Network error on attempt {attempt}/{MAX_NETWORK_RETRIES}: {exc}")
            if attempt < MAX_NETWORK_RETRIES:
                await asyncio.sleep(0.5 * attempt)

    raise NetworkError(f"Failed after {MAX_NETWORK_RETRIES} attempts: {last_exc}") from last_exc


async def post_form(url: str, data: dict[str, str]) -> str:
    """Simple HTTP POST with form data and retry."""
    client = get_http_client()
    ua = random.choice(_USER_AGENTS)

    last_exc = None
    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            response = await client.post(
                url,
                data=data,
                headers={"User-Agent": ua},
            )
            if response.status_code >= 400:
                print(f"[client] HTTP {response.status_code} for POST {url[:80]}")
                if response.status_code in {429, 500, 502, 503, 504} and attempt < MAX_NETWORK_RETRIES:
                    await asyncio.sleep(0.5 * attempt)
                    continue
            return response.text
        except NETWORK_RETRY_ERRORS as exc:
            last_exc = exc
            if attempt < MAX_NETWORK_RETRIES:
                await asyncio.sleep(0.5 * attempt)

    raise NetworkError(f"POST failed after {MAX_NETWORK_RETRIES} attempts: {last_exc}") from last_exc
