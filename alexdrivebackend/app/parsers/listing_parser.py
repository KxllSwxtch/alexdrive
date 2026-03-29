import re

from selectolax.lexbor import LexborHTMLParser


def parse_car_listings(html: str) -> list[dict]:
    """Parse car listings from salecars.co.kr search result page.

    Each listing is an <li> inside ul.ul-car-detail (or similar list),
    containing a link to /search/detail/{id}, image, name, specs, and price.
    """
    parser = LexborHTMLParser(html)
    listings: list[dict] = []

    for li in parser.css("li"):
        # Find link to detail page
        link = None
        for a in li.css("a[href]"):
            href = a.attributes.get("href", "")
            if "/search/detail/" in href:
                link = a
                break
        if not link:
            continue

        href = link.attributes.get("href", "")
        id_match = re.search(r"/search/detail/(\d+)", href)
        if not id_match:
            continue
        car_id = id_match.group(1)

        # Image — first img inside the detail link
        img = link.css_first("img")
        image_url = ""
        if img:
            # Try data-lazy first (slick lazy loading), then src
            image_url = img.attributes.get("data-lazy", "") or img.attributes.get("src", "")
        image_url = normalize_image_url(image_url)

        # Name — from button or link text containing [Maker]Model
        name = ""
        name_btn = li.css_first("button")
        if name_btn:
            name_link = name_btn.css_first("a")
            if name_link:
                name = name_link.text(strip=True)
            else:
                name = name_btn.text(strip=True)

        if not name:
            continue

        # Specs list — <ul> with <li> items: year, mileage, fuel, color
        year = ""
        mileage = ""
        fuel = ""
        color = ""
        spec_items = []
        for ul in li.css("ul"):
            items = ul.css("li")
            texts = [item.text(strip=True) for item in items if item.text(strip=True)]
            # The specs list typically has 3-4 items (year, mileage, fuel, color)
            if len(texts) >= 3 and re.match(r"\d{4}-\d{2}", texts[0]):
                spec_items = texts
                break

        if spec_items:
            year = spec_items[0] if len(spec_items) > 0 else ""
            mileage = spec_items[1] if len(spec_items) > 1 else ""
            fuel = spec_items[2] if len(spec_items) > 2 else ""
            color = spec_items[3] if len(spec_items) > 3 else ""

        # Price — look for text matching 만원 pattern (check all elements)
        price = ""
        for el in li.css("div, span, p, strong"):
            text = el.text(strip=True)
            # Match price like "4,270만원" but not monthly payment "월 51만원"
            if text and re.match(r"^[\d,]+만원$", text):
                price = text
                break

        listings.append({
            "id": car_id,
            "imageUrl": image_url,
            "name": name,
            "year": year,
            "mileage": mileage,
            "fuel": fuel,
            "transmission": "",  # not shown in listing cards
            "price": price,
            "color": color,
            "location": "",
            "dealer": "",
            "phone": "",
        })

    return listings


def parse_total_count(html: str) -> int:
    """Extract total count from '전체 49,659대' text or pagination."""
    # Try direct text match first
    match = re.search(r"전체\s*([\d,]+)\s*대", html)
    if match:
        return int(match.group(1).replace(",", ""))

    # Fallback: estimate from last pagination page link
    # Pattern: /search/model/.../2069?... (last page number)
    pages = re.findall(r'/search/model/\w+/(\d+)\?', html)
    if pages:
        last_page = max(int(p) for p in pages)
        # Extract customSelect (items per page) from URL
        per_page_match = re.search(r'customSelect=(\d+)', html)
        per_page = int(per_page_match.group(1)) if per_page_match else 24
        return last_page * per_page

    return 0


def normalize_image_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/"):
        return f"https://www.salecars.co.kr{url}"
    return url
