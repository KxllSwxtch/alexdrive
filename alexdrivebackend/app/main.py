import time
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from app.config import settings
from app.routes import cars, filters, health
from app.services.carmanager import get_car_listings, get_filter_data
from app.services.client import NetworkError
from app.services.session import set_http_client, get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    client_kwargs: dict = {
        "timeout": httpx.Timeout(30.0),
        "follow_redirects": False,
    }
    if settings.proxy_url:
        client_kwargs["proxy"] = settings.proxy_url

    async with httpx.AsyncClient(**client_kwargs) as client:
        set_http_client(client)
        try:
            await get_session()
            print("[server] Session pre-warmed successfully")
        except Exception as e:
            print(f"[server] Session pre-warm failed (will retry on first request): {e}")

        # Pre-warm filter cache
        try:
            await get_filter_data()
            print("[server] Filter cache pre-warmed")
        except Exception as e:
            print(f"[server] Filter pre-warm failed: {e}")

        # Pre-warm default listing cache
        try:
            await get_car_listings({
                "PageNow": 1, "PageSize": 20,
                "PageSort": "ModDt", "PageAscDesc": "DESC",
            })
            print("[server] Default listing cache pre-warmed")
        except Exception as e:
            print(f"[server] Listing pre-warm failed: {e}")

        print(f"[server] AlexDrive backend running on port {settings.port}")
        yield


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
