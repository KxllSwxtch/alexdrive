import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.scraper import _detail_cache, get_car_detail, get_car_listings, get_rate_limit_retry_after, warm_detail_cache_for_listings

router = APIRouter(prefix="/api")

_prefetch_semaphore = asyncio.Semaphore(3)


async def _capped_prefetch(car_id: str) -> None:
    async with _prefetch_semaphore:
        await get_car_detail(car_id)


@router.get("/cars")
async def get_cars(
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
    SearchName: str | None = Query(None),
    SearchCarNo: str | None = Query(None),
    carnation: str | None = Query(None),
    PageNow: int | None = Query(None),
    PageSize: int | None = Query(None),
    PageSort: str | None = Query(None),
    PageAscDesc: str | None = Query(None),
):
    params = {
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
        "SearchName": SearchName,
        "SearchCarNo": SearchCarNo,
        "carnation": carnation,
        "PageNow": PageNow,
        "PageSize": PageSize,
        "PageSort": PageSort,
        "PageAscDesc": PageAscDesc,
    }
    data = await get_car_listings(params)

    if data.get("status") == "rate_limited" and not data.get("listings"):
        retry_after = data.get("retry_after") or get_rate_limit_retry_after() or 60
        return JSONResponse(
            status_code=429,
            content=data,
            headers={"Retry-After": str(retry_after), "Cache-Control": "no-cache"},
        )

    if data.get("status") in ("empty", "parse_failure") and not data.get("listings"):
        return JSONResponse(
            status_code=503,
            content=data,
            headers={"Retry-After": "30", "Cache-Control": "no-cache"},
        )

    if data.get("listings"):
        asyncio.ensure_future(warm_detail_cache_for_listings(data["listings"]))
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "public, max-age=300, stale-while-revalidate=300"},
    )


@router.post("/cars/prefetch")
async def prefetch_detail(id: str | None = Query(None)):
    if not id:
        return JSONResponse(status_code=400, content={"error": "Missing id"})
    if id not in _detail_cache:
        asyncio.ensure_future(_capped_prefetch(id))
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
