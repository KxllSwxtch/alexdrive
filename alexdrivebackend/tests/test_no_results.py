"""A search with no matches must read as "no cars found", not as a crash.

chasainmotors answers a zero-match search with a perfectly valid 200 page (~74KB).
The status branch classified ANY zero-row page over 50 bytes as `parse_failure`, which
routes/cars.py turns into a 503 and the catalog renders as
"Не удалось загрузить эту категорию". Production logs caught a real visitor searching a
Kia K3 by plate number who got an error instead of an empty result.

The discriminator, verified against both real pages: the results container
(`table.list-table.search-txt-list` inside `div.list-top`) is present whether or not the
search matched anything. Only `ul#list-pagination` is results-dependent, so it cannot be
used. Genuinely broken HTML -- a proxy error page, a redirect -- has no container at all
and must keep reporting parse_failure so the forensic capture still fires.
"""
import pytest

from app.parsers.listing_parser import has_results_container, parse_car_listings

# Trimmed from the real pages: /search/model/kor?...&maker=10065 (zero matches) and the
# default catalog page. Structure preserved, bulk removed.
EMPTY_PAGE = """<!DOCTYPE html><html lang="ko"><head><title>수원skv1모터스 차사인모터스</title></head>
<body><div class="wrap"><div class="list-top"><span>정렬</span></div>
<table class="list-table search-txt-list" ><tbody></tbody></table>
<div class="footer">회사소개</div></div></body></html>"""

ROW = """<tr><td class="car-detail">
  <div class="img-wrap"><a href="/search/detail/463C99938774BE2159399E48EBBFAE67"><img src="https://myshop-img.carmanager.co.kr/a_TH.jpg" /></a></div>
  <div class="car-info">
    <span class="name"><a href="/search/detail/463C99938774BE2159399E48EBBFAE67">[기아]올 뉴 K7</a></span>
    <ul class="car-option"><li>2020-01</li><li>10,000km</li><li>휘발유</li><li>오토</li></ul>
    <span class="font-md car_pay">740</span>
  </div></td></tr>"""

FULL_PAGE = EMPTY_PAGE.replace("<tbody></tbody>", f"<tbody>{ROW}</tbody>")

# What a broken response actually looks like: an upstream/proxy error page.
BROKEN_PAGE = """<!DOCTYPE html><html><head><title>502 Bad Gateway</title></head>
<body><center><h1>502 Bad Gateway</h1></center><hr><center>nginx</center></body></html>""" + ("x" * 400)


class TestHasResultsContainer:
    def test_true_for_a_valid_page_with_no_matches(self):
        assert has_results_container(EMPTY_PAGE) is True

    def test_true_for_a_page_with_results(self):
        assert has_results_container(FULL_PAGE) is True

    def test_false_for_an_upstream_error_page(self):
        assert has_results_container(BROKEN_PAGE) is False

    def test_false_for_empty_string(self):
        assert has_results_container("") is False

    def test_does_not_depend_on_pagination(self):
        """ul#list-pagination only renders when there ARE results, so it must not be the marker."""
        assert "list-pagination" not in EMPTY_PAGE
        assert has_results_container(EMPTY_PAGE) is True


class TestParsingStillWorks:
    def test_empty_page_yields_no_listings(self):
        assert parse_car_listings(EMPTY_PAGE) == []

    def test_full_page_still_parses(self):
        listings = parse_car_listings(FULL_PAGE)
        assert len(listings) == 1
        assert listings[0]["id"] == "463C99938774BE2159399E48EBBFAE67"


class TestStatusClassification:
    """The scraper's status branch is what routes/cars.py keys off."""

    def _classify(self, html, listings):
        from app.services.scraper import classify_listing_status
        return classify_listing_status(html, listings)

    def test_valid_page_with_no_matches_is_no_results(self):
        assert self._classify(EMPTY_PAGE, []) == "no_results"

    def test_broken_html_is_still_parse_failure(self):
        assert self._classify(BROKEN_PAGE, []) == "parse_failure"

    def test_page_with_listings_is_ok(self):
        assert self._classify(FULL_PAGE, [{"id": "x"}]) == "ok"

    def test_tiny_response_is_still_empty(self):
        assert self._classify("", []) == "empty"


class TestRouteStatusMapping:
    @pytest.mark.asyncio
    async def test_no_results_returns_200_not_503(self, monkeypatch):
        """A zero-match search is a normal answer, not a service failure."""
        from app.routes import cars as cars_mod

        async def fake(params):
            return {"listings": [], "total": 0, "status": "no_results"}

        monkeypatch.setattr(cars_mod, "get_car_listings", fake)
        resp = await cars_mod.get_cars()
        assert resp.status_code == 200, "no_results must not be a 503"

    @pytest.mark.asyncio
    async def test_parse_failure_still_returns_503(self, monkeypatch):
        from app.routes import cars as cars_mod

        async def fake(params):
            return {"listings": [], "total": 0, "status": "parse_failure"}

        monkeypatch.setattr(cars_mod, "get_car_listings", fake)
        resp = await cars_mod.get_cars()
        assert resp.status_code == 503, "a genuine failure must still alarm"
