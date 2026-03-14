import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.carmanager import _detail_cache, get_car_detail, get_car_listings, warm_detail_cache_for_listings

router = APIRouter(prefix="/api")


@router.get("/cars")
async def get_cars(
    CarSiDoNo: str | None = Query(None),
    CarSiDoAreaNo: str | None = Query(None),
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
    DanjiNo: str | None = Query(None),
    CarLpg: str | None = Query(None),
    CarInsurance: str | None = Query(None),
    CarPhoto: str | None = Query(None),
    CarSalePrice: str | None = Query(None),
    CarInspection: str | None = Query(None),
    CarLease: str | None = Query(None),
    SearchName: str | None = Query(None),
    SearchCarNo: str | None = Query(None),
    PageNow: int | None = Query(None),
    PageSize: int | None = Query(None),
    PageSort: str | None = Query(None),
    PageAscDesc: str | None = Query(None),
):
    params = {
        "CarSiDoNo": CarSiDoNo,
        "CarSiDoAreaNo": CarSiDoAreaNo,
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
        "DanjiNo": DanjiNo,
        "CarLpg": CarLpg,
        "CarInsurance": CarInsurance,
        "CarPhoto": CarPhoto,
        "CarSalePrice": CarSalePrice,
        "CarInspection": CarInspection,
        "CarLease": CarLease,
        "SearchName": SearchName,
        "SearchCarNo": SearchCarNo,
        "PageNow": PageNow,
        "PageSize": PageSize,
        "PageSort": PageSort,
        "PageAscDesc": PageAscDesc,
    }
    data = await get_car_listings(params)

    if data.get("status") == "rate_limited" and not data.get("listings"):
        return JSONResponse(
            status_code=429,
            content=data,
            headers={"Retry-After": "10", "Cache-Control": "no-cache"},
        )

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
