"""
Follow-up debug: Is the block account-level or IP-level?

Tests:
1. Same account, NO proxy (local IP) — account vs IP
2. GET /Car/Data (HTML page) vs POST /Car/DataPart (API) — which endpoints blocked
3. Check if session validation endpoint is blocked too
"""

import asyncio
import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import httpx

BASE_URL = "https://www.carmanager.co.kr"
PROXY_URL = os.getenv("PROXY_URL", "")
USERNAME = os.getenv("CARMANAGER_USERNAME", "")
PASSWORD = os.getenv("CARMANAGER_PASSWORD", "")
RATE_LIMIT_MARKER = "limits_box"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg): print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")
def header(msg):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{msg}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")


LISTING_BODY = json.dumps({"para": {
    "PageNow": 1, "PageSize": 20, "PageSort": "5", "PageAscDesc": "1",
    "CarMode": "0", "CarSiDoNo": "102", "CarSiDoAreaNo": "1013",
    "CarDanjiNo": "", "CarMakerNo": None, "CarModelNo": None,
    "CarModelDetailNo": "", "CarGradeNo": "", "CarGradeDetailNo": "",
    "CarMakeSDate": "", "CarMakeEDate": "",
    "CarDriveSKm": None, "CarDriveEKm": None,
    "CarMission": "", "CarFuel": "", "CarColor": "",
    "CarSMoney": None, "CarEMoney": None,
    "CarIsLPG": "False", "CarIsSago": "False", "CarIsPhoto": "False",
    "CarIsSaleAmount": "False", "CarIsCarCheck": "False",
    "CarIsLeaseCheck": "False", "CarName": "", "CarDealerName": "",
    "CarShopName": "", "CarDealerHP": "", "CarNumber": "",
    "CarOption": "", "CarTruckTonS": "", "CarTruckTonE": "",
}})


async def login(client: httpx.AsyncClient) -> str | None:
    body = urlencode({
        "userid": USERNAME, "userpwd": PASSWORD,
        "sbxgubun": "1", "returnurl": "/",
    })
    resp = await client.post(
        f"{BASE_URL}/User/Login",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        content=body,
    )
    set_cookies = resp.headers.get_list("set-cookie")
    cookies = "; ".join(c.split(";")[0] for c in set_cookies)
    return cookies if cookies else None


async def test_with_client(client: httpx.AsyncClient, label: str) -> None:
    """Run all endpoint tests with the given client."""
    info(f"Logging in ({label})...")
    cookies = await login(client)
    if not cookies:
        fail(f"Login failed ({label})")
        return

    ok(f"Login OK ({label})")
    headers = {
        "Cookie": cookies,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE_URL}/Car/Data",
    }

    # Check exit IP
    try:
        ip_resp = await client.get("https://api.ipify.org?format=json", timeout=10)
        info(f"Exit IP: {ip_resp.json().get('ip', '?')}")
    except Exception:
        info("Could not check IP")

    # Test 1: GET /Car/Data (full page)
    info(f"GET /Car/Data (full HTML page)...")
    try:
        resp = await client.get(f"{BASE_URL}/Car/Data", headers=headers)
        rl = RATE_LIMIT_MARKER in resp.text
        if rl:
            fail(f"Rate limited on GET /Car/Data ({len(resp.text)} bytes)")
        else:
            ok(f"GET /Car/Data OK ({len(resp.text)} bytes)")
    except Exception as e:
        fail(f"GET /Car/Data error: {e}")

    # Test 2: POST /Car/DataPart (listings API)
    info(f"POST /Car/DataPart (listings API)...")
    try:
        resp = await client.post(
            f"{BASE_URL}/Car/DataPart",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            content=LISTING_BODY,
        )
        rl = RATE_LIMIT_MARKER in resp.text
        if rl:
            fail(f"Rate limited on POST /Car/DataPart ({len(resp.text)} bytes)")
        else:
            ok(f"POST /Car/DataPart OK ({len(resp.text)} bytes)")
    except Exception as e:
        fail(f"POST /Car/DataPart error: {e}")

    # Test 3: Session validation endpoint
    info(f"POST /JsonUser/JsonGetCarConfigBookMark (session check)...")
    try:
        resp = await client.post(
            f"{BASE_URL}/JsonUser/JsonGetCarConfigBookMark",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            content="",
        )
        info(f"Status: {resp.status_code}, body: {resp.text[:200]}")
    except Exception as e:
        fail(f"Session check error: {e}")

    # Test 4: Danji JSON API (filter data)
    info(f"POST /CodeBase/JsonBaseCodeDanji/1013 (filter API)...")
    try:
        resp = await client.post(
            f"{BASE_URL}/CodeBase/JsonBaseCodeDanji/1013",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            content="",
        )
        rl = RATE_LIMIT_MARKER in resp.text
        if rl:
            fail(f"Rate limited on Danji API ({len(resp.text)} bytes)")
        else:
            ok(f"Danji API OK ({len(resp.text)} bytes)")
    except Exception as e:
        fail(f"Danji API error: {e}")

    # Test 5: JS file (filter data)
    info(f"GET /Scripts/Common/CarBaseMaker.js (static JS)...")
    try:
        resp = await client.get(
            f"{BASE_URL}/Scripts/Common/CarBaseMaker.js",
            headers=headers,
        )
        if resp.status_code == 200 and len(resp.text) > 100:
            ok(f"JS file OK ({len(resp.text)} bytes)")
        else:
            fail(f"JS file: status {resp.status_code}, {len(resp.text)} bytes")
    except Exception as e:
        fail(f"JS file error: {e}")


async def main() -> None:
    header("Account Block Diagnosis")

    # Test A: WITH proxy
    header("Test A: With Proxy (same as Render)")
    client_kwargs: dict = {"timeout": httpx.Timeout(30.0), "follow_redirects": False}
    if PROXY_URL:
        client_kwargs["proxy"] = PROXY_URL
    async with httpx.AsyncClient(**client_kwargs) as client:
        await test_with_client(client, "via proxy")

    print()
    await asyncio.sleep(3)

    # Test B: WITHOUT proxy (local IP)
    header("Test B: Without Proxy (local IP)")
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), follow_redirects=False) as client:
        await test_with_client(client, "direct/local IP")

    header("Diagnosis")
    info("If BOTH proxy and direct are rate-limited:")
    info("  → Account-level block. Contact carmanager support.")
    info("  → Or wait for the block to expire (could be hours/days).")
    info("")
    info("If ONLY proxy is rate-limited:")
    info("  → Proxy IP is flagged. Need IP rotation or different proxy.")
    info("")
    info("If ONLY DataPart is blocked (not Danji/JS):")
    info("  → Search-specific rate limit. Reduce search frequency.")


if __name__ == "__main__":
    asyncio.run(main())
