import asyncio
import random

import httpx

MAX_NETWORK_RETRIES = 3
NETWORK_RETRY_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)

# Non-standard 6xx responses (and the bestproxy.com "612 auth fail" signature) come from
# the proxy layer itself, never from the origin. Treat them as proxy failures and try the
# direct client if one is configured.
_PROXY_FAILURE_STATUS = 612

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]

_http_client: httpx.AsyncClient | None = None
_direct_client: httpx.AsyncClient | None = None
_proxy_failure_logged = False


class NetworkError(Exception):
    """Raised when all network retry attempts are exhausted."""
    pass


def set_http_client(client: httpx.AsyncClient) -> None:
    global _http_client
    _http_client = client


def set_direct_client(client: httpx.AsyncClient | None) -> None:
    """Configure the direct (no-proxy) fallback client. Pass None to disable failover."""
    global _direct_client, _proxy_failure_logged
    _direct_client = client
    _proxy_failure_logged = False


def get_http_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("HTTP client not initialized")
    return _http_client


def _is_proxy_failure_status(status_code: int) -> bool:
    return status_code == _PROXY_FAILURE_STATUS or status_code >= 600


def _log_proxy_failure_once(detail: str) -> None:
    global _proxy_failure_logged
    if not _proxy_failure_logged:
        print(f"[client] Proxy failure detected ({detail}). Falling back to direct connection.")
        _proxy_failure_logged = True


async def fetch_page(url: str) -> str:
    """HTTP GET with retry. Falls back to direct client on proxy-side failures."""
    primary = get_http_client()
    ua = random.choice(_USER_AGENTS)
    headers = {"User-Agent": ua, "Accept": "text/html,*/*"}

    last_exc: Exception | None = None
    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            response = await primary.get(url, headers=headers)
            if _is_proxy_failure_status(response.status_code):
                _log_proxy_failure_once(f"HTTP {response.status_code} from proxy")
                direct_text = await _try_direct_get(url, headers)
                if direct_text is not None:
                    return direct_text
            if response.status_code >= 400:
                print(f"[client] HTTP {response.status_code} for {url[:80]}")
                if response.status_code in {429, 500, 502, 503, 504} and attempt < MAX_NETWORK_RETRIES:
                    await asyncio.sleep(0.5 * attempt)
                    continue
            return response.text
        except httpx.ProxyError as exc:
            _log_proxy_failure_once(f"ProxyError: {exc}")
            direct_text = await _try_direct_get(url, headers)
            if direct_text is not None:
                return direct_text
            last_exc = exc
            break
        except NETWORK_RETRY_ERRORS as exc:
            last_exc = exc
            print(f"[client] Network error on attempt {attempt}/{MAX_NETWORK_RETRIES}: {exc}")
            if attempt < MAX_NETWORK_RETRIES:
                await asyncio.sleep(0.5 * attempt)

    raise NetworkError(f"Failed after {MAX_NETWORK_RETRIES} attempts: {last_exc}") from last_exc


async def post_form(url: str, data: dict[str, str]) -> str:
    """HTTP POST form. Falls back to direct client on proxy-side failures."""
    primary = get_http_client()
    ua = random.choice(_USER_AGENTS)
    headers = {"User-Agent": ua}

    last_exc: Exception | None = None
    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            response = await primary.post(url, data=data, headers=headers)
            if _is_proxy_failure_status(response.status_code):
                _log_proxy_failure_once(f"HTTP {response.status_code} from proxy (POST)")
                direct_text = await _try_direct_post(url, data, headers)
                if direct_text is not None:
                    return direct_text
            if response.status_code >= 400:
                print(f"[client] HTTP {response.status_code} for POST {url[:80]}")
                if response.status_code in {429, 500, 502, 503, 504} and attempt < MAX_NETWORK_RETRIES:
                    await asyncio.sleep(0.5 * attempt)
                    continue
            return response.text
        except httpx.ProxyError as exc:
            _log_proxy_failure_once(f"ProxyError (POST): {exc}")
            direct_text = await _try_direct_post(url, data, headers)
            if direct_text is not None:
                return direct_text
            last_exc = exc
            break
        except NETWORK_RETRY_ERRORS as exc:
            last_exc = exc
            if attempt < MAX_NETWORK_RETRIES:
                await asyncio.sleep(0.5 * attempt)

    raise NetworkError(f"POST failed after {MAX_NETWORK_RETRIES} attempts: {last_exc}") from last_exc


async def _try_direct_get(url: str, headers: dict[str, str]) -> str | None:
    if _direct_client is None:
        return None
    try:
        response = await _direct_client.get(url, headers=headers)
        if _is_proxy_failure_status(response.status_code):
            return None
        return response.text
    except Exception as exc:
        print(f"[client] Direct-client GET also failed: {exc}")
        return None


async def _try_direct_post(url: str, data: dict[str, str], headers: dict[str, str]) -> str | None:
    if _direct_client is None:
        return None
    try:
        response = await _direct_client.post(url, data=data, headers=headers)
        if _is_proxy_failure_status(response.status_code):
            return None
        return response.text
    except Exception as exc:
        print(f"[client] Direct-client POST also failed: {exc}")
        return None
