import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.namsuwon import _detail_cache, get_car_detail, get_car_listings, warm_detail_cache_for_listings

router = APIRouter(prefix="/api")


@router.get("/cars")
async def get_cars(
    bm_no: str | None = Query(None),
    bo_no: str | None = Query(None),
    bs_no: str | None = Query(None),
    bd_no: str | None = Query(None),
    yearFrom: str | None = Query(None),
    yearTo: str | None = Query(None),
    mileageFrom: str | None = Query(None),
    mileageTo: str | None = Query(None),
    priceFrom: str | None = Query(None),
    priceTo: str | None = Query(None),
    fuel: str | None = Query(None),
    transmission: str | None = Query(None),
    color: str | None = Query(None),
    keyword: str | None = Query(None),
    sort: str | None = Query(None),
    order: str | None = Query(None),
    page: int | None = Query(None),
    page_size: int | None = Query(None),
    extFlag1: str | None = Query(None),
    extFlag2: str | None = Query(None),
    extFlag3: str | None = Query(None),
    extFlag4: str | None = Query(None),
    extFlag5: str | None = Query(None),
):
    params = {
        "bm_no": bm_no,
        "bo_no": bo_no,
        "bs_no": bs_no,
        "bd_no": bd_no,
        "yearFrom": yearFrom,
        "yearTo": yearTo,
        "mileageFrom": mileageFrom,
        "mileageTo": mileageTo,
        "priceFrom": priceFrom,
        "priceTo": priceTo,
        "fuel": fuel,
        "transmission": transmission,
        "color": color,
        "keyword": keyword,
        "sort": sort,
        "order": order,
        "page": page or 1,
        "page_size": page_size or 20,
        "extFlag1": extFlag1,
        "extFlag2": extFlag2,
        "extFlag3": extFlag3,
        "extFlag4": extFlag4,
        "extFlag5": extFlag5,
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
