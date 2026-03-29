import time

from fastapi import APIRouter

from app.services.salecars import get_last_successful_parse, is_rate_limited

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    last_parse = get_last_successful_parse()
    rate_limited = is_rate_limited()
    return {
        "status": "degraded" if rate_limited else "ok",
        "last_successful_parse_seconds_ago": int(time.time() - last_parse) if last_parse > 0 else None,
        "rate_limited": rate_limited,
    }
