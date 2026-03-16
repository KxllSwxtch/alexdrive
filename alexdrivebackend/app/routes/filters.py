from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.jenya import get_filter_data

router = APIRouter(prefix="/api")


@router.get("/filters")
async def get_filters(carnation: str | None = Query(None)):
    data = await get_filter_data(carnation=int(carnation) if carnation else 1)
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=3600"},
    )
