import json
import re
from typing import Any

from bs4 import BeautifulSoup


def extract_js_var(js_content: str, var_name: str) -> str | None:
    search_str = f"var {var_name}"
    idx = js_content.find(search_str)
    if idx == -1:
        return None

    eq_idx = js_content.find("=", idx + len(search_str))
    if eq_idx == -1:
        return None

    start = eq_idx + 1
    while start < len(js_content) and js_content[start] == " ":
        start += 1

    depth = 0
    in_str = False
    str_ch = ""
    esc = False

    for i in range(start, len(js_content)):
        ch = js_content[i]
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if in_str:
            if ch == str_ch:
                in_str = False
            continue
        if ch in ('"', "'"):
            in_str = True
            str_ch = ch
            continue
        if ch in ("[", "{"):
            depth += 1
        if ch in ("]", "}"):
            depth -= 1
            if depth == 0:
                return js_content[start:i + 1]

    return None


def safe_parse_json(text: str) -> Any:
    try:
        json_text = re.sub(r'([{,]\s*)([A-Za-z_]\w*)(\s*:)', r'\1"\2"\3', text)
        return json.loads(json_text)
    except (json.JSONDecodeError, ValueError):
        return None


def parse_makers(js: str) -> list[dict]:
    raw = extract_js_var(js, "CarBaseMaker")
    if not raw:
        return []
    data = safe_parse_json(raw)
    if not isinstance(data, list):
        return []
    return data


def parse_models(js: str) -> dict[str, list[dict]]:
    raw = extract_js_var(js, "CarBaseModel")
    if not raw:
        return {}
    data = safe_parse_json(raw)
    if not isinstance(data, dict):
        return {}
    return data


def parse_model_details(js: str) -> dict[str, list[dict]]:
    raw = extract_js_var(js, "CarBaseModelDetail")
    if not raw:
        return {}
    data = safe_parse_json(raw)
    if not isinstance(data, dict):
        return {}
    return data


def parse_grades(js: str) -> dict[str, list[dict]]:
    raw = extract_js_var(js, "CarBaseGrade")
    if not raw:
        return {}
    data = safe_parse_json(raw)
    if not isinstance(data, dict):
        return {}
    return data


def parse_grade_details(js: str) -> dict[str, list[dict]]:
    raw = extract_js_var(js, "CarBaseGradeDetail")
    if not raw:
        return {}
    data = safe_parse_json(raw)
    if not isinstance(data, dict):
        return {}
    return data


def parse_filter_data_from_js(js_content: str) -> dict:
    return {
        "makers": parse_makers(js_content),
        "models": parse_models(js_content),
        "modelDetails": parse_model_details(js_content),
        "grades": parse_grades(js_content),
        "gradeDetails": parse_grade_details(js_content),
    }


def parse_danjis_from_js(js_content: str, area_code: str) -> list[dict]:
    raw = extract_js_var(js_content, "BaseDanji")
    if not raw:
        return []
    data = safe_parse_json(raw)
    if not isinstance(data, dict):
        return []
    area_danjis = data.get(area_code, [])
    return [
        {"DanjiNo": int(d["DanjiNo"]), "DanjiName": d["DanjiName"]}
        for d in area_danjis
    ]


def parse_select_options(html: str, select_id: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    select = soup.find("select", id=select_id)
    if not select:
        return []
    options: list[dict[str, str]] = []
    for el in select.find_all("option"):
        value = el.get("value", "")
        label = el.get_text(strip=True)
        if value and value != "" and value != "0":
            options.append({"value": value, "label": label})
    return options
