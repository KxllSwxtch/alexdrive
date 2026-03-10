from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.session import get_session_info, inject_cookies

router = APIRouter(prefix="/api/admin")


class CookiePayload(BaseModel):
    cookies: str


@router.post("/session")
async def set_session(
    payload: CookiePayload,
    x_admin_secret: str = Header(..., alias="X-Admin-Secret"),
):
    if not settings.admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    success = await inject_cookies(payload.cookies)
    if not success:
        raise HTTPException(status_code=400, detail="Cookies are invalid or expired")

    return {"status": "ok", "message": "Session cookies updated"}


@router.get("/session")
async def get_session_status(
    x_admin_secret: str = Header(..., alias="X-Admin-Secret"),
):
    if not settings.admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    return get_session_info()
