import re

from selectolax.lexbor import LexborHTMLParser


# Dark SVG placeholder matching the site's dark theme — zero-latency, no network fetch
BLUR_PLACEHOLDER = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjE2IiBoZWlnaHQ9IjEwIiBmaWxsPSIjMWExYTFhIi8+PC9zdmc+"


def parse_car_detail(html: str, encrypted_id: str) -> dict:
    parser = LexborHTMLParser(html)

    name_el = parser.css_first("#ui_ViewCarName")
    if name_el:
        name = name_el.text(strip=True)
    else:
        tit_h2 = parser.css_first(".uc_cardetail .tit h2")
        name = tit_h2.text(strip=True) if tit_h2 else ""

    images: list[str] = []
    for a in parser.css("a.img_box"):
        imgs = a.css("img")
        full_img = imgs[1] if len(imgs) > 1 else imgs[0] if imgs else None
        if full_img:
            src = full_img.attributes.get("src", "")
            if src and "noimage" not in src and "sblank" not in src:
                images.append(normalize_image_url(src))

    spec_table = parser.css_first("table.car_info_201210")
    specs = extract_specs_from_table(spec_table) if spec_table else {}

    price_el = parser.css_first("#ui_ViewCarAmount")
    price = price_el.text(strip=True) if price_el else ""

    options = extract_options(parser)

    # Extract inspection report URL from script tags
    inspection_url = None
    m = re.search(r"var\s+carcheckoutUrl\s*=\s*'([^']*)'", html)
    if m and m.group(1).strip():
        inspection_url = m.group(1).strip()
        # Open report in view mode, not print mode
        inspection_url = re.sub(r"([?&])print=\d+", r"\1print=0", inspection_url)

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
        "inspectionUrl": inspection_url,
        "blurDataUrl": BLUR_PLACEHOLDER if images else None,
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

    for tr in table.css("tr"):
        ths = tr.css("th")
        tds = tr.css("td")

        for i, th in enumerate(ths):
            if i >= len(tds):
                break
            label = th.text(strip=True)
            td = tds[i]
            value = re.sub(r"\s+", " ", td.text(strip=True))

            if label == "차량번호":
                plate_input = td.css_first("input#carplatenoCopy")
                specs["carNumber"] = plate_input.attributes.get("value", "") if plate_input else value
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
                for span in td.css("span"):
                    text = span.text(strip=True)
                    if text and "-" not in text and "(" not in text and "증번호" not in text and len(text) < 10:
                        specs["dealer"] = text

    return specs


def extract_options(parser) -> list[dict]:
    option_groups: list[dict] = []

    for group in parser.css("div.num01sub"):
        h4 = group.css_first("h4")
        group_name = h4.text(strip=True) if h4 else ""
        if not group_name:
            continue

        items: list[str] = []
        for checkbox in group.css("input[type='checkbox'][checked]"):
            # selectolax doesn't have find_next_sibling — use .next to get adjacent label
            sibling = checkbox.next
            if sibling and sibling.tag == "label":
                text = sibling.text(strip=True)
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
