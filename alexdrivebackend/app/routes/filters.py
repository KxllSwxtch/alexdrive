from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.namsuwon import get_filter_data, get_models, get_series

router = APIRouter(prefix="/api")


@router.get("/filters")
async def get_filters():
    data = await get_filter_data()
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/filters/models")
async def get_filter_models(bm_no: str = Query(...)):
    data = await get_models(bm_no)
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/filters/series")
async def get_filter_series(bo_no: str = Query(...)):
    data = await get_series(bo_no)
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=3600"},
    )
