import re

from selectolax.lexbor import LexborHTMLParser


def diagnose_listing_html(html: str) -> dict:
    """Analyze listing HTML to diagnose why parsing might fail.

    Checks each CSS selector used by the listing parser and returns
    counts/booleans for each, plus markers for common error responses.
    """
    parser = LexborHTMLParser(html)

    tr_uc_carcss = parser.css("tr.uc_carcss")
    all_tr = parser.css("tr")

    a_with_popup_count = 0
    for a in parser.css("a[href]"):
        href = a.attributes.get("href", "")
        if "carmangerDetailWindowPopUp_CHECK" in href:
            a_with_popup_count += 1

    hdf_found = bool(re.search(r'hdfCarRowCount', html))

    login_form_detected = (
        "/User/Login" in html
        or 'id="userid"' in html
        or 'id="userpwd"' in html
    )

    sample_classes: list[str] = []
    seen: set[str] = set()
    for tr in all_tr:
        cls = tr.attributes.get("class", "")
        if cls and cls not in seen:
            seen.add(cls)
            sample_classes.append(cls)
            if len(sample_classes) >= 10:
                break

    return {
        "html_length": len(html),
        "tr_uc_carcss_count": len(tr_uc_carcss),
        "all_tr_count": len(all_tr),
        "a_with_popup_count": a_with_popup_count,
        "hdfCarRowCount_found": hdf_found,
        "login_form_detected": login_form_detected,
        "sample_tr_classes": sample_classes,
    }
