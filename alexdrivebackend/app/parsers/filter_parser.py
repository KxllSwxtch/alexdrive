import re


def parse_carcode_js(js_content: str) -> list[list]:
    """Extract the carcode array from carcode2_en.js.

    Each entry: [carnation, maker, series, trim, trimVariant, detail, cartype2, cartype]
    """
    match = re.search(r"var\s+carcode\s*=\s*\[", js_content)
    if not match:
        return []

    start = match.end() - 1  # include the opening [
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
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                array_str = js_content[start:i + 1]
                break
    else:
        return []

    # Parse the JS array — entries use double quotes for strings
    # Convert to valid JSON by replacing single quotes if needed
    try:
        import json
        return json.loads(array_str)
    except (json.JSONDecodeError, ValueError):
        # Try replacing single quotes
        try:
            fixed = array_str.replace("'", '"')
            return json.loads(fixed)
        except (json.JSONDecodeError, ValueError):
            return []


def build_filter_hierarchy(carcode: list[list], carnation: int) -> dict:
    """Build hierarchical filter structure for a specific category (carnation).

    Returns dict with makers, models, modelDetails, grades, gradeDetails.
    """
    makers_set: set[str] = set()
    models_dict: dict[str, set[str]] = {}      # maker -> set of series
    details_dict: dict[str, set[str]] = {}      # series -> set of trims
    grades_dict: dict[str, set[str]] = {}       # trim -> set of trimVariants
    grade_details_dict: dict[str, set[str]] = {}  # trimVariant -> set of details

    for entry in carcode:
        if len(entry) < 6:
            continue
        entry_carnation = entry[0]
        if entry_carnation != carnation:
            continue

        maker = entry[1]
        series = entry[2]
        trim = entry[3]
        trim_variant = entry[4]
        detail = entry[5]

        if maker:
            makers_set.add(maker)
        if maker and series:
            models_dict.setdefault(maker, set()).add(series)
        if series and trim:
            details_dict.setdefault(series, set()).add(trim)
        if trim and trim_variant:
            grades_dict.setdefault(trim, set()).add(trim_variant)
        if trim_variant and detail:
            grade_details_dict.setdefault(trim_variant, set()).add(detail)

    # Convert to list format matching frontend expectations
    makers = sorted(
        [{"MakerNo": m, "MakerName": m} for m in makers_set],
        key=lambda x: x["MakerName"],
    )

    models: dict[str, list[dict]] = {}
    for maker, series_set in models_dict.items():
        models[maker] = sorted(
            [{"ModelNo": s, "ModelName": s, "MakerNo": maker} for s in series_set],
            key=lambda x: x["ModelName"],
        )

    model_details: dict[str, list[dict]] = {}
    for series, trim_set in details_dict.items():
        model_details[series] = sorted(
            [{"ModelDetailNo": t, "ModelDetailName": t, "ModelNo": series} for t in trim_set],
            key=lambda x: x["ModelDetailName"],
        )

    grades: dict[str, list[dict]] = {}
    for trim, variant_set in grades_dict.items():
        grades[trim] = sorted(
            [{"GradeNo": v, "GradeName": v, "ModelDetailNo": trim} for v in variant_set],
            key=lambda x: x["GradeName"],
        )

    grade_details: dict[str, list[dict]] = {}
    for variant, detail_set in grade_details_dict.items():
        grade_details[variant] = sorted(
            [{"GradeDetailNo": d, "GradeDetailName": d, "GradeNo": variant} for d in detail_set],
            key=lambda x: x["GradeDetailName"],
        )

    return {
        "makers": makers,
        "models": models,
        "modelDetails": model_details,
        "grades": grades,
        "gradeDetails": grade_details,
    }


# Static filter options from jenya HTML

COLORS = [
    {"CKeyNo": "흰색", "ColorName": "Белый"},
    {"CKeyNo": "검정", "ColorName": "Черный"},
    {"CKeyNo": "은색", "ColorName": "Серебристый"},
    {"CKeyNo": "회색", "ColorName": "Серый"},
    {"CKeyNo": "진주", "ColorName": "Жемчужный"},
    {"CKeyNo": "파란", "ColorName": "Синий"},
    {"CKeyNo": "빨강", "ColorName": "Красный"},
    {"CKeyNo": "녹색", "ColorName": "Зеленый"},
    {"CKeyNo": "갈색", "ColorName": "Коричневый"},
    {"CKeyNo": "주황", "ColorName": "Оранжевый"},
    {"CKeyNo": "노랑", "ColorName": "Желтый"},
    {"CKeyNo": "금색", "ColorName": "Золотой"},
    {"CKeyNo": "보라", "ColorName": "Фиолетовый"},
    {"CKeyNo": "분홍", "ColorName": "Розовый"},
    {"CKeyNo": "연금", "ColorName": "Светло-золотой"},
    {"CKeyNo": "쥐색", "ColorName": "Мышиный"},
    {"CKeyNo": "청색", "ColorName": "Голубой"},
    {"CKeyNo": "하늘", "ColorName": "Небесный"},
    {"CKeyNo": "베이지", "ColorName": "Бежевый"},
    {"CKeyNo": "은회색", "ColorName": "Серебристо-серый"},
    {"CKeyNo": "연회색", "ColorName": "Светло-серый"},
    {"CKeyNo": "진회색", "ColorName": "Темно-серый"},
    {"CKeyNo": "밤색", "ColorName": "Каштановый"},
    {"CKeyNo": "연파랑", "ColorName": "Светло-синий"},
    {"CKeyNo": "진파랑", "ColorName": "Темно-синий"},
    {"CKeyNo": "연초록", "ColorName": "Светло-зеленый"},
    {"CKeyNo": "진초록", "ColorName": "Темно-зеленый"},
    {"CKeyNo": "연빨강", "ColorName": "Светло-красный"},
    {"CKeyNo": "진빨강", "ColorName": "Темно-красный"},
    {"CKeyNo": "흰진주", "ColorName": "Белый перламутр"},
    {"CKeyNo": "검진주", "ColorName": "Черный перламутр"},
    {"CKeyNo": "기타", "ColorName": "Другой"},
]

FUELS = [
    {"FKeyNo": "1", "FuelName": "Бензин"},
    {"FKeyNo": "2", "FuelName": "Дизель"},
    {"FKeyNo": "3", "FuelName": "LPG"},
    {"FKeyNo": "4", "FuelName": "Гибрид"},
    {"FKeyNo": "5", "FuelName": "Электро"},
    {"FKeyNo": "6", "FuelName": "CNG"},
    {"FKeyNo": "7", "FuelName": "Водород"},
    {"FKeyNo": "8", "FuelName": "LPG Гибрид"},
]

MISSIONS = [
    {"MKeyNo": "오토", "MissionName": "Автоматическая коробка передач"},
    {"MKeyNo": "수동", "MissionName": "Механическая коробка передач"},
    {"MKeyNo": "세미오토", "MissionName": "Полуавтомат"},
    {"MKeyNo": "무단변속", "MissionName": "Вариатор"},
]

CATEGORIES = [
    {"value": "1", "label": "Корейские марки"},
    {"value": "2", "label": "Иностранные марки"},
    {"value": "3", "label": "Грузовые автомобили"},
]
