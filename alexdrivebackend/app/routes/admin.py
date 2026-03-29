from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import settings
from app.services.salecars import get_car_listings, is_rate_limited, get_rate_limit_retry_after

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
    """Fetch a listing page and return status for debugging."""
    data = await get_car_listings({
        "PageNow": 1, "PageSize": 24,
        "PageSort": "ModDt", "PageAscDesc": "DESC",
    })

    return {
        "rate_limited": is_rate_limited(),
        "rate_limit_retry_after": get_rate_limit_retry_after(),
        "listing_count": len(data.get("listings", [])),
        "total": data.get("total", 0),
        "status": data.get("status", "unknown"),
    }
