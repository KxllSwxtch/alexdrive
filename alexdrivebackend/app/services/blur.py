import asyncio
import base64
from io import BytesIO

import httpx
from PIL import Image

from app.config import settings

_blur_cache: dict[str, str] = {}
_pending: set[str] = set()
_client: httpx.AsyncClient | None = None
_generation_running: bool = False


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        client_kwargs: dict = {
            "timeout": httpx.Timeout(15.0),
            "follow_redirects": True,
        }
        if settings.proxy_url:
            client_kwargs["proxy"] = settings.proxy_url
        _client = httpx.AsyncClient(**client_kwargs)
    return _client


async def enrich_listings_with_blur(result: dict) -> dict:
    """Add blurDataUrl to each listing from cache. Trigger background generation for uncached URLs."""
    global _generation_running

    listings = result.get("listings", [])
    urls_to_generate: list[str] = []

    enriched_listings = []
    for listing in listings:
        url = listing.get("imageUrl", "")
        blur = _blur_cache.get(url, "")
        enriched = {**listing, "blurDataUrl": blur}
        enriched_listings.append(enriched)

        if url and not blur and url not in _pending:
            _pending.add(url)
            urls_to_generate.append(url)

    if urls_to_generate and not _generation_running:
        asyncio.create_task(_process_pending())

    return {**result, "listings": enriched_listings}


async def _process_pending() -> None:
    """Process pending URLs sequentially (proxy-safe)."""
    global _generation_running
    _generation_running = True

    try:
        client = _get_client()
        while _pending:
            url = next(iter(_pending))
            try:
                response = await client.get(url)
                response.raise_for_status()

                img = Image.open(BytesIO(response.content))
                # Resize to 10px wide, preserve aspect ratio
                aspect = img.height / img.width
                thumb = img.resize((10, max(1, int(10 * aspect))), Image.LANCZOS)

                buf = BytesIO()
                thumb.save(buf, format="JPEG", quality=20)
                b64 = base64.b64encode(buf.getvalue()).decode()
                _blur_cache[url] = f"data:image/jpeg;base64,{b64}"
            except Exception as e:
                print(f"[blur] Failed to generate blur for {url[:60]}...: {e}")
            finally:
                _pending.discard(url)

            await asyncio.sleep(0.1)
    finally:
        _generation_running = False

    count = len(_blur_cache)
    print(f"[blur] Cache size: {count} entries")


async def generate_blur_for_url(url: str) -> str:
    """Generate blur data URL for a single image. Returns empty string on failure."""
    if not url:
        return ""

    cached = _blur_cache.get(url)
    if cached:
        return cached

    try:
        client = _get_client()
        response = await client.get(url)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        aspect = img.height / img.width
        thumb = img.resize((10, max(1, int(10 * aspect))), Image.LANCZOS)

        buf = BytesIO()
        thumb.save(buf, format="JPEG", quality=20)
        b64 = base64.b64encode(buf.getvalue()).decode()
        data_url = f"data:image/jpeg;base64,{b64}"
        _blur_cache[url] = data_url
        return data_url
    except Exception as e:
        print(f"[blur] Failed to generate blur for {url[:60]}...: {e}")
        return ""


async def close_client() -> None:
    """Cleanup for lifespan shutdown."""
    global _client
    if _client:
        await _client.aclose()
        _client = None
