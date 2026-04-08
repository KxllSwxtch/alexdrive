import re

from selectolax.lexbor import LexborHTMLParser

from app.config import settings


def parse_car_listings(html: str) -> list[dict]:
    """Parse car listings from chasainmotors.com search result page.

    Each listing is a <tr> with td.car-detail, containing a link to
    /search/detail/{id}, images, name, specs (year, mileage, fuel, transmission),
    and price.
    """
    parser = LexborHTMLParser(html)
    listings: list[dict] = []

    for tr in parser.css("tr"):
        # Find link to detail page
        link = None
        for a in tr.css("a[href]"):
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

        # Name — from span.name > a
        name = ""
        name_el = tr.css_first("span.name a")
        if name_el:
            name = name_el.text(strip=True)
        if not name:
            continue

        # Specs list — ul.car-option with 4 <li>: year, mileage, fuel, transmission
        year = ""
        mileage = ""
        fuel = ""
        transmission = ""
        spec_ul = tr.css_first("ul.car-option")
        if spec_ul:
            spec_items = [li.text(strip=True) for li in spec_ul.css("li") if li.text(strip=True)]
            if len(spec_items) >= 1:
                year = spec_items[0]
            if len(spec_items) >= 2:
                mileage = spec_items[1]
            if len(spec_items) >= 3:
                fuel = spec_items[2]
            if len(spec_items) >= 4:
                transmission = spec_items[3]

        # Price — from span.car_pay (number only, e.g. "1,370")
        price = ""
        price_el = tr.css_first("span.car_pay")
        if price_el:
            num_text = price_el.text(strip=True)
            if num_text:
                price = f"{num_text}만원"

        # Image — first img in div.img-wrap
        image_url = ""
        img_el = tr.css_first("div.img-wrap img")
        if img_el:
            image_url = img_el.attributes.get("src", "")
        image_url = normalize_image_url(image_url)

        listings.append({
            "id": car_id,
            "imageUrl": image_url,
            "name": name,
            "year": year,
            "mileage": mileage,
            "fuel": fuel,
            "transmission": transmission,
            "price": price,
            "color": "",
            "location": "",
            "dealer": "",
            "phone": "",
        })

    return listings


def parse_total_count(html: str) -> int:
    """Extract total count from '전체 49,659대' text or pagination."""
    parser = LexborHTMLParser(html)

    # Primary: extract text (strips inner tags like <span>), then regex
    body = parser.body
    if body:
        body_text = body.text()
        match = re.search(r"전체\s*([\d,]+)\s*대", body_text)
        if match:
            return int(match.group(1).replace(",", ""))

    # Fallback: estimate from last pagination page link
    pages = re.findall(r'/search/model/\w+/(\d+)\?', html)
    if pages:
        last_page = max(int(p) for p in pages)
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
        return f"{settings.source_base_url}{url}"
    return url
