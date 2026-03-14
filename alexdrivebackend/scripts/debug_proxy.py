"""
Debug script for carmanager.co.kr rate limiting via proxy.

Run from alexdrivebackend/:
    source .venv/bin/activate
    python scripts/debug_proxy.py

Reads PROXY_URL, CARMANAGER_USERNAME, CARMANAGER_PASSWORD from .env automatically.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

# Load .env before importing anything else
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import httpx

BASE_URL = "https://www.carmanager.co.kr"
PROXY_URL = os.getenv("PROXY_URL", "")
USERNAME = os.getenv("CARMANAGER_USERNAME", "")
PASSWORD = os.getenv("CARMANAGER_PASSWORD", "")
RATE_LIMIT_MARKER = "limits_box"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {CYAN}→{RESET} {msg}")


def header(msg: str) -> None:
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{msg}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")


# ── Step 1: Basic proxy connectivity ─────────────────────────


async def step1_proxy_connectivity() -> bool:
    """Test basic proxy connectivity to carmanager.co.kr."""
    header("Step 1: Proxy Connectivity Test")

    if not PROXY_URL:
        fail("PROXY_URL not set in .env — testing without proxy")
    else:
        # Mask credentials in output
        masked = PROXY_URL.split("@")[-1] if "@" in PROXY_URL else PROXY_URL
        info(f"Proxy: ...@{masked}")

    client_kwargs: dict = {"timeout": httpx.Timeout(30.0), "follow_redirects": False}
    if PROXY_URL:
        client_kwargs["proxy"] = PROXY_URL

    async with httpx.AsyncClient(**client_kwargs) as client:
        # Test 1: Basic GET to homepage
        info("Testing GET / (homepage)...")
        try:
            start = time.time()
            resp = await client.get(BASE_URL, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            elapsed = int((time.time() - start) * 1000)

            if resp.status_code in (200, 302):
                ok(f"Status: {resp.status_code} ({elapsed}ms)")
            else:
                fail(f"Unexpected status: {resp.status_code} ({elapsed}ms)")

            has_rate_limit = RATE_LIMIT_MARKER in resp.text
            if has_rate_limit:
                fail(f"Rate limited! (limits_box found in {len(resp.text)} bytes)")
                return False
            else:
                ok(f"No rate limit marker (response: {len(resp.text)} bytes)")

        except Exception as e:
            fail(f"Connection failed: {e}")
            return False

        # Test 2: Check IP address via proxy
        info("Checking exit IP...")
        try:
            ip_resp = await client.get("https://api.ipify.org?format=json", timeout=10)
            ip_data = ip_resp.json()
            ok(f"Exit IP: {ip_data.get('ip', 'unknown')}")
        except Exception as e:
            warn(f"Could not check IP: {e}")

    return True


# ── Step 2: Full auth flow ───────────────────────────────────


async def step2_auth_flow() -> str | None:
    """Test full login + authenticated requests. Returns cookies on success."""
    header("Step 2: Full Authentication Flow")

    if not USERNAME or not PASSWORD:
        fail("CARMANAGER_USERNAME or CARMANAGER_PASSWORD not set")
        return None

    info(f"Username: {USERNAME}")

    client_kwargs: dict = {"timeout": httpx.Timeout(30.0), "follow_redirects": False}
    if PROXY_URL:
        client_kwargs["proxy"] = PROXY_URL

    async with httpx.AsyncClient(**client_kwargs) as client:
        # Login
        info("Logging in...")
        try:
            start = time.time()
            body = urlencode({
                "userid": USERNAME,
                "userpwd": PASSWORD,
                "sbxgubun": "1",
                "returnurl": "/",
            })
            resp = await client.post(
                f"{BASE_URL}/User/Login",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                content=body,
            )
            elapsed = int((time.time() - start) * 1000)

            set_cookies = resp.headers.get_list("set-cookie")
            cookies = "; ".join(c.split(";")[0] for c in set_cookies)

            if cookies:
                ok(f"Login successful ({elapsed}ms), got {len(set_cookies)} cookies")
                # Show session expiry if present
                import re
                date_match = re.search(r"EndDate=(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", cookies)
                if date_match:
                    info(f"Session EndDate: {date_match.group(1)} (KST)")
            else:
                fail(f"Login returned no cookies (status: {resp.status_code}, {elapsed}ms)")
                if resp.status_code == 302:
                    info(f"Redirect to: {resp.headers.get('location', 'unknown')}")
                return None

        except Exception as e:
            fail(f"Login failed: {e}")
            return None

        # Test authenticated request: /Car/DataPart (listing)
        info("Fetching car listings (POST /Car/DataPart)...")
        try:
            import json
            listing_body = json.dumps({"para": {
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

            start = time.time()
            resp = await client.post(
                f"{BASE_URL}/Car/DataPart",
                headers={
                    "Cookie": cookies,
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{BASE_URL}/Car/Data",
                },
                content=listing_body,
            )
            elapsed = int((time.time() - start) * 1000)

            has_rate_limit = RATE_LIMIT_MARKER in resp.text
            if has_rate_limit:
                fail(f"RATE LIMITED on listings! (limits_box in {len(resp.text)} bytes, {elapsed}ms)")
                print(f"\n  {RED}Response preview:{RESET}")
                print(f"  {resp.text[:500]}")
            else:
                # Count car items in response
                car_count = resp.text.count('class="car_list_')
                if car_count == 0:
                    car_count = resp.text.count('data-encarno')
                if car_count == 0:
                    car_count = resp.text.count('caritem')
                ok(f"Listings OK ({elapsed}ms, {len(resp.text)} bytes, ~{car_count} items)")

        except Exception as e:
            fail(f"Listing request failed: {e}")

        # Test detail request
        info("Fetching a car detail (POST /PopupFrame/CarDetailEnc)...")
        try:
            # First extract an encrypted ID from listings
            import re
            enc_ids = re.findall(r'data-encarno="([^"]+)"', resp.text)
            if not enc_ids:
                enc_ids = re.findall(r"encarno=([^&\"']+)", resp.text)

            if enc_ids:
                test_id = enc_ids[0]
                info(f"Testing with ID: {test_id[:30]}...")

                start = time.time()
                detail_resp = await client.post(
                    f"{BASE_URL}/PopupFrame/CarDetailEnc",
                    headers={
                        "Cookie": cookies,
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": f"{BASE_URL}/Car/Data",
                    },
                    content=urlencode({"encarno": test_id}),
                )
                elapsed = int((time.time() - start) * 1000)

                has_rate_limit = RATE_LIMIT_MARKER in detail_resp.text
                if has_rate_limit:
                    fail(f"RATE LIMITED on detail! (limits_box in {len(detail_resp.text)} bytes, {elapsed}ms)")
                else:
                    ok(f"Detail OK ({elapsed}ms, {len(detail_resp.text)} bytes)")
            else:
                warn("No encrypted IDs found in listing response, skipping detail test")

        except Exception as e:
            fail(f"Detail request failed: {e}")

        return cookies


# ── Step 3: Rate limit threshold test ────────────────────────


async def step3_rate_limit_threshold(cookies: str) -> None:
    """Make repeated requests to find where rate limiting kicks in."""
    header("Step 3: Rate Limit Threshold Test")

    if not cookies:
        fail("No cookies available, skipping")
        return

    client_kwargs: dict = {"timeout": httpx.Timeout(30.0), "follow_redirects": False}
    if PROXY_URL:
        client_kwargs["proxy"] = PROXY_URL

    import json

    listing_body = json.dumps({"para": {
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

    headers = {
        "Cookie": cookies,
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE_URL}/Car/Data",
    }

    async def make_request(client: httpx.AsyncClient, label: str) -> bool:
        """Make a listing request. Returns True if OK, False if rate-limited."""
        start = time.time()
        resp = await client.post(
            f"{BASE_URL}/Car/DataPart",
            headers=headers,
            content=listing_body,
        )
        elapsed = int((time.time() - start) * 1000)
        rate_limited = RATE_LIMIT_MARKER in resp.text
        if rate_limited:
            fail(f"{label}: RATE LIMITED ({elapsed}ms, {len(resp.text)} bytes)")
        else:
            ok(f"{label}: OK ({elapsed}ms, {len(resp.text)} bytes)")
        return not rate_limited

    async with httpx.AsyncClient(**client_kwargs) as client:
        # Test A: 5 requests with 3s intervals (conservative)
        print(f"\n{CYAN}Test A: 5 requests @ 3s intervals{RESET}")
        rate_limited = False
        for i in range(5):
            if i > 0:
                await asyncio.sleep(3.0)
            success = await make_request(client, f"  A.{i+1}")
            if not success:
                rate_limited = True
                break
        if not rate_limited:
            ok("3s interval: all passed")

        # Cool down
        info("Cooling down 10s...")
        await asyncio.sleep(10)

        # Test B: 5 requests with 2s intervals (current setting)
        print(f"\n{CYAN}Test B: 5 requests @ 2s intervals (current MIN_REQUEST_INTERVAL){RESET}")
        rate_limited = False
        for i in range(5):
            if i > 0:
                await asyncio.sleep(2.0)
            success = await make_request(client, f"  B.{i+1}")
            if not success:
                rate_limited = True
                break
        if not rate_limited:
            ok("2s interval: all passed")

        # Cool down
        info("Cooling down 10s...")
        await asyncio.sleep(10)

        # Test C: 5 requests with 1s intervals (aggressive)
        print(f"\n{CYAN}Test C: 5 requests @ 1s intervals{RESET}")
        rate_limited = False
        for i in range(5):
            if i > 0:
                await asyncio.sleep(1.0)
            success = await make_request(client, f"  C.{i+1}")
            if not success:
                rate_limited = True
                break
        if not rate_limited:
            ok("1s interval: all passed")

        # Cool down
        info("Cooling down 10s...")
        await asyncio.sleep(10)

        # Test D: Burst of 5 rapid requests (simulates detail warming)
        print(f"\n{CYAN}Test D: Burst of 5 rapid requests (no delay){RESET}")
        rate_limited = False
        for i in range(5):
            success = await make_request(client, f"  D.{i+1}")
            if not success:
                rate_limited = True
                break
        if not rate_limited:
            ok("Burst: all passed")
        else:
            warn("Burst requests trigger rate limit — detail warming is likely the cause")

        # Test E: Mixed listing + detail requests (simulates real usage)
        info("Cooling down 10s before mixed test...")
        await asyncio.sleep(10)

        print(f"\n{CYAN}Test E: Mixed listing + detail burst (simulates real page load){RESET}")
        info("1 listing request + 3 rapid detail requests...")

        # Listing
        success = await make_request(client, "  E.listing")
        if success:
            # Rapid detail requests (like warming)
            import re
            resp = await client.post(
                f"{BASE_URL}/Car/DataPart",
                headers=headers,
                content=listing_body,
            )
            enc_ids = re.findall(r'data-encarno="([^"]+)"', resp.text)
            if not enc_ids:
                enc_ids = re.findall(r"encarno=([^&\"']+)", resp.text)

            for i, eid in enumerate(enc_ids[:3]):
                start = time.time()
                detail_resp = await client.post(
                    f"{BASE_URL}/PopupFrame/CarDetailEnc",
                    headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                    content=urlencode({"encarno": eid}),
                )
                elapsed = int((time.time() - start) * 1000)
                rl = RATE_LIMIT_MARKER in detail_resp.text
                if rl:
                    fail(f"  E.detail.{i+1}: RATE LIMITED ({elapsed}ms)")
                else:
                    ok(f"  E.detail.{i+1}: OK ({elapsed}ms)")


# ── Main ─────────────────────────────────────────────────────


async def main() -> None:
    header("AlexDrive Proxy & Rate Limit Debugger")
    info(f"Target: {BASE_URL}")
    info(f"Proxy configured: {'yes' if PROXY_URL else 'NO'}")
    info(f"Credentials configured: {'yes' if USERNAME and PASSWORD else 'NO'}")

    # Step 1
    proxy_ok = await step1_proxy_connectivity()
    if not proxy_ok:
        fail("Proxy connectivity failed — fix this before proceeding")
        sys.exit(1)

    # Step 2
    cookies = await step2_auth_flow()
    if not cookies:
        fail("Auth flow failed — cannot proceed to rate limit tests")
        sys.exit(1)

    # Step 3
    await step3_rate_limit_threshold(cookies)

    header("Summary")
    info("If all tests passed locally, the issue is likely Render-specific:")
    info("  - Multiple instances hitting same proxy IP")
    info("  - Detail cache warming creating request bursts")
    info("  - Startup warmup (7+ requests) triggering limits")
    info("")
    info("If rate limits appeared in Tests D/E, detail warming is the culprit.")
    info("If rate limits appeared in Tests B/C, MIN_REQUEST_INTERVAL needs increasing.")


if __name__ == "__main__":
    asyncio.run(main())
