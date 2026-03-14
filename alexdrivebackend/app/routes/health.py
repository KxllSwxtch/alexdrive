import time

from fastapi import APIRouter

from app.services.carmanager import get_last_successful_parse, get_rate_limit_info
from app.services.session import get_session_info

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    session = get_session_info()
    last_parse = get_last_successful_parse()
    rate_info = get_rate_limit_info()
    return {
        "status": "ok",
        "session_active": session["has_cookies"] and session["ttl_remaining_sec"] > 0,
        "session_ttl": session["ttl_remaining_sec"],
        "last_successful_parse_seconds_ago": int(time.time() - last_parse) if last_parse > 0 else None,
        "rate_limited": rate_info["rate_limited"],
        "rate_limit_consecutive_hits": rate_info["consecutive_hits"],
        "rate_limit_cooldown_remaining": rate_info["cooldown_remaining"],
    }
