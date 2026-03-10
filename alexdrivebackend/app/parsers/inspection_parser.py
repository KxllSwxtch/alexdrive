import json
import re

from selectolax.lexbor import LexborHTMLParser

# Basic condition codes (bc)
BC_CODES = {
    "2": "gaugeStatus",      # 1=양호, 2=불량
    "3": "vinMarking",       # 1=양호, 2=부식, 3=훼손, 4=상이, 5=변조, 6=도말
    "4": "emissions",        # 1=적합, 2=부적합
    "5": "tuning",           # 1=없음, 2=있음
    "11": "flood",           # 1=없음, 2=있음
    "12": "fire",            # 1=없음, 2=있음, 3=모름
    "81": "warrantyType",    # 1=자가보증, 2=보험사보증
}

BC_VALUES = {
    "gaugeStatus": {"1": "good", "2": "bad"},
    "vinMarking": {"1": "good", "2": "corrosion", "3": "damaged", "4": "different", "5": "forged", "6": "erased"},
    "emissions": {"1": "pass", "2": "fail"},
    "tuning": {"1": "none", "2": "exists"},
    "flood": {"1": "none", "2": "exists"},
    "fire": {"1": "none", "2": "exists", "3": "unknown"},
    "warrantyType": {"1": "self", "2": "insurance"},
}

# Accident/maintenance codes (mac)
MAC_CODES = {
    "11": "accidentHistory",  # 1=없음, 2=있음
    "12": "simpleRepair",     # 1=없음, 2=있음
    "21": "repairStatus",
}

# Detailed condition codes (dc) - grouped by system
DC_CODES = {
    "11": ("engine", "oilLeakRockerArm"),
    "12": ("engine", "oilLeakCylinderHead"),
    "21": ("engine", "coolantLeak"),
    "23": ("engine", "idleCondition"),
    "24": ("engine", "exhaustSystem"),
    "41": ("transmission", "oilLeak"),
    "42": ("transmission", "oilLevelCondition"),
    "43": ("transmission", "idleGearShift"),
    "44": ("transmission", "drivePowerShift"),
    "51": ("power", "clutchAssembly"),
    "61": ("electrical", "generatorOutput"),
    "62": ("electrical", "starterMotor"),
    "63": ("electrical", "wiperMotor"),
    "71": ("electrical", "lights"),
    "72": ("electrical", "windowOperation"),
    "73": ("electrical", "interiorElectrics"),
    "74": ("electrical", "acSystem"),
    "75": ("electrical", "heater"),
    "76": ("electrical", "defroster"),
    "81": ("fuel", "fuelLeak"),
    "91": ("tires", "tireFrontLeft"),
    "92": ("tires", "tireFrontRight"),
    "93": ("tires", "tireRearLeft"),
    "94": ("tires", "tireRearRight"),
}

DC_VALUES = {"0": "unable", "1": "good", "2": "bad"}

# Body zone names (for exterior/structural panels)
BODY_ZONES = {
    "1": "hood",
    "2": "frontFenderLeft",
    "3": "frontFenderRight",
    "4": "frontDoorLeft",
    "5": "frontDoorRight",
    "6": "rearDoorLeft",
    "7": "rearDoorRight",
    "8": "rearFenderLeft",
    "9": "rearFenderRight",
    "10": "trunk",
    "11": "roofPanel",
    "12": "frontBumper",
    "13": "rearBumper",
    "14": "sideSkirtLeft",
    "15": "sideSkirtRight",
    "16": "aPillarLeft",
    "17": "aPillarRight",
    "18": "bPillarLeft",
    "19": "bPillarRight",
}


def _extract_setdata(html: str) -> dict[str, dict]:
    """Extract setData('key', '{...}') calls from embedded JavaScript."""
    result = {}
    for match in re.finditer(r"setData\(\s*'(\w+)'\s*,\s*'(\{[^']*\})'\s*\)", html):
        key = match.group(1)
        try:
            result[key] = json.loads(match.group(2))
        except json.JSONDecodeError:
            pass
    return result


def _extract_js_var(html: str, var_name: str) -> dict:
    """Extract a JS variable assignment like: var name = '{...}';"""
    m = re.search(rf"var\s+{var_name}\s*=\s*'(\{{[^']*\}})'\s*;", html)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def _parse_basic_condition(bc_data: dict) -> dict:
    """Parse basic condition (bc) setData into structured fields."""
    result = {}
    for code, field in BC_CODES.items():
        raw = bc_data.get(code)
        value_map = BC_VALUES.get(field, {})
        result[field] = value_map.get(raw, raw) if raw else None
    return result


def _parse_accident_history(mac_data: dict) -> dict:
    """Parse accident/maintenance (mac) setData."""
    return {
        "exists": mac_data.get("11") == "2",
        "simpleRepair": mac_data.get("12") == "2",
    }


def _parse_detailed_condition(dc_data: dict) -> dict:
    """Parse detailed condition (dc) setData into grouped structure."""
    groups: dict[str, dict] = {}
    for code, (system, field) in DC_CODES.items():
        raw = dc_data.get(code)
        if system not in groups:
            groups[system] = {}
        groups[system][field] = DC_VALUES.get(raw, raw) if raw else None
    return groups


def _parse_body_damage(exterior: dict, structural: dict, diagram: dict) -> dict:
    """Parse body damage variables into structured format."""
    return {
        "exterior": {BODY_ZONES.get(k, k): v for k, v in exterior.items() if v},
        "structural": {BODY_ZONES.get(k, k): v for k, v in structural.items() if v},
        "diagram": {BODY_ZONES.get(k, k): v for k, v in diagram.items() if v},
    }


def parse_inspection_report(html: str) -> dict:
    """Parse carmodoo inspection report HTML into structured data."""
    parser = LexborHTMLParser(html)

    # 1. Extract JavaScript data (primary data source)
    setdata = _extract_setdata(html)
    bc_data = setdata.get("bc", {})
    mac_data = setdata.get("mac", {})
    dc_data = setdata.get("dc", {})

    uc_img_on = _extract_js_var(html, "ucImgOnCheck")
    uc_acc_out = _extract_js_var(html, "ucAccOutCheck")
    uc_acc_bone = _extract_js_var(html, "ucAccBoneCheck")

    # 2. Parse basic condition
    bc = _parse_basic_condition(bc_data)

    # 3. Parse HTML for text data
    # Document number
    doc_number = ""
    num_el = parser.css_first("span.num")
    if num_el:
        num_match = re.search(r"(\d+)", num_el.text(strip=True))
        if num_match:
            doc_number = num_match.group(1)

    # Mileage
    mileage_value = ""
    km_el = parser.css_first("strong.km")
    if km_el:
        mileage_value = km_el.text(strip=True).replace("Km", "").replace("km", "").strip()

    # Mileage trend (주행거리 상태)
    mileage_trend = ""
    m = re.search(r"setData\(\s*'ms'\s*,\s*'(\d+)'\s*\)", html)
    if m:
        trend_map = {"1": "low", "2": "normal", "3": "high"}
        mileage_trend = trend_map.get(m.group(1), "")

    # Emissions values from table
    co_value = ""
    hc_value = ""
    smoke_value = ""
    # Look for emission data in setData or HTML
    emissions_el = parser.css("td.ac")
    for el in emissions_el:
        text = el.text(strip=True)
        if "%" in text and not co_value:
            co_value = text
        elif "ppm" in text.lower() and not hc_value:
            hc_value = text

    # Warranty company
    warranty_company = ""
    warranty_premium = 0
    # Look for insurance company name in brackets like [신한EZ손해보험]
    bracket_match = re.search(r"\[([^\]]*(?:손해보험|보증보험)[^\]]*)\]", html)
    if bracket_match:
        warranty_company = bracket_match.group(1)
    else:
        for td in parser.css("td"):
            text = td.text(strip=True)
            if ("손해보험" in text or "보증보험" in text) and len(text) < 30:
                warranty_company = text
                break
    # Insurance premium
    price_el = parser.css_first("span.repair_price")
    if price_el:
        price_text = price_el.text(strip=True).replace(",", "").replace("원", "")
        try:
            warranty_premium = int(re.sub(r"[^\d]", "", price_text))
        except (ValueError, TypeError):
            pass

    # Inspector name and date
    inspector = ""
    inspection_date = ""
    # Date from HTML
    for td in parser.css("td"):
        text = td.text(strip=True)
        date_m = re.search(r"(\d{4})\s*[.년/-]\s*(\d{1,2})\s*[.월/-]\s*(\d{1,2})", text)
        if date_m and not inspection_date:
            inspection_date = f"{date_m.group(1)}-{date_m.group(2).zfill(2)}-{date_m.group(3).zfill(2)}"

    # Inspector from signature area
    for el in parser.css("span.sign_name, td.sign_name"):
        text = el.text(strip=True)
        if text and len(text) < 30:
            inspector = text
            break

    # If no inspector from span, try broader search
    if not inspector:
        m = re.search(r"var\s+checkUserName\s*=\s*['\"]([^'\"]+)['\"]", html)
        if m:
            inspector = m.group(1)

    # Inspection photos
    photos: list[str] = []
    for img in parser.css("img"):
        src = img.attributes.get("src", "")
        if src and "__check" in src:
            if src.startswith("/"):
                src = f"https://ck.carmodoo.com{src}"
            elif src.startswith("//"):
                src = f"https:{src}"
            if src not in photos:
                photos.append(src)

    # Recall status
    recall_applicable = False
    m = re.search(r"setData\(\s*'rc'\s*,\s*'(\{[^']*\})'\s*\)", html)
    if m:
        try:
            rc_data = json.loads(m.group(1))
            recall_applicable = rc_data.get("1") == "2"
        except json.JSONDecodeError:
            pass

    return {
        "available": True,
        "documentNumber": doc_number,
        "inspectionDate": inspection_date,
        "inspector": inspector,
        "mileage": {
            "value": mileage_value,
            "gaugeStatus": bc.get("gaugeStatus", ""),
            "trend": mileage_trend,
        },
        "vinStatus": bc.get("vinMarking", ""),
        "emissions": {
            "status": bc.get("emissions", ""),
            "co": co_value,
            "hc": hc_value,
            "smoke": smoke_value,
        },
        "tuning": {"exists": bc.get("tuning") == "exists"},
        "specialHistory": {
            "flood": bc.get("flood") == "exists",
            "fire": bc.get("fire") == "exists",
        },
        "accidentHistory": _parse_accident_history(mac_data),
        "warranty": {
            "type": bc.get("warrantyType", ""),
            "company": warranty_company,
            "premium": warranty_premium,
        },
        "recallStatus": {"applicable": recall_applicable},
        "bodyDamage": _parse_body_damage(uc_acc_out, uc_acc_bone, uc_img_on),
        "detailedCondition": _parse_detailed_condition(dc_data),
        "photos": photos,
    }
