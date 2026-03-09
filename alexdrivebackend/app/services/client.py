from urllib.parse import urlencode

from app.config import settings
from app.services.session import get_http_client, get_session, invalidate_session


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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if headers:
        req_headers.update(headers)

    response = await client.request(
        method,
        f"{settings.carmanager_base_url}{path}",
        headers=req_headers,
        content=body,
    )

    location = response.headers.get("location", "")
    if (response.status_code == 302 and "Login" in location) or response.status_code == 401:
        if _retried:
            raise RuntimeError("Authentication failed after retry")
        invalidate_session()
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
