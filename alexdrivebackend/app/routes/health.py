import time

from fastapi import APIRouter

from app.services.jenya import get_last_successful_parse

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    last_parse = get_last_successful_parse()
    return {
        "status": "ok",
        "last_successful_parse_seconds_ago": int(time.time() - last_parse) if last_parse > 0 else None,
    }
