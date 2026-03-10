from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.session import get_session_info, inject_cookies

router = APIRouter(prefix="/api/admin")


class CookiePayload(BaseModel):
    cookies: str


async def verify_admin_secret(
    x_admin_secret: str = Header(..., alias="X-Admin-Secret"),
) -> None:
    if not settings.admin_secret:
        raise HTTPException(
            status_code=403,
            detail="Admin endpoints disabled (ADMIN_SECRET not configured)",
        )
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/session", dependencies=[Depends(verify_admin_secret)])
async def set_session(payload: CookiePayload):
    success = await inject_cookies(payload.cookies)
    if not success:
        raise HTTPException(status_code=400, detail="Cookies are invalid or expired")

    return {"status": "ok", "message": "Session cookies updated"}


@router.get("/session", dependencies=[Depends(verify_admin_secret)])
async def get_session_status():
    return get_session_info()
