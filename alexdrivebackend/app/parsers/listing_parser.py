import re

from selectolax.lexbor import LexborHTMLParser


def parse_car_listings(html: str) -> list[dict]:
    parser = LexborHTMLParser(html)
    listings: list[dict] = []

    for row in parser.css("tr.uc_carcss"):
        # Find link with encrypted ID
        link = None
        for a in row.css("a[href]"):
            href = a.attributes.get("href", "")
            if "carmangerDetailWindowPopUp_CHECK" in href:
                link = a
                break
        if not link:
            continue
        href = link.attributes.get("href", "")
        enc_match = re.search(r"carmangerDetailWindowPopUp_CHECK\('([^']+)'\)", href)
        if not enc_match:
            continue
        encrypted_id = enc_match.group(1)

        img = row.css_first("img.thumbnail")
        image_url = img.attributes.get("src", "") if img else ""

        name_cell = row.css_first("td.uc_textleft")
        maker = ""
        model = ""
        if name_cell:
            maker_label = name_cell.css_first("label.uc_carmaker")
            if maker_label:
                maker = maker_label.text(strip=True)
            model_link = name_cell.css_first("span > a")
            if model_link:
                model = model_link.text(strip=True)
        name = f"{maker} {model}".strip()

        cells = row.css("td")
        transmission = ""
        year = ""
        model_year = ""
        fuel = ""

        for td in cells:
            first_p = td.css_first("p")
            if first_p:
                p_text = first_p.text(strip=True)
                if p_text and re.search(r"오토|수동|세미오토|무단변속", p_text) and not transmission:
                    transmission = p_text

            reg_span = td.css_first("span.uc_carreg")
            if reg_span:
                reg_text = reg_span.text(strip=True)
                if reg_text and not year:
                    year = reg_text

            year_span = td.css_first("span.uc_carreg_year")
            if year_span:
                year_text = year_span.text(strip=True)
                if year_text and year_text.startswith("[") and not model_year:
                    model_year = year_text.strip("[]")

        for td in cells:
            text = td.text(strip=True)
            td_class = td.attributes.get("class")
            if not td_class and re.match(r"^(휘발유|경유|LPG|전기|하이브리드|CNG|수소)", text) and not fuel:
                fuel = text

        mileage_td = row.css_first("td.uc_carusekm")
        mileage = mileage_td.text(strip=True) if mileage_td else ""

        price_b = row.css_first("b.uc_caramount")
        price = price_b.text(strip=True) if price_b else ""

        area_td = row.css_first("td.uc_cararea")
        location = re.sub(r"\s+", " ", area_td.text(strip=True)) if area_td else ""

        dealer_span = row.css_first("span.uc_cardealer")
        dealer = dealer_span.text(strip=True) if dealer_span else ""

        phone_span = row.css_first("span.uc_cardealer_phone")
        phone = phone_span.text(strip=True) if phone_span else ""

        display_year = f"{year} [{model_year}]" if model_year else year

        listings.append({
            "encryptedId": encrypted_id,
            "imageUrl": normalize_image_url(image_url),
            "name": name,
            "year": display_year,
            "mileage": mileage,
            "fuel": fuel,
            "transmission": transmission,
            "price": price,
            "location": location,
            "dealer": dealer,
            "phone": phone,
        })

    return listings


def parse_total_count(html: str) -> int:
    # Format 1: hidden input (from /Car/Data full page)
    match = re.search(r'id="hdfCarRowCount"[^>]*value="(\d+)"', html)
    if match:
        return int(match.group(1))
    # Format 2: jQuery .val() call (from /Car/DataPart)
    match = re.search(r'hdfCarRowCount.*?\.val\([\'"](\d+)[\'"]\)', html)
    if match:
        return int(match.group(1))
    # Format 3: reLoadPage first argument
    match = re.search(r"reLoadPage\(['\"](\d+)['\"]", html)
    if match:
        return int(match.group(1))
    return 0


def normalize_image_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/"):
        return f"https://www.carmanager.co.kr{url}"
    return url
