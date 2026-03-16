import re

from selectolax.lexbor import LexborHTMLParser


def diagnose_listing_html(html: str) -> dict:
    """Analyze jenya listing HTML to diagnose why parsing might fail."""
    parser = LexborHTMLParser(html)

    all_li = parser.css("ul li")
    links_with_seq = 0
    for a in parser.css("a[href]"):
        href = a.attributes.get("href", "")
        if "seq=" in href:
            links_with_seq += 1

    has_pagination = bool(re.search(r"javascript:page\('\d+'\)", html))

    return {
        "html_length": len(html),
        "li_count": len(all_li),
        "links_with_seq": links_with_seq,
        "has_pagination": has_pagination,
    }
