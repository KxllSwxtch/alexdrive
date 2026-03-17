import asyncio
import json
import time
from datetime import datetime, timedelta

import httpx
import pytest
import respx

from app.services import session as session_mod
from app.services.session import (
    _parse_session_expiry,
    _save_session_to_disk,
    _load_session_from_disk,
    validate_session,
    login,
    get_session,
    inject_cookies,
    get_session_info,
    invalidate_session,
    session_keepalive_loop,
    KST,
    SESSION_TTL,
)


# ── _parse_session_expiry (pure function) ────────────────────


class TestParseSessionExpiry:
    def test_parse_valid_enddate(self):
        dt_str = "2026-03-10 15:30:00"
        cookies = f"Session_Cookie=UserID=test&EndDate={dt_str}&Other=foo; path=/"
        result = _parse_session_expiry(cookies)
        expected_dt = datetime(2026, 3, 10, 15, 30, 0, tzinfo=KST)
        expected = expected_dt.timestamp() - 60
        assert result is not None
        assert abs(result - expected) < 1

    def test_parse_no_session_cookie(self):
        cookies = "OtherCookie=abc123; path=/"
        assert _parse_session_expiry(cookies) is None

    def test_parse_no_enddate_field(self):
        cookies = "Session_Cookie=UserID%3Dtest%26Foo%3Dbar; path=/"
        assert _parse_session_expiry(cookies) is None

    def test_parse_malformed_date(self):
        cookies = "Session_Cookie=UserID%3Dtest%26EndDate%3Dnot-a-date; path=/"
        assert _parse_session_expiry(cookies) is None

    def test_parse_multiple_cookies_session_not_first(self):
        dt_str = "2026-06-15 12:00:00"
        cookies = f"SomeCookie=xyz; Session_Cookie=EndDate={dt_str}; path=/"
        result = _parse_session_expiry(cookies)
        assert result is not None
        expected_dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=KST)
        expected = expected_dt.timestamp() - 60
        assert abs(result - expected) < 1


# ── Disk persistence ─────────────────────────────────────────


class TestDiskPersistence:
    def test_save_load_roundtrip(self, session_file):
        session_mod._cached_cookies = "test-cookie"
        session_mod._cookie_expiry = time.time() + 3600
        _save_session_to_disk()

        # Clear globals
        session_mod._cached_cookies = ""
        session_mod._cookie_expiry = 0.0
        session_mod._disk_loaded = False

        result = _load_session_from_disk()
        assert result is True
        assert session_mod._cached_cookies == "test-cookie"
        assert session_mod._cookie_expiry > time.time()

    def test_load_expired(self, session_file):
        session_file.write_text(json.dumps({
            "cookies": "expired-cookie",
            "expiry": time.time() - 100,
        }))
        result = _load_session_from_disk()
        assert result is False
        assert session_mod._cached_cookies == ""

    def test_load_file_not_found(self, session_file):
        # session_file doesn't exist yet by default
        result = _load_session_from_disk()
        assert result is False

    def test_load_corrupted_json(self, session_file):
        session_file.write_text("{bad json!!")
        result = _load_session_from_disk()
        assert result is False

    def test_save_io_error(self, session_file, monkeypatch):
        session_mod._cached_cookies = "cookie"
        session_mod._cookie_expiry = time.time() + 3600
        monkeypatch.setattr(session_mod, "SESSION_FILE", session_file / "nonexistent" / "file.json")
        # Should not raise
        _save_session_to_disk()

    def test_load_sets_disk_loaded_flag(self, session_file):
        session_mod._disk_loaded = False
        _load_session_from_disk()
        assert session_mod._disk_loaded is True


# ── validate_session ─────────────────────────────────────────


class TestValidateSession:
    @pytest.mark.asyncio
    async def test_validate_200_returns_true(self, mock_http_client):
        mock_http_client.post("https://test.carmanager.co.kr/JsonUser/JsonGetCarConfigBookMark").respond(200)
        result = await validate_session("valid-cookies")
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_302_login_returns_false(self, mock_http_client):
        mock_http_client.post("https://test.carmanager.co.kr/JsonUser/JsonGetCarConfigBookMark").respond(
            302, headers={"Location": "/User/Login?returnurl=%2F"}
        )
        result = await validate_session("expired-cookies")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_401_returns_false(self, mock_http_client):
        mock_http_client.post("https://test.carmanager.co.kr/JsonUser/JsonGetCarConfigBookMark").respond(401)
        result = await validate_session("bad-cookies")
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_network_error_returns_false(self, mock_http_client):
        mock_http_client.post("https://test.carmanager.co.kr/JsonUser/JsonGetCarConfigBookMark").mock(
            side_effect=httpx.ConnectError("connection failed")
        )
        result = await validate_session("any-cookies")
        assert result is False


# ── login ─────────────────────────────────────────────────────


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success_with_enddate(self, mock_http_client):
        future = datetime.now(KST) + timedelta(hours=1)
        enddate_str = future.strftime("%Y-%m-%d %H:%M:%S")
        cookie_val = f"Session_Cookie=UserID=test&EndDate={enddate_str}"
        mock_http_client.post("https://test.carmanager.co.kr/User/Login").respond(
            302, headers={"Set-Cookie": cookie_val}
        )
        cookies = await login()
        assert "Session_Cookie" in cookies
        # Should use server-provided expiry, not the fallback
        expected = future.timestamp() - 60
        assert abs(session_mod._cookie_expiry - expected) < 2

    @pytest.mark.asyncio
    async def test_login_success_fallback_ttl(self, mock_http_client):
        mock_http_client.post("https://test.carmanager.co.kr/User/Login").respond(
            302, headers={"Set-Cookie": "SomeCookie=value123"}
        )
        before = time.time()
        cookies = await login()
        assert cookies == "SomeCookie=value123"
        assert session_mod._cookie_expiry >= before + SESSION_TTL - 1

    @pytest.mark.asyncio
    async def test_login_retries_on_failure(self, mock_http_client):
        route = mock_http_client.post("https://test.carmanager.co.kr/User/Login")
        route.side_effect = [
            httpx.ConnectError("fail 1"),
            httpx.ConnectError("fail 2"),
            respx.MockResponse(302, headers={"Set-Cookie": "GoodCookie=yes"}),
        ]
        cookies = await login()
        assert cookies == "GoodCookie=yes"

    @pytest.mark.asyncio
    async def test_login_fails_after_3_retries(self, mock_http_client):
        mock_http_client.post("https://test.carmanager.co.kr/User/Login").mock(
            side_effect=httpx.ConnectError("always fail")
        )
        with pytest.raises(httpx.ConnectError):
            await login()

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, mock_http_client, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "carmanager_username", "")
        with pytest.raises(RuntimeError, match="CARMANAGER_USERNAME"):
            await login()


# ── get_session ───────────────────────────────────────────────


class TestGetSession:
    @pytest.mark.asyncio
    async def test_returns_cached_when_valid(self, mock_http_client):
        session_mod._cached_cookies = "cached-cookie"
        session_mod._cookie_expiry = time.time() + 3600
        session_mod._disk_loaded = True
        result = await get_session()
        assert result == "cached-cookie"

    @pytest.mark.asyncio
    async def test_validates_before_login(self, mock_http_client):
        session_mod._cached_cookies = "old-cookie"
        session_mod._cookie_expiry = time.time() - 1  # expired
        session_mod._disk_loaded = True
        # Validation succeeds → should skip login
        mock_http_client.post("https://test.carmanager.co.kr/JsonUser/JsonGetCarConfigBookMark").respond(200)
        result = await get_session()
        assert result == "old-cookie"
        assert session_mod._cookie_expiry > time.time()

    @pytest.mark.asyncio
    async def test_logs_in_when_validation_fails(self, mock_http_client):
        session_mod._cached_cookies = "stale-cookie"
        session_mod._cookie_expiry = time.time() - 1  # expired
        session_mod._disk_loaded = True
        mock_http_client.post("https://test.carmanager.co.kr/JsonUser/JsonGetCarConfigBookMark").respond(
            302, headers={"Location": "/User/Login"}
        )
        mock_http_client.post("https://test.carmanager.co.kr/User/Login").respond(
            302, headers={"Set-Cookie": "NewCookie=fresh"}
        )
        result = await get_session()
        assert result == "NewCookie=fresh"


# ── inject_cookies / get_session_info / invalidate_session ────


class TestAdminSessionFunctions:
    @pytest.mark.asyncio
    async def test_inject_valid_cookies(self, mock_http_client):
        mock_http_client.post("https://test.carmanager.co.kr/JsonUser/JsonGetCarConfigBookMark").respond(200)
        result = await inject_cookies("valid-cookie")
        assert result is True
        assert session_mod._cached_cookies == "valid-cookie"

    @pytest.mark.asyncio
    async def test_inject_invalid_cookies(self, mock_http_client):
        mock_http_client.post("https://test.carmanager.co.kr/JsonUser/JsonGetCarConfigBookMark").respond(
            302, headers={"Location": "/User/Login"}
        )
        result = await inject_cookies("bad-cookie")
        assert result is False
        assert session_mod._cached_cookies == ""

    def test_session_info_with_cookies(self):
        session_mod._cached_cookies = "test-cookie"
        session_mod._cookie_expiry = time.time() + 1800
        info = get_session_info()
        assert info["has_cookies"] is True
        assert info["ttl_remaining_sec"] > 0

    def test_invalidate_clears_globals(self):
        session_mod._cached_cookies = "some-cookie"
        session_mod._cookie_expiry = time.time() + 9999
        invalidate_session()
        assert session_mod._cached_cookies == ""
        assert session_mod._cookie_expiry == 0.0


# ── session_keepalive_loop ────────────────────────────────────


class TestKeepalive:
    @pytest.mark.asyncio
    async def test_keepalive_validates_and_invalidates(self, mock_http_client, monkeypatch):
        monkeypatch.setattr(session_mod, "KEEPALIVE_INTERVAL", 0)
        monkeypatch.setattr(session_mod, "KEEPALIVE_JITTER", 0)
        session_mod._cached_cookies = "keepalive-cookie"
        session_mod._cookie_expiry = time.time() + 9999

        call_count = 0
        original_validate = validate_session

        async def counting_validate(cookies):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True  # first keepalive: valid
            return False  # second keepalive: expired

        monkeypatch.setattr(session_mod, "validate_session", counting_validate)

        task = asyncio.create_task(session_keepalive_loop())
        # Give the loop time to run a couple iterations
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert call_count >= 2
        assert session_mod._cached_cookies == ""
