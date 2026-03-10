import asyncio
import json
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlencode

import httpx

from app.config import settings

_cached_cookies: str = ""
_cookie_expiry: float = 0.0
_http_client: httpx.AsyncClient | None = None
_session_lock = asyncio.Lock()
_disk_loaded: bool = False

SESSION_TTL = 24 * 60 * 60  # 24h safety-net TTL
VALIDATION_TIMEOUT = 5.0
KEEPALIVE_INTERVAL = 4 * 60  # 4 minutes (server session TTL is ~10min)
SESSION_FILE = Path("/tmp/alexdrive_session.json")

# KST timezone (UTC+9) — carmanager.co.kr is Korean
KST = timezone(timedelta(hours=9))


def set_http_client(client: httpx.AsyncClient) -> None:
    global _http_client
    _http_client = client


def get_http_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError("HTTP client not initialized")
    return _http_client


# ── Disk persistence ────────────────────────────────────────


def _save_session_to_disk() -> None:
    try:
        SESSION_FILE.write_text(json.dumps({
            "cookies": _cached_cookies,
            "expiry": _cookie_expiry,
        }))
    except Exception as e:
        print(f"[session] Failed to save session to disk: {e}")


def _load_session_from_disk() -> bool:
    global _cached_cookies, _cookie_expiry, _disk_loaded
    _disk_loaded = True
    try:
        data = json.loads(SESSION_FILE.read_text())
        cookies = data.get("cookies", "")
        expiry = data.get("expiry", 0.0)
        if cookies and expiry > time.time():
            _cached_cookies = cookies
            _cookie_expiry = expiry
            print(f"[session] Loaded session from disk (expires in {int(expiry - time.time())}s)")
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[session] Failed to load session from disk: {e}")
    return False


# ── Session validation ──────────────────────────────────────


async def validate_session(cookies: str) -> bool:
    """Probe carmanager with a lightweight JSON endpoint to check if cookies are still valid."""
    client = get_http_client()
    try:
        response = await client.request(
            "POST",
            f"{settings.carmanager_base_url}/JsonUser/JsonGetCarConfigBookMark",
            headers={
                "Cookie": cookies,
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "X-Requested-With": "XMLHttpRequest",
            },
            content="",
            timeout=VALIDATION_TIMEOUT,
        )
        location = response.headers.get("location", "")
        if response.status_code == 302 and "Login" in location:
            return False
        if response.status_code == 401:
            return False
        if response.status_code == 200:
            return True
        return False
    except Exception:
        return False


# ── EndDate parsing ─────────────────────────────────────────


def _parse_session_expiry(cookies: str) -> float | None:
    """Extract EndDate from the Session_Cookie and convert to Unix timestamp."""
    match = re.search(r"Session_Cookie=([^;]+)", cookies)
    if not match:
        return None
    cookie_val = match.group(1)
    date_match = re.search(r"EndDate=(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", cookie_val)
    if not date_match:
        return None
    try:
        dt = datetime.strptime(date_match.group(1), "%Y-%m-%d %H:%M:%S")
        dt_kst = dt.replace(tzinfo=KST)
        # 60-second safety margin
        return dt_kst.timestamp() - 60
    except ValueError:
        return None


# ── Login ───────────────────────────────────────────────────


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

            # Use server-provided EndDate if available, otherwise 24h safety TTL
            server_expiry = _parse_session_expiry(cookies)
            if server_expiry and server_expiry > time.time():
                _cookie_expiry = server_expiry
                print(f"[session] Login successful (attempt {attempt}), expires in {int(server_expiry - time.time())}s (from EndDate)")
            else:
                _cookie_expiry = time.time() + SESSION_TTL
                print(f"[session] Login successful (attempt {attempt}), using {SESSION_TTL}s safety TTL")

            _save_session_to_disk()
            return cookies
        except Exception as err:
            msg = str(err)
            print(f"[session] Login attempt {attempt}/3 failed: {msg}")
            if attempt == 3:
                raise
            await asyncio.sleep(1.0 * attempt)

    raise RuntimeError("Login failed after all retries")


# ── Session management ──────────────────────────────────────


async def get_session() -> str:
    global _cached_cookies, _cookie_expiry, _disk_loaded

    # One-time: try loading from disk on first call
    if not _disk_loaded:
        _load_session_from_disk()

    if _cached_cookies and time.time() < _cookie_expiry:
        return _cached_cookies

    async with _session_lock:
        # Double-check after acquiring lock
        if _cached_cookies and time.time() < _cookie_expiry:
            return _cached_cookies

        # Try to validate existing cookies before login
        if _cached_cookies:
            if await validate_session(_cached_cookies):
                _cookie_expiry = time.time() + SESSION_TTL
                _save_session_to_disk()
                print("[session] Existing cookies still valid, skipping login")
                return _cached_cookies
            print("[session] Cookie validation failed, must login")

        return await login()


def invalidate_session() -> None:
    global _cached_cookies, _cookie_expiry
    _cached_cookies = ""
    _cookie_expiry = 0.0


# ── Admin injection ─────────────────────────────────────────


async def inject_cookies(cookies: str) -> bool:
    """Validate and store externally-provided cookies. Returns True on success."""
    global _cached_cookies, _cookie_expiry
    async with _session_lock:
        if await validate_session(cookies):
            _cached_cookies = cookies
            server_expiry = _parse_session_expiry(cookies)
            if server_expiry and server_expiry > time.time():
                _cookie_expiry = server_expiry
            else:
                _cookie_expiry = time.time() + SESSION_TTL
            _save_session_to_disk()
            print("[session] Cookies injected via admin endpoint")
            return True
    return False


def get_session_info() -> dict:
    """Return current session status (read-only)."""
    remaining = max(0, _cookie_expiry - time.time())
    return {
        "has_cookies": bool(_cached_cookies),
        "ttl_remaining_sec": int(remaining),
    }


# ── Keepalive ───────────────────────────────────────────────


async def session_keepalive_loop() -> None:
    """Periodically ping carmanager to keep the session alive."""
    while True:
        await asyncio.sleep(KEEPALIVE_INTERVAL)
        if not _cached_cookies:
            continue
        try:
            valid = await validate_session(_cached_cookies)
            if valid:
                print("[session] Keepalive: session still alive")
                _save_session_to_disk()
            else:
                print("[session] Keepalive: session expired, will re-login on next request")
                invalidate_session()
        except Exception as e:
            print(f"[session] Keepalive error: {e}")
