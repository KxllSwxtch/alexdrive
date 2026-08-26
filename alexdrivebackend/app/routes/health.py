import time

from fastapi import APIRouter

from app.config import settings
from app.services.scraper import (
    _listing_cache,
    get_last_successful_parse,
    is_degraded,
    is_rate_limited,
)

router = APIRouter(prefix="/api")


STALE_THRESHOLD_SECONDS = 900  # 15 minutes — anything longer is abnormal with fallback paths in place


@router.get("/health")
async def health():
    last_parse = get_last_successful_parse()
    rate_limited = is_rate_limited()
    seconds_ago = int(time.time() - last_parse) if last_parse > 0 else None
    # is_degraded() measures from process start when nothing has EVER parsed, so a
    # container that can never reach the source stops reporting "ok" forever. The
    # previous check only looked at last_parse > 0, so a permanently broken fresh
    # container looked healthy indefinitely -- which is how a 6-day outage in
    # 2026-08 went unnoticed behind an "Up 7 weeks (healthy)" container.
    stale = is_degraded()
    return {
        "status": "degraded" if (rate_limited or stale) else "ok",
        "last_successful_parse_seconds_ago": seconds_ago,
        "never_parsed": last_parse <= 0,
        "rate_limited": rate_limited,
        "proxy_configured": bool(settings.proxy_url),
        "listing_cache_entries": len(_listing_cache),
    }
