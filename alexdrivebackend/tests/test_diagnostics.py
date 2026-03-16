from app.parsers.diagnostics import diagnose_listing_html


class TestDiagnoseListingHtml:
    def test_with_listings(self):
        html = '''
        <html><ul>
            <li><a href="/?m=sale&s=detail&seq=001">Car 1</a></li>
            <li><a href="/?m=sale&s=detail&seq=002">Car 2</a></li>
        </ul>
        <a href="javascript:page('2')">2</a>
        </html>
        '''
        result = diagnose_listing_html(html)
        assert result["html_length"] == len(html)
        assert result["links_with_seq"] == 2
        assert result["has_pagination"] is True

    def test_with_empty_html(self):
        html = "<html></html>"
        result = diagnose_listing_html(html)
        assert result["html_length"] == len(html)
        assert result["li_count"] == 0
        assert result["links_with_seq"] == 0
        assert result["has_pagination"] is False

    def test_no_pagination(self):
        html = '<html><ul><li><a href="/?seq=001">Car</a></li></ul></html>'
        result = diagnose_listing_html(html)
        assert result["links_with_seq"] == 1
        assert result["has_pagination"] is False
