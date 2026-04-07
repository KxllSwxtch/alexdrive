import re

from selectolax.lexbor import LexborHTMLParser


# Dark SVG placeholder matching the site's dark theme
BLUR_PLACEHOLDER = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjE2IiBoZWlnaHQ9IjEwIiBmaWxsPSIjMWExYTFhIi8+PC9zdmc+"


def parse_car_detail(html: str, car_id: str) -> dict:
    """Parse a salecars.co.kr detail page.

    Structure:
    - .car_name → car name
    - .car_price → price
    - table (first, no class) → specs rows (th/td pairs)
    - table.type02 → seller info
    - .slick-slide img / .img_box img → gallery images
    - input[type='checkbox'][checked] + label → options
    """
    parser = LexborHTMLParser(html)

    # Name — from .car_name or first <p> with bracket notation
    name = ""
    name_el = parser.css_first(".car_name p")
    if name_el:
        name = name_el.text(strip=True)
    if not name:
        name_el = parser.css_first(".car_name")
        if name_el:
            name = name_el.text(strip=True)
    # Strip surrounding quotes if present
    name = name.strip('"').strip("'")

    # Price — from .car_price
    price = ""
    price_el = parser.css_first(".car_price")
    if price_el:
        price_text = price_el.text(strip=True)
        # Extract "1,800만원" from "판매가 1,800만원"
        m = re.search(r"([\d,]+\s*만원)", price_text)
        if m:
            price = m.group(1)

    # Images — from gallery slider
    images: list[str] = []
    seen = set()
    for img in parser.css(".slick-slide img, .img_box img, .car-img-slider img"):
        src = img.attributes.get("data-lazy", "") or img.attributes.get("src", "")
        src = normalize_image_url(src)
        if not src or "noimage" in src or "xbox" in src or "sblank" in src or "_TH." in src:
            continue
        if src not in seen:
            seen.add(src)
            images.append(src)

    # Specs from first table (no class or unnamed class)
    specs = _extract_specs(parser)

    # Options — checked checkboxes with adjacent labels
    options = _extract_options(parser)

    # Inspection URL — from script or performance report button link
    inspection_url = None
    m = re.search(r"var\s+carcheckoutUrl\s*=\s*'([^']*)'", html)
    if m and m.group(1).strip():
        inspection_url = m.group(1).strip()
        inspection_url = re.sub(r"([?&])print=\d+", r"\1print=0", inspection_url)

    # Also check for autocafe link in onclick handlers
    if not inspection_url:
        m = re.search(r"(https?://[^\s'\"]*autocafe\.co\.kr[^\s'\"]*)", html)
        if m:
            inspection_url = m.group(1)

    return {
        "id": car_id,
        "name": name,
        "images": images,
        "year": specs.get("year", ""),
        "mileage": specs.get("mileage", ""),
        "fuel": specs.get("fuel", ""),
        "transmission": specs.get("transmission", ""),
        "price": price,
        "color": specs.get("color", ""),
        "engineCapacity": "",
        "carNumber": specs.get("carNumber", ""),
        "location": _extract_location(parser) or specs.get("location", ""),
        "options": options,
        "dealer": "",  # suppressed — keep AlexDrive's own contacts
        "phone": "",   # suppressed
        "registrationDate": specs.get("registrationDate", ""),
        "modelYear": specs.get("year", ""),
        "inspectionUrl": inspection_url,
        "blurDataUrl": BLUR_PLACEHOLDER if images else None,
    }


def _extract_location(parser) -> str:
    """Extract location from 판매방식 tooltip, e.g. '(주)건우(안산)' → '안산'."""
    tooltip = parser.css_first("span.tooltip-box")
    if tooltip:
        text = tooltip.text(strip=True)
        # Extract region from last parentheses: "(주)건우(안산)" → "안산"
        match = re.search(r"\(([^)]+)\)\s*$", text)
        if match:
            return match.group(1)
    return ""


def _extract_specs(parser) -> dict:
    """Extract specs from the detail page tables.

    salecars uses tables with th/td pairs per row:
    - 연식 / 최초등록일
    - 연료 / 변속기
    - 색상 / 주행거리
    - 차량번호 / 차대번호
    """
    specs: dict[str, str] = {}

    for table in parser.css("table"):
        # Skip seller info table (class=type02)
        if table.attributes.get("class", "") == "type02":
            continue

        for tr in table.css("tr"):
            ths = tr.css("th")
            tds = tr.css("td")

            for i, th in enumerate(ths):
                if i >= len(tds):
                    break
                label = th.text(strip=True)
                value = re.sub(r"\s+", " ", tds[i].text(strip=True))

                if label == "연식":
                    specs["year"] = value
                elif label == "최초등록일":
                    specs["registrationDate"] = value
                elif label == "연료":
                    specs["fuel"] = value
                elif label == "변속기":
                    specs["transmission"] = value
                elif label == "색상":
                    specs["color"] = value
                elif label == "주행거리":
                    specs["mileage"] = value
                elif label == "차량번호":
                    specs["carNumber"] = value
                elif label == "주차위치":
                    specs["location"] = value

    return specs


def _extract_options(parser) -> list[dict]:
    """Extract car options from checked checkboxes with labels."""
    items: list[str] = []

    for checkbox in parser.css("input[type='checkbox'][checked]"):
        sibling = checkbox.next
        if sibling and sibling.tag == "label":
            text = sibling.text(strip=True)
            # Skip consent checkbox
            if text and "개인정보" not in text and "동의" not in text:
                items.append(text)

    if items:
        return [{"group": "옵션", "items": items}]
    return []


def normalize_image_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/"):
        return f"https://www.salecars.co.kr{url}"
    return url
