from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.parsers.diagnostics import diagnose_listing_html
from app.parsers.listing_parser import parse_car_listings, parse_total_count
from app.services.carmanager import _build_datapart_params
from app.services.client import post_json
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


@router.get("/diagnose", dependencies=[Depends(verify_admin_secret)])
async def diagnose():
    """Fetch /Car/DataPart and return raw HTML analysis for debugging."""
    session_info = get_session_info()

    json_body = _build_datapart_params({
        "PageNow": 1,
        "PageSize": 20,
        "PageSort": "ModDt",
        "PageAscDesc": "DESC",
    })

    html = await post_json("/Car/DataPart", json_body)
    listings = parse_car_listings(html)
    total = parse_total_count(html)
    diagnosis = diagnose_listing_html(html)

    return {
        "session": session_info,
        "html_length": len(html),
        "html_sample": html[:2000],
        "html_tail": html[-1000:] if len(html) > 1000 else html,
        "parsed_listings_count": len(listings),
        "parsed_total": total,
        "contains_login_redirect": "/User/Login" in html,
        "diagnosis": diagnosis,
    }
