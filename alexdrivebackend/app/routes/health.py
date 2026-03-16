import time

from fastapi import APIRouter

from app.services.namsuwon import get_last_successful_fetch

router = APIRouter(prefix="/api")


@router.get("/health")
async def health():
    last_fetch = get_last_successful_fetch()
    return {
        "status": "ok",
        "last_successful_fetch_seconds_ago": int(time.time() - last_fetch) if last_fetch > 0 else None,
    }
