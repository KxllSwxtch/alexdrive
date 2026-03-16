import pytest

from app.parsers.listing_parser import parse_car_listings, parse_pagination, estimate_total


SAMPLE_LISTING_HTML = '''
<html><body>
<ul>
  <li>
    <a href="/?m=sale&s=detail&seq=0006687244">
      <img src="https://photo5.autosale.co.kr/car_middle/NC00066/NC0006687244_1.jpg">
      <div class="carmemo">
        <span class="carinfo">Kia New K5 2.0 Gasoline</span>
        <span>2015/08 | 109,000km | Автоматическая коробка передач | Бензин</span>
      </div>
      <strong>\\9,290,000</strong>
    </a>
  </li>
  <li>
    <a href="/?m=sale&s=detail&seq=0007123456">
      <img src="https://photo5.autosale.co.kr/car_middle/NC00071/NC0007123456_1.jpg">
      <div class="carmemo">
        <span class="carinfo">Hyundai Sonata 2.0</span>
        <span>2020/03 | 45,000km | Автоматическая коробка передач | Бензин</span>
      </div>
      <strong>\\15,900,000</strong>
    </a>
  </li>
</ul>
<a href="javascript:page('2')">2</a>
<a href="javascript:page('3')">3</a>
<a href="javascript:page('4')">▶</a>
</body></html>
'''


class TestParseCarListings:
    def test_parses_listings(self):
        listings = parse_car_listings(SAMPLE_LISTING_HTML)
        assert len(listings) == 2

    def test_first_listing_fields(self):
        listings = parse_car_listings(SAMPLE_LISTING_HTML)
        car = listings[0]
        assert car["encryptedId"] == "0006687244"
        assert "autosale.co.kr" in car["imageUrl"]
        assert car["name"] == "Kia New K5 2.0 Gasoline"
        assert car["year"] == "2015/08"
        assert car["mileage"] == "109,000km"
        assert car["transmission"] == "Автоматическая коробка передач"
        assert car["fuel"] == "Бензин"
        assert car["price"] == "9,290,000"

    def test_second_listing(self):
        listings = parse_car_listings(SAMPLE_LISTING_HTML)
        car = listings[1]
        assert car["encryptedId"] == "0007123456"
        assert car["name"] == "Hyundai Sonata 2.0"
        assert car["price"] == "15,900,000"

    def test_empty_html(self):
        listings = parse_car_listings("<html><body></body></html>")
        assert listings == []

    def test_no_seq_links(self):
        html = '<html><ul><li><a href="/other">link</a></li></ul></html>'
        listings = parse_car_listings(html)
        assert listings == []


class TestParsePagination:
    def test_parse_pagination(self):
        result = parse_pagination(SAMPLE_LISTING_HTML)
        assert result["max_visible_page"] >= 3
        assert result["has_next"] is True

    def test_no_pagination(self):
        result = parse_pagination("<html><body>no pages</body></html>")
        assert result["max_visible_page"] == 1
        assert result["has_next"] is False

    def test_last_page(self):
        html = '''
        <a href="javascript:page('1')">1</a>
        <a href="javascript:page('2')">2</a>
        <a href="javascript:page('3')">3</a>
        '''
        result = parse_pagination(html)
        assert result["max_visible_page"] == 3
        assert result["has_next"] is False


class TestEstimateTotal:
    def test_with_next(self):
        total = estimate_total({"max_visible_page": 5, "has_next": True})
        assert total == 101

    def test_without_next(self):
        total = estimate_total({"max_visible_page": 5, "has_next": False})
        assert total == 100

    def test_single_page(self):
        total = estimate_total({"max_visible_page": 1, "has_next": False})
        assert total == 20
