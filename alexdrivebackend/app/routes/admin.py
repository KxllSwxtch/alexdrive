from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import settings
from app.services.client import fetch_json
from app.services.namsuwon import _api_url

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
    """Fetch a test listing from namsuwon API and return diagnostics."""
    data = await fetch_json(
        _api_url("/api/proxy/cars"),
        {"lang": "ru", "page": "1", "page_size": "2"},
    )

    items = data.get("items", []) if isinstance(data, dict) else []
    total = data.get("total", 0) if isinstance(data, dict) else 0

    return {
        "api_url": f"{settings.namsuwon_base_url}/api/proxy/cars",
        "total_cars": total,
        "sample_count": len(items),
        "sample_items": items[:2],
        "status": "ok" if items else "no_items",
    }
