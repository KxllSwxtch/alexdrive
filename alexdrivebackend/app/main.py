import asyncio
import time
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from app.config import settings
from app.routes import admin, cars, filters, health
from app.services.salecars import (
    get_car_listings,
    get_filter_data,
    listing_refresh_loop,
    _load_detail_cache_from_disk,
    _load_excluded_ids_from_disk,
    _save_detail_cache_to_disk,
    detail_cache_persist_loop,
)
from app.services.client import NetworkError, set_http_client


async def _prewarm_caches():
    """Background cache warming — runs after server is accepting connections."""
    try:
        await get_filter_data()
        print("[server] Filter cache pre-warmed")
    except Exception as e:
        print(f"[server] Filter pre-warm failed: {e}")

    try:
        await get_car_listings({
            "PageNow": 1, "PageSize": 24,
            "PageSort": "ModDt", "PageAscDesc": "DESC",
        })
        print("[server] Listing cache pre-warmed")
    except Exception as e:
        print(f"[server] Listing pre-warm failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    client_kwargs: dict = {
        "timeout": httpx.Timeout(30.0),
        "follow_redirects": True,
    }
    if settings.proxy_url:
        client_kwargs["proxy"] = settings.proxy_url
        masked = settings.proxy_url.split("@")[-1] if "@" in settings.proxy_url else settings.proxy_url
        print(f"[server] Using proxy: {masked}")

    async with httpx.AsyncClient(**client_kwargs) as client:
        set_http_client(client)

        # Load detail cache and exclusion set from disk (instant, no network)
        loaded = _load_detail_cache_from_disk()
        if loaded:
            print(f"[server] Restored {loaded} detail cache entries from disk")
        excluded = _load_excluded_ids_from_disk()
        if excluded:
            print(f"[server] Restored {excluded} excluded car IDs from disk")

        # Start background tasks
        prewarm_task = asyncio.create_task(_prewarm_caches())
        listing_refresh_task = asyncio.create_task(listing_refresh_loop())
        detail_persist_task = asyncio.create_task(detail_cache_persist_loop())

        print(f"[server] AlexDrive backend running on port {settings.port}")
        yield

        prewarm_task.cancel()
        listing_refresh_task.cancel()
        detail_persist_task.cancel()
        try:
            await asyncio.gather(
                prewarm_task,
                listing_refresh_task, detail_persist_task,
                return_exceptions=True,
            )
        except asyncio.CancelledError:
            pass

        # Final save on shutdown
        _save_detail_cache_to_disk()


app = FastAPI(lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(filters.router)
app.include_router(cars.router)
app.include_router(admin.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = int((time.time() - start) * 1000)
    print(f"[{request.method}] {request.url.path} -> {response.status_code} ({duration}ms)")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, NetworkError):
        print(f"[error] Network failure: {exc}")
        return JSONResponse(status_code=503, content={"error": "Service temporarily unavailable"})
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
        print(f"[error] Connection error: {exc}")
        return JSONResponse(status_code=503, content={"error": "Service temporarily unavailable"})
    print(f"[error] {type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )
