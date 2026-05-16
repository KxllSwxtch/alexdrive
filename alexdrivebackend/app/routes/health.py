import time

from fastapi import APIRouter

from app.config import settings
from app.services.scraper import get_last_successful_parse, is_rate_limited, _listing_cache

router = APIRouter(prefix="/api")


STALE_THRESHOLD_SECONDS = 900  # 15 minutes — anything longer is abnormal with fallback paths in place


@router.get("/health")
async def health():
    last_parse = get_last_successful_parse()
    rate_limited = is_rate_limited()
    seconds_ago = int(time.time() - last_parse) if last_parse > 0 else None
    stale = seconds_ago is not None and seconds_ago > STALE_THRESHOLD_SECONDS
    return {
        "status": "degraded" if (rate_limited or stale) else "ok",
        "last_successful_parse_seconds_ago": seconds_ago,
        "rate_limited": rate_limited,
        "proxy_configured": bool(settings.proxy_url),
        "listing_cache_entries": len(_listing_cache),
    }
