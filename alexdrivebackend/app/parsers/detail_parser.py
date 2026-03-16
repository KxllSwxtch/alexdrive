import re

from selectolax.lexbor import LexborHTMLParser


# Dark SVG placeholder matching the site's dark theme
BLUR_PLACEHOLDER = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjE2IiBoZWlnaHQ9IjEwIiBmaWxsPSIjMWExYTFhIi8+PC9zdmc+"


def parse_car_detail(html: str, seq_id: str) -> dict:
    """Parse car detail from jenya detail page HTML."""
    parser = LexborHTMLParser(html)

    # Name — look for car name in various locations
    name = ""
    # Try common patterns for mobile car detail pages
    for selector in [
        "div.car_name", "h1", "h2", ".carname", ".car_title",
        "div.detail_title", ".tit_detail",
    ]:
        el = parser.css_first(selector)
        if el:
            text = el.text(strip=True)
            if text and len(text) > 3:
                name = text
                break

    # If no name found, try the page title
    if not name:
        title_el = parser.css_first("title")
        if title_el:
            title_text = title_el.text(strip=True)
            # Remove site name from title
            name = re.sub(r"\s*[-|].*$", "", title_text).strip()

    # Price
    price = ""
    for selector in [
        "div.car_price", ".price", "strong.price", ".detail_price",
        "div.money",
    ]:
        el = parser.css_first(selector)
        if el:
            text = el.text(strip=True)
            if text and any(c.isdigit() for c in text):
                price = text.lstrip("\\").strip()
                break

    # If still no price, search for price pattern in text
    if not price:
        price_match = re.search(r"\\?([\d,]+,\d{3})\s*원?", html)
        if price_match:
            price = price_match.group(1)

    # Specs — look for table or definition list with Russian labels
    specs = _extract_specs(parser, html)

    # Images — from swiper slides with background-image
    images: list[str] = []
    for slide in parser.css(".swiper-slide"):
        style = slide.attributes.get("style", "")
        bg_match = re.search(r"background-image:\s*url\(([^)]+)\)", style)
        if bg_match:
            img_url = bg_match.group(1).strip("'\"")
            # Only keep car_large images (not car_small thumbnails)
            if "car_small" not in img_url and img_url:
                if not img_url.startswith("http"):
                    img_url = f"https:{img_url}" if img_url.startswith("//") else img_url
                images.append(img_url)

    # Also check for regular img tags in swiper or gallery
    if not images:
        for img in parser.css(".swiper-slide img, .gallery img, .detail_img img"):
            src = img.attributes.get("src", "")
            if src and "car_large" in src:
                if not src.startswith("http"):
                    src = f"https:{src}" if src.startswith("//") else src
                images.append(src)

    # Also find images from any img tags with autosale.co.kr
    if not images:
        for img in parser.css("img"):
            src = img.attributes.get("src", "")
            if src and "autosale.co.kr" in src and "car_large" in src:
                if not src.startswith("http"):
                    src = f"https:{src}" if src.startswith("//") else src
                images.append(src)

    # Options — flat list of li items
    option_items: list[str] = []
    # Look for options section
    for selector in ["ul.option_list li", ".car_option li", ".option li"]:
        for li in parser.css(selector):
            text = li.text(strip=True)
            if text:
                option_items.append(text)
        if option_items:
            break

    # If no structured options found, try finding checkmarks or checked items
    if not option_items:
        for li in parser.css("li"):
            cls = li.attributes.get("class", "")
            if "on" in cls or "check" in cls or "active" in cls:
                text = li.text(strip=True)
                if text and len(text) > 1:
                    option_items.append(text)

    options = [{"group": "Опции", "items": option_items}] if option_items else []

    # Diagnostics URL
    diagnostics_url = None
    for button in parser.css("button, a"):
        onclick = button.attributes.get("onclick", "")
        href = button.attributes.get("href", "")
        for target in [onclick, href]:
            diag_match = re.search(r"(https?://photo5\.autosale\.co\.kr/safe\.php\?[^'\")\s]+)", target)
            if diag_match:
                diagnostics_url = diag_match.group(1)
                break
        if diagnostics_url:
            break

    # If not found in buttons, search in full HTML
    if not diagnostics_url:
        diag_match = re.search(r"(https?://photo5\.autosale\.co\.kr/safe\.php\?seq=\d+[^'\")\s]*)", html)
        if diag_match:
            diagnostics_url = diag_match.group(1)

    # Dealer info — look for dealer/contact sections
    dealer = specs.get("dealer", "")
    phone = specs.get("phone", "")

    return {
        "encryptedId": seq_id,
        "name": name,
        "images": images,
        "year": specs.get("year", ""),
        "mileage": specs.get("mileage", ""),
        "fuel": specs.get("fuel", ""),
        "transmission": specs.get("transmission", ""),
        "price": price,
        "color": specs.get("color", ""),
        "carNumber": specs.get("carNumber", ""),
        "options": options,
        "dealer": dealer,
        "phone": phone,
        "diagnosticsUrl": diagnostics_url,
        "blurDataUrl": BLUR_PLACEHOLDER if images else None,
    }


def _extract_specs(parser, html: str) -> dict:
    """Extract specs from jenya detail page — uses Russian labels."""
    specs = {
        "year": "",
        "mileage": "",
        "fuel": "",
        "transmission": "",
        "color": "",
        "carNumber": "",
        "dealer": "",
        "phone": "",
    }

    # Try table-based specs (th/td pairs)
    for table in parser.css("table"):
        for tr in table.css("tr"):
            ths = tr.css("th")
            tds = tr.css("td")
            for i, th in enumerate(ths):
                if i >= len(tds):
                    break
                label = th.text(strip=True).lower()
                value = re.sub(r"\s+", " ", tds[i].text(strip=True))
                _assign_spec(specs, label, value)

            # Also handle single-column rows with dt/dd-like structure
            if not ths:
                text = tr.text(strip=True)
                _try_parse_spec_text(specs, text)

    # Try dt/dd pairs
    for dt in parser.css("dt"):
        dd = dt.next
        if dd and dd.tag == "dd":
            label = dt.text(strip=True).lower()
            value = re.sub(r"\s+", " ", dd.text(strip=True))
            _assign_spec(specs, label, value)

    # Try div-based spec lists
    for div in parser.css("div"):
        text = div.text(strip=True)
        if not text:
            continue
        # Look for label:value patterns
        for line in text.split("\n"):
            _try_parse_spec_text(specs, line.strip())

    return specs


def _assign_spec(specs: dict, label: str, value: str) -> None:
    """Assign a spec value based on Russian/Korean label."""
    if not value:
        return

    label = label.strip().rstrip(":")

    if label in ("год выпуска", "год", "연식"):
        specs["year"] = value
    elif label in ("цвет", "색상"):
        specs["color"] = value
    elif label in ("топливо", "연료"):
        specs["fuel"] = value
    elif label in ("коробка", "коробка передач", "кпп", "미션"):
        specs["transmission"] = value
    elif label in ("пробег", "주행거리"):
        specs["mileage"] = value
    elif label in ("номер авто", "номер", "차량번호"):
        specs["carNumber"] = value
    elif label in ("автодилер", "дилер", "담당사원"):
        specs["dealer"] = value
    elif label in ("контакты", "телефон", "연락처"):
        specs["phone"] = value


def _try_parse_spec_text(specs: dict, text: str) -> None:
    """Try to extract a spec from a text line with label:value format."""
    if ":" not in text and "：" not in text:
        return
    parts = re.split(r"[:：]", text, maxsplit=1)
    if len(parts) == 2:
        label = parts[0].strip().lower()
        value = parts[1].strip()
        _assign_spec(specs, label, value)
