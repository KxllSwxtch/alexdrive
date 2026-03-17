from app.parsers.diagnostics import diagnose_listing_html


class TestDiagnoseListingHtml:
    def test_with_car_listings(self):
        html = """
        <table>
            <tr class="uc_carcss">
                <td><a href="javascript:carmangerDetailWindowPopUp_CHECK('abc123')">Car 1</a></td>
            </tr>
            <tr class="uc_carcss">
                <td><a href="javascript:carmangerDetailWindowPopUp_CHECK('def456')">Car 2</a></td>
            </tr>
            <input type="hidden" id="hdfCarRowCount" value="100" />
        </table>
        """
        result = diagnose_listing_html(html)
        assert result["html_length"] == len(html)
        assert result["tr_uc_carcss_count"] == 2
        assert result["a_with_popup_count"] == 2
        assert result["hdfCarRowCount_found"] is True
        assert result["login_form_detected"] is False
        assert result["all_tr_count"] >= 2
        assert "uc_carcss" in result["sample_tr_classes"]

    def test_with_empty_html(self):
        html = "<html></html>"
        result = diagnose_listing_html(html)
        assert result["html_length"] == len(html)
        assert result["tr_uc_carcss_count"] == 0
        assert result["all_tr_count"] == 0
        assert result["a_with_popup_count"] == 0
        assert result["hdfCarRowCount_found"] is False
        assert result["login_form_detected"] is False
        assert result["sample_tr_classes"] == []

    def test_with_login_redirect(self):
        html = """
        <html>
            <form action="/User/Login" method="post">
                <input id="userid" type="text" />
                <input id="userpwd" type="password" />
            </form>
        </html>
        """
        result = diagnose_listing_html(html)
        assert result["login_form_detected"] is True
        assert result["tr_uc_carcss_count"] == 0
        assert result["a_with_popup_count"] == 0

    def test_with_short_error_html(self):
        """Simulates the 426-byte error response."""
        html = "<script>alert('error');</script><div>잘못된 요청</div>"
        result = diagnose_listing_html(html)
        assert result["html_length"] == len(html)
        assert result["tr_uc_carcss_count"] == 0
        assert result["all_tr_count"] == 0
        assert result["login_form_detected"] is False

    def test_sample_classes_limited_to_ten(self):
        rows = "".join(f'<tr class="cls{i}"><td></td></tr>' for i in range(20))
        html = f"<table>{rows}</table>"
        result = diagnose_listing_html(html)
        assert len(result["sample_tr_classes"]) == 10
