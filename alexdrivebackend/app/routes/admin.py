from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import settings
from app.parsers.diagnostics import diagnose_listing_html
from app.parsers.listing_parser import parse_car_listings
from app.services.client import fetch_page
from app.services.jenya import _build_listing_url

router = APIRouter(prefix="/api/admin")


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


@router.get("/diagnose", dependencies=[Depends(verify_admin_secret)])
async def diagnose():
    """Fetch a listing page and return raw HTML analysis for debugging."""
    url = _build_listing_url({
        "PageNow": 1,
        "PageSort": "ModDt",
        "PageAscDesc": "DESC",
        "carnation": "1",
    })

    html = await fetch_page(url)
    listings = parse_car_listings(html)
    diagnosis = diagnose_listing_html(html)

    return {
        "url": url,
        "html_length": len(html),
        "html_sample": html[:2000],
        "html_tail": html[-1000:] if len(html) > 1000 else html,
        "parsed_listings_count": len(listings),
        "diagnosis": diagnosis,
    }
