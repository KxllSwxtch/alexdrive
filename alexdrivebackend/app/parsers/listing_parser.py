import re

from selectolax.lexbor import LexborHTMLParser


def parse_car_listings(html: str) -> list[dict]:
    """Parse car listings from jenya listing page HTML."""
    parser = LexborHTMLParser(html)
    listings: list[dict] = []

    # Find all listing links: <a href="/?m=sale&s=detail&seq=XXXXXXXXXX">
    for li in parser.css("ul li"):
        link = li.css_first("a[href]")
        if not link:
            continue
        href = link.attributes.get("href", "")
        seq_match = re.search(r"[?&]seq=(\d+)", href)
        if not seq_match:
            continue
        seq_id = seq_match.group(1)

        # Image
        img = li.css_first("img")
        image_url = img.attributes.get("src", "") if img else ""

        # Name from .carinfo span
        carinfo = li.css_first("span.carinfo, .carinfo")
        name = carinfo.text(strip=True) if carinfo else ""

        # Info line: "2015/08 | 109000km | Автоматическая коробка передач | Бензин"
        year = ""
        mileage = ""
        transmission = ""
        fuel = ""

        # Find the info span (second span in carmemo, or span without class)
        carmemo = li.css_first("div.carmemo, .carmemo")
        if carmemo:
            spans = carmemo.css("span")
            for span in spans:
                text = span.text(strip=True)
                if not text:
                    continue
                # Skip the carinfo span (already got name from it)
                span_class = span.attributes.get("class", "")
                if "carinfo" in span_class:
                    continue
                # Parse pipe-delimited info
                if "|" in text:
                    parts = [p.strip() for p in text.split("|")]
                    if len(parts) >= 1:
                        year = parts[0]
                    if len(parts) >= 2:
                        mileage = parts[1]
                    if len(parts) >= 3:
                        transmission = parts[2]
                    if len(parts) >= 4:
                        fuel = parts[3]

        # Price from <strong>
        price_el = li.css_first("strong")
        price = ""
        if price_el:
            price_text = price_el.text(strip=True)
            # Strip leading backslash if present (jenya uses \9,290,000 format)
            price = price_text.lstrip("\\").strip()

        listings.append({
            "encryptedId": seq_id,
            "imageUrl": image_url,
            "name": name,
            "year": year,
            "mileage": mileage,
            "fuel": fuel,
            "transmission": transmission,
            "price": price,
            "dealer": "",
            "phone": "",
        })

    return listings


def parse_pagination(html: str) -> dict:
    """Parse pagination info from jenya listing HTML.

    Returns {"max_visible_page": int, "has_next": bool}
    """
    # Find page links: javascript:page('N')
    page_numbers = [int(m) for m in re.findall(r"javascript:page\('(\d+)'\)", html)]

    # Also check for current page (may be shown without javascript: link)
    # Look for <b> or <strong> or active class with page number
    current_match = re.findall(r'class="[^"]*on[^"]*"[^>]*>(\d+)<', html)
    for m in current_match:
        page_numbers.append(int(m))

    if not page_numbers:
        return {"max_visible_page": 1, "has_next": False}

    max_page = max(page_numbers)

    # Check if there's a "next" link (▶ or > or 다음)
    has_next = bool(re.search(r"javascript:page\('\d+'\)[^>]*>[▶>»]|다음|next", html, re.IGNORECASE))

    return {"max_visible_page": max_page, "has_next": has_next}


def estimate_total(pagination: dict, page_size: int = 20) -> int:
    """Estimate total count from pagination info."""
    max_page = pagination["max_visible_page"]
    has_next = pagination["has_next"]

    if has_next:
        # There are more pages beyond what's visible
        return max_page * page_size + 1
    else:
        # Last visible page is the last page
        return max_page * page_size
