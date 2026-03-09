import re

from bs4 import BeautifulSoup


def parse_car_listings(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    listings: list[dict] = []

    for row in soup.find_all("tr", class_="uc_carcss"):
        link = row.find("a", href=lambda h: h and "carmangerDetailWindowPopUp_CHECK" in h)
        if not link:
            continue
        href = link.get("href", "")
        enc_match = re.search(r"carmangerDetailWindowPopUp_CHECK\('([^']+)'\)", href)
        if not enc_match:
            continue
        encrypted_id = enc_match.group(1)

        img = row.find("img", class_="thumbnail")
        image_url = img.get("src", "") if img else ""

        name_cell = row.find("td", class_="uc_textleft")
        maker = ""
        model = ""
        if name_cell:
            maker_label = name_cell.find("label", class_="uc_carmaker")
            if maker_label:
                maker = maker_label.get_text(strip=True)
            model_link = name_cell.select_one("span > a")
            if model_link:
                model = model_link.get_text(strip=True)
        name = f"{maker} {model}".strip()

        cells = row.find_all("td")
        transmission = ""
        year = ""
        model_year = ""
        fuel = ""

        for td in cells:
            first_p = td.find("p")
            if first_p:
                p_text = first_p.get_text(strip=True)
                if p_text and re.search(r"오토|수동|세미오토|무단변속", p_text) and not transmission:
                    transmission = p_text

            reg_span = td.find("span", class_="uc_carreg")
            if reg_span:
                reg_text = reg_span.get_text(strip=True)
                if reg_text and not year:
                    year = reg_text

            year_span = td.find("span", class_="uc_carreg_year")
            if year_span:
                year_text = year_span.get_text(strip=True)
                if year_text and year_text.startswith("[") and not model_year:
                    model_year = year_text.strip("[]")

        for td in cells:
            text = td.get_text(strip=True)
            td_class = td.get("class")
            if not td_class and re.match(r"^(휘발유|경유|LPG|전기|하이브리드|CNG|수소)", text) and not fuel:
                fuel = text

        mileage_td = row.find("td", class_="uc_carusekm")
        mileage = mileage_td.get_text(strip=True) if mileage_td else ""

        price_b = row.find("b", class_="uc_caramount")
        price = price_b.get_text(strip=True) if price_b else ""

        area_td = row.find("td", class_="uc_cararea")
        location = re.sub(r"\s+", " ", area_td.get_text(strip=True)) if area_td else ""

        dealer_span = row.find("span", class_="uc_cardealer")
        dealer = dealer_span.get_text(strip=True) if dealer_span else ""

        phone_span = row.find("span", class_="uc_cardealer_phone")
        phone = phone_span.get_text(strip=True) if phone_span else ""

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
    match = re.search(r'id="hdfCarRowCount"[^>]*value="(\d+)"', html)
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
