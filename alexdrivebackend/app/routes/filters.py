from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.salecars import get_filter_data

router = APIRouter(prefix="/api")


@router.get("/filters")
async def get_filters():
    data = await get_filter_data()
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=3600"},
    )
