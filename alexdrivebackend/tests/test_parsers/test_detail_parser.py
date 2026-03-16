import pytest

from app.parsers.detail_parser import parse_car_detail


SAMPLE_DETAIL_HTML = '''
<html><head><title>Kia K5 2.0 - jenya</title></head><body>
<div class="car_name">Kia New K5 2.0 Gasoline</div>
<div class="car_price">\\9,290,000</div>
<table>
  <tr><th>Год выпуска</th><td>2015/08</td></tr>
  <tr><th>Цвет</th><td>Белый</td></tr>
  <tr><th>Топливо</th><td>Бензин</td></tr>
  <tr><th>Коробка</th><td>Автоматическая коробка передач</td></tr>
  <tr><th>Пробег</th><td>109,000km</td></tr>
  <tr><th>Номер авто</th><td>12가3456</td></tr>
  <tr><th>Автодилер</th><td>AlexDrive</td></tr>
  <tr><th>Контакты</th><td>010-3908-6050</td></tr>
</table>
<div class="swiper-wrapper">
  <div class="swiper-slide" style="background-image: url(https://photo5.autosale.co.kr/car_large/NC00066/NC0006687244_1.jpg)"></div>
  <div class="swiper-slide" style="background-image: url(https://photo5.autosale.co.kr/car_large/NC00066/NC0006687244_2.jpg)"></div>
  <div class="swiper-slide" style="background-image: url(https://photo5.autosale.co.kr/car_small/NC00066/NC0006687244_1.jpg)"></div>
</div>
<ul class="option_list">
  <li>ABS</li>
  <li>Airbag</li>
  <li>Navigation</li>
</ul>
<button onclick="window.open('https://photo5.autosale.co.kr/safe.php?seq=0006687244&t=jeniya1661')">Diagnostics</button>
</body></html>
'''


class TestParseCarDetail:
    def test_name(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert result["name"] == "Kia New K5 2.0 Gasoline"

    def test_price(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert result["price"] == "9,290,000"

    def test_encrypted_id(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert result["encryptedId"] == "0006687244"

    def test_specs(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert result["year"] == "2015/08"
        assert result["color"] == "Белый"
        assert result["fuel"] == "Бензин"
        assert result["transmission"] == "Автоматическая коробка передач"
        assert result["mileage"] == "109,000km"
        assert result["carNumber"] == "12가3456"

    def test_dealer_info(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert result["dealer"] == "AlexDrive"
        assert result["phone"] == "010-3908-6050"

    def test_images_filter_small(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert len(result["images"]) == 2
        assert all("car_large" in img for img in result["images"])
        assert not any("car_small" in img for img in result["images"])

    def test_options(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert len(result["options"]) == 1
        assert result["options"][0]["group"] == "Опции"
        assert "ABS" in result["options"][0]["items"]
        assert "Navigation" in result["options"][0]["items"]

    def test_diagnostics_url(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert result["diagnosticsUrl"] is not None
        assert "safe.php" in result["diagnosticsUrl"]
        assert "seq=0006687244" in result["diagnosticsUrl"]

    def test_blur_placeholder(self):
        result = parse_car_detail(SAMPLE_DETAIL_HTML, "0006687244")
        assert result["blurDataUrl"] is not None
        assert result["blurDataUrl"].startswith("data:image/svg+xml")

    def test_empty_html(self):
        result = parse_car_detail("<html><body></body></html>", "123")
        assert result["encryptedId"] == "123"
        assert result["name"] == ""
        assert result["images"] == []
        assert result["options"] == []

    def test_no_diagnostics(self):
        html = '<html><body><div class="car_name">Test</div></body></html>'
        result = parse_car_detail(html, "999")
        assert result["diagnosticsUrl"] is None
