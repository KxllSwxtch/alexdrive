import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.jenya import _detail_cache, get_car_detail, get_car_listings, warm_detail_cache_for_listings

router = APIRouter(prefix="/api")


@router.get("/cars")
async def get_cars(
    carnation: str | None = Query(None),
    CarMakerNo: str | None = Query(None),
    CarModelNo: str | None = Query(None),
    CarModelDetailNo: str | None = Query(None),
    CarGradeNo: str | None = Query(None),
    CarGradeDetailNo: str | None = Query(None),
    CarYearFrom: str | None = Query(None),
    CarYearTo: str | None = Query(None),
    CarMileageFrom: str | None = Query(None),
    CarMileageTo: str | None = Query(None),
    CarPriceFrom: str | None = Query(None),
    CarPriceTo: str | None = Query(None),
    CarMissionNo: str | None = Query(None),
    CarFuelNo: str | None = Query(None),
    CarColorNo: str | None = Query(None),
    SearchCarNo: str | None = Query(None),
    PageNow: int | None = Query(None),
    PageSort: str | None = Query(None),
    PageAscDesc: str | None = Query(None),
):
    params = {
        "carnation": carnation or "1",
        "CarMakerNo": CarMakerNo,
        "CarModelNo": CarModelNo,
        "CarModelDetailNo": CarModelDetailNo,
        "CarGradeNo": CarGradeNo,
        "CarGradeDetailNo": CarGradeDetailNo,
        "CarYearFrom": CarYearFrom,
        "CarYearTo": CarYearTo,
        "CarMileageFrom": CarMileageFrom,
        "CarMileageTo": CarMileageTo,
        "CarPriceFrom": CarPriceFrom,
        "CarPriceTo": CarPriceTo,
        "CarMissionNo": CarMissionNo,
        "CarFuelNo": CarFuelNo,
        "CarColorNo": CarColorNo,
        "SearchCarNo": SearchCarNo,
        "PageNow": PageNow,
        "PageSort": PageSort,
        "PageAscDesc": PageAscDesc,
    }
    data = await get_car_listings(params)

    if data.get("listings"):
        asyncio.ensure_future(warm_detail_cache_for_listings(data["listings"]))
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=300, stale-while-revalidate=300"},
    )


@router.post("/cars/prefetch")
async def prefetch_detail(id: str | None = Query(None)):
    """Fire-and-forget cache warming. Returns 202 immediately."""
    if not id:
        return JSONResponse(status_code=400, content={"error": "Missing id"})
    if id not in _detail_cache:
        asyncio.ensure_future(get_car_detail(id))
    return JSONResponse(status_code=202, content={"status": "warming"})


@router.get("/cars/detail")
async def get_detail(id: str | None = Query(None)):
    if not id:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing id query parameter"},
        )
    data = await get_car_detail(id)
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=600, stale-while-revalidate=120"},
    )
