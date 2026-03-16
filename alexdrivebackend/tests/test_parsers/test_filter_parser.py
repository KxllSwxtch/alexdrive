import pytest

from app.parsers.filter_parser import parse_carcode_js, build_filter_hierarchy, CATEGORIES, COLORS, FUELS, MISSIONS


SAMPLE_JS = '''
var carcode = [[1,"Hyundai","i30","The New i30","1.6 VGT","Unique","승용","준중형"],[1,"Hyundai","Sonata","New Sonata","2.0","Premium","승용","중형"],[1,"Kia","K5","New K5","2.0","Standard","승용","중형"],[2,"BMW","3 Series","320i","Luxury","Sport","승용","중형"],[2,"BMW","5 Series","530i","M Sport","","승용","대형"],[3,"Hyundai","Mighty","1 Ton","Standard","","화물","소형"]];
'''


class TestParseCarcodeJs:
    def test_parse_valid_js(self):
        result = parse_carcode_js(SAMPLE_JS)
        assert len(result) == 6
        assert result[0] == [1, "Hyundai", "i30", "The New i30", "1.6 VGT", "Unique", "승용", "준중형"]

    def test_parse_empty(self):
        result = parse_carcode_js("")
        assert result == []

    def test_parse_no_var(self):
        result = parse_carcode_js("var other = [1,2,3];")
        assert result == []


class TestBuildFilterHierarchy:
    def setup_method(self):
        self.carcode = parse_carcode_js(SAMPLE_JS)

    def test_korean_makers(self):
        hierarchy = build_filter_hierarchy(self.carcode, 1)
        maker_names = {m["MakerName"] for m in hierarchy["makers"]}
        assert "Hyundai" in maker_names
        assert "Kia" in maker_names
        assert "BMW" not in maker_names

    def test_foreign_makers(self):
        hierarchy = build_filter_hierarchy(self.carcode, 2)
        maker_names = {m["MakerName"] for m in hierarchy["makers"]}
        assert "BMW" in maker_names
        assert "Hyundai" not in maker_names

    def test_truck_makers(self):
        hierarchy = build_filter_hierarchy(self.carcode, 3)
        maker_names = {m["MakerName"] for m in hierarchy["makers"]}
        assert "Hyundai" in maker_names
        assert "BMW" not in maker_names

    def test_models_for_maker(self):
        hierarchy = build_filter_hierarchy(self.carcode, 1)
        hyundai_models = hierarchy["models"].get("Hyundai", [])
        model_names = {m["ModelName"] for m in hyundai_models}
        assert "i30" in model_names
        assert "Sonata" in model_names

    def test_model_details(self):
        hierarchy = build_filter_hierarchy(self.carcode, 1)
        i30_details = hierarchy["modelDetails"].get("i30", [])
        assert len(i30_details) == 1
        assert i30_details[0]["ModelDetailName"] == "The New i30"

    def test_grades(self):
        hierarchy = build_filter_hierarchy(self.carcode, 1)
        grades = hierarchy["grades"].get("The New i30", [])
        assert len(grades) == 1
        assert grades[0]["GradeName"] == "1.6 VGT"

    def test_grade_details(self):
        hierarchy = build_filter_hierarchy(self.carcode, 1)
        grade_details = hierarchy["gradeDetails"].get("1.6 VGT", [])
        assert len(grade_details) == 1
        assert grade_details[0]["GradeDetailName"] == "Unique"

    def test_maker_no_equals_maker_name(self):
        hierarchy = build_filter_hierarchy(self.carcode, 1)
        for maker in hierarchy["makers"]:
            assert maker["MakerNo"] == maker["MakerName"]

    def test_empty_carnation(self):
        hierarchy = build_filter_hierarchy(self.carcode, 99)
        assert hierarchy["makers"] == []
        assert hierarchy["models"] == {}


class TestStaticFilters:
    def test_categories(self):
        assert len(CATEGORIES) == 3
        values = {c["value"] for c in CATEGORIES}
        assert values == {"1", "2", "3"}

    def test_colors(self):
        assert len(COLORS) > 10
        assert any(c["CKeyNo"] == "흰색" for c in COLORS)

    def test_fuels(self):
        assert len(FUELS) == 8
        assert FUELS[0]["FKeyNo"] == "1"
        assert FUELS[0]["FuelName"] == "Бензин"

    def test_missions(self):
        assert len(MISSIONS) == 4
        assert any(m["MKeyNo"] == "오토" for m in MISSIONS)
