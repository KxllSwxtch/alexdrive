"""Regression tests for the 2026-08 car-id format change.

chasainmotors switched detail links from numeric seq ids to 32-char hex tokens
(/search/detail/463C99938774BE2159399E48EBBFAE67). The parser matched `(\\d+)`,
which:
  * truncated ids beginning with a digit  ("463C99..." -> "463"), and
  * matched NOTHING for ids beginning with a letter, silently dropping the row.

Roughly 6 of every 16 ids start with a letter, so ~37% of every page vanished and
the survivors got short, colliding ids -- which broke React's keyed reconciliation
in the catalog (stale cards persisted when switching filters).

Every pre-existing fixture used numeric ids, so the whole suite stayed green.
"""
from app.parsers.listing_parser import parse_car_listings

HEX_A = "463C99938774BE2159399E48EBBFAE67"  # starts with a digit
HEX_B = "BB8761B4284D82671F2D09D7960FE1A5"  # starts with a letter
NUMERIC = "113316161"                        # the historical format


def _row(car_id: str, name: str) -> str:
    return f"""
    <tr>
      <td class="car-detail">
        <div class="img-wrap"><a href="/search/detail/{car_id}"><img src="https://img.test/x.jpg" /></a></div>
        <div class="car-info">
          <span class="name"><a href="/search/detail/{car_id}">{name}</a></span>
          <ul class="car-option"><li>2020-01</li><li>10,000km</li><li>가솔린</li><li>오토</li></ul>
          <span class="car_pay">1,370</span>
        </div>
      </td>
    </tr>"""


def _html(*rows: str) -> str:
    return "<html><body><table>" + "".join(rows) + "</table></body></html>"


def test_hex_id_starting_with_a_digit_is_not_truncated():
    listings = parse_car_listings(_html(_row(HEX_A, "[기아]K7")))
    assert len(listings) == 1
    assert listings[0]["id"] == HEX_A, "id was truncated to its leading digits"


def test_hex_id_starting_with_a_letter_is_not_dropped():
    listings = parse_car_listings(_html(_row(HEX_B, "[테슬라]모델 X")))
    assert len(listings) == 1, "row with a letter-leading id was silently dropped"
    assert listings[0]["id"] == HEX_B


def test_numeric_ids_still_parse():
    listings = parse_car_listings(_html(_row(NUMERIC, "[현대]소나타")))
    assert len(listings) == 1
    assert listings[0]["id"] == NUMERIC


def test_a_full_page_keeps_every_row_with_unique_ids():
    """The truncation bug also made ids collide, breaking client-side list keys."""
    ids = [
        "463C99938774BE2159399E48EBBFAE67",
        "BB8761B4284D82671F2D09D7960FE1A5",
        "504D5EE6947906F4342F46DB6BD158C8",
        "9DA0B729B04694D4A6758221EEF8257B",
        "4A1B2C3D4E5F60718293A4B5C6D7E8F9",
        "4A1B2C3D4E5F60718293A4B5C6D7E8FA",  # shares a long digit-free prefix
    ]
    listings = parse_car_listings(_html(*[_row(i, f"car {n}") for n, i in enumerate(ids)]))
    assert len(listings) == len(ids), "rows were dropped"
    parsed = [c["id"] for c in listings]
    assert parsed == ids
    assert len(set(parsed)) == len(ids), "ids collided -- breaks React list keys"
