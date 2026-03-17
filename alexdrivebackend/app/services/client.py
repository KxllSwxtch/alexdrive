import asyncio
import json
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.services.session import get_current_ua, get_http_client, get_session, invalidate_session

MAX_NETWORK_RETRIES = 3
NETWORK_RETRY_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)


class NetworkError(Exception):
    """Raised when all network retry attempts are exhausted."""
    pass


async def fetch_with_auth(
    path: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
    _retried: bool = False,
) -> tuple[int, str]:
    cookies = await get_session()
    client = get_http_client()

    req_headers = {
        "Cookie": cookies,
        "User-Agent": get_current_ua(),
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{settings.carmanager_base_url}/Car/Data",
    }
    if headers:
        req_headers.update(headers)

    last_exc = None
    for attempt in range(1, MAX_NETWORK_RETRIES + 1):
        try:
            response = await client.request(
                method,
                f"{settings.carmanager_base_url}{path}",
                headers=req_headers,
                content=body,
            )
            break
        except NETWORK_RETRY_ERRORS as exc:
            last_exc = exc
            print(f"[client] Network error on attempt {attempt}/{MAX_NETWORK_RETRIES}: {exc}")
            if attempt < MAX_NETWORK_RETRIES:
                await asyncio.sleep(0.5 * attempt)
    else:
        raise NetworkError(f"Failed after {MAX_NETWORK_RETRIES} attempts: {last_exc}") from last_exc

    location = response.headers.get("location", "")
    if (response.status_code == 302 and "Login" in location) or response.status_code == 401:
        if _retried:
            raise RuntimeError("Authentication failed after retry")
        print(f"[client] Auth failure on {path}, re-authenticating...")
        invalidate_session()
        await asyncio.sleep(1.0)
        return await fetch_with_auth(path, method, headers, body, _retried=True)

    text = response.text
    return response.status_code, text


async def fetch_page(path: str) -> str:
    _, text = await fetch_with_auth(path)
    return text


async def post_form(path: str, data: dict[str, str]) -> str:
    body = urlencode(data)
    _, text = await fetch_with_auth(
        path,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=body,
    )
    return text


async def post_json(path: str, data: dict) -> str:
    body = json.dumps(data)
    _, text = await fetch_with_auth(
        path,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
        body=body,
    )
    return text


async def post_json_parsed(path: str, data: dict | None = None) -> Any:
    """POST JSON and return parsed JSON response."""
    body = json.dumps(data) if data else ""
    _, text = await fetch_with_auth(
        path,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
        body=body,
    )
    return json.loads(text)
