from fastapi import APIRouter

from app.services.carmanager import get_filter_data

router = APIRouter(prefix="/api")


@router.get("/filters")
async def get_filters():
    return await get_filter_data()
