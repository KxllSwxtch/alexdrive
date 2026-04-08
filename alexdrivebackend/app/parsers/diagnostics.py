import re

from selectolax.lexbor import LexborHTMLParser


def diagnose_listing_html(html: str) -> dict:
    """Analyze listing HTML to diagnose why parsing might fail.

    Checks CSS selectors used by the listing parser and returns
    counts/booleans for each, plus markers for common error responses.
    """
    parser = LexborHTMLParser(html)

    all_tr = parser.css("tr")

    detail_link_count = 0
    for a in parser.css("a[href]"):
        href = a.attributes.get("href", "")
        if "/search/detail/" in href:
            detail_link_count += 1

    name_count = len(parser.css("span.name a"))
    price_count = len(parser.css("span.car_pay"))
    spec_count = len(parser.css("ul.car-option"))

    total_match = re.search(r"전체\s*([\d,]+)\s*대", html)

    login_form_detected = (
        "/User/Login" in html
        or 'id="userid"' in html
        or 'id="userpwd"' in html
    )

    rate_limited = "limits_box" in html

    return {
        "html_length": len(html),
        "all_tr_count": len(all_tr),
        "detail_link_count": detail_link_count,
        "name_span_count": name_count,
        "price_span_count": price_count,
        "spec_ul_count": spec_count,
        "total_count_text": total_match.group(0) if total_match else None,
        "login_form_detected": login_form_detected,
        "rate_limited": rate_limited,
    }
