import asyncio
import time
from urllib.parse import urlencode

import httpx

from app.config import settings

_cached_cookies: str = ""
_cookie_expiry: float = 0.0
_http_client: httpx.AsyncClient | None = None
_session_lock = asyncio.Lock()


def set_http_client(client: httpx.AsyncClient) -> None:
    global _http_client
    _http_client = client


def get_http_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("HTTP client not initialized")
    return _http_client


async def login() -> str:
    global _cached_cookies, _cookie_expiry

    username = settings.carmanager_username
    password = settings.carmanager_password

    if not username or not password:
        raise RuntimeError("CARMANAGER_USERNAME and CARMANAGER_PASSWORD must be set")

    client = get_http_client()

    for attempt in range(1, 4):
        try:
            body = urlencode({
                "userid": username,
                "userpwd": password,
                "sbxgubun": "1",
                "returnurl": "/",
            })

            response = await client.request(
                "POST",
                f"{settings.carmanager_base_url}/User/Login",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                content=body,
            )

            set_cookie_headers = response.headers.get_list("set-cookie")
            cookies = "; ".join(
                c.split(";")[0] for c in set_cookie_headers
            )

            if not cookies:
                raise RuntimeError("Login failed: no cookies returned")

            _cached_cookies = cookies
            _cookie_expiry = time.time() + 50 * 60

            print(f"[session] Login successful (attempt {attempt})")
            return cookies
        except Exception as err:
            msg = str(err)
            print(f"[session] Login attempt {attempt}/3 failed: {msg}")
            if attempt == 3:
                raise
            await asyncio.sleep(1.0 * attempt)

    raise RuntimeError("Login failed after all retries")


async def get_session() -> str:
    if _cached_cookies and time.time() < _cookie_expiry:
        return _cached_cookies
    async with _session_lock:
        # Double-check after acquiring lock
        if _cached_cookies and time.time() < _cookie_expiry:
            return _cached_cookies
        return await login()


def invalidate_session() -> None:
    global _cached_cookies, _cookie_expiry
    _cached_cookies = ""
    _cookie_expiry = 0.0
