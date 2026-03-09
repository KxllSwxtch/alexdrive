import re

from bs4 import BeautifulSoup


def parse_car_detail(html: str, encrypted_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    name_el = soup.find(id="ui_ViewCarName")
    if name_el:
        name = name_el.get_text(strip=True)
    else:
        tit_h2 = soup.select_one(".uc_cardetail .tit h2")
        name = tit_h2.get_text(strip=True) if tit_h2 else ""

    images: list[str] = []
    for a in soup.find_all("a", class_="img_box"):
        imgs = a.find_all("img")
        full_img = imgs[1] if len(imgs) > 1 else imgs[0] if imgs else None
        if full_img:
            src = full_img.get("src", "")
            if src and "noimage" not in src and "sblank" not in src:
                images.append(normalize_image_url(src))

    spec_table = soup.find("table", class_="car_info_201210")
    specs = extract_specs_from_table(spec_table) if spec_table else {}

    price_el = soup.find(id="ui_ViewCarAmount")
    price = price_el.get_text(strip=True) if price_el else ""

    options = extract_options(soup)

    return {
        "encryptedId": encrypted_id,
        "name": name,
        "images": images,
        "year": specs.get("year", ""),
        "mileage": specs.get("mileage", ""),
        "fuel": specs.get("fuel", ""),
        "transmission": specs.get("transmission", ""),
        "price": price,
        "color": specs.get("color", ""),
        "engineCapacity": specs.get("engineCapacity", ""),
        "carNumber": specs.get("carNumber", ""),
        "location": specs.get("location", ""),
        "options": options,
        "dealer": specs.get("dealer", ""),
        "phone": specs.get("phone", ""),
        "registrationDate": specs.get("registrationDate", ""),
        "modelYear": specs.get("modelYear", ""),
    }


def extract_specs_from_table(table) -> dict:
    specs = {
        "year": "",
        "mileage": "",
        "fuel": "",
        "transmission": "",
        "color": "",
        "engineCapacity": "",
        "carNumber": "",
        "location": "",
        "dealer": "",
        "phone": "",
        "registrationDate": "",
        "modelYear": "",
    }

    for tr in table.find_all("tr"):
        ths = tr.find_all("th")
        tds = tr.find_all("td")

        for i, th in enumerate(ths):
            if i >= len(tds):
                break
            label = th.get_text(strip=True)
            td = tds[i]
            value = re.sub(r"\s+", " ", td.get_text(strip=True))

            if label == "차량번호":
                plate_input = td.find("input", id="carplatenoCopy")
                specs["carNumber"] = plate_input.get("value", "") if plate_input else value
            elif label == "주행거리":
                specs["mileage"] = value
            elif label == "미션":
                specs["transmission"] = value
            elif label == "연형":
                year_match = re.search(r"(\d{4})\s*년", value)
                if year_match:
                    specs["modelYear"] = year_match.group(1)
                reg_match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", value)
                if reg_match:
                    specs["registrationDate"] = reg_match.group(1)
            elif label == "연료":
                specs["fuel"] = value
            elif label == "색상":
                specs["color"] = value
            elif label == "주차위치":
                specs["location"] = value
            elif label == "담당사원":
                phones = re.findall(r"\d{2,4}-\d{3,4}-\d{4}", value)
                if phones:
                    specs["phone"] = phones[-1]
                for span in td.find_all("span"):
                    text = span.get_text(strip=True)
                    if text and "-" not in text and "(" not in text and "증번호" not in text and len(text) < 10:
                        specs["dealer"] = text

    return specs


def extract_options(soup) -> list[dict]:
    option_groups: list[dict] = []

    for group in soup.find_all("div", class_="num01sub"):
        h4 = group.find("h4")
        group_name = h4.get_text(strip=True) if h4 else ""
        if not group_name:
            continue

        items: list[str] = []
        for el in group.select("input[type='checkbox'][checked]"):
            label = el.find_next_sibling("label")
            if label:
                text = label.get_text(strip=True)
                if text:
                    items.append(text)

        if items:
            option_groups.append({"group": group_name, "items": items})

    return option_groups


def normalize_image_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/"):
        return f"https://www.carmanager.co.kr{url}"
    return url
