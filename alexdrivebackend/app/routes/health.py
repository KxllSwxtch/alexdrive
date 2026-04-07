import time

from fastapi import APIRouter

from app.config import settings
from app.services.salecars import get_last_successful_parse, is_rate_limited, _location_cache, _excluded_car_ids, _listing_cache

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    last_parse = get_last_successful_parse()
    rate_limited = is_rate_limited()
    seconds_ago = int(time.time() - last_parse) if last_parse > 0 else None
    stale = seconds_ago is not None and seconds_ago > 3600
    return {
        "status": "degraded" if (rate_limited or stale) else "ok",
        "last_successful_parse_seconds_ago": seconds_ago,
        "rate_limited": rate_limited,
        "proxy_configured": bool(settings.proxy_url),
        "location_cache_size": len(_location_cache),
        "excluded_car_ids": len(_excluded_car_ids),
        "listing_cache_entries": len(_listing_cache),
    }
