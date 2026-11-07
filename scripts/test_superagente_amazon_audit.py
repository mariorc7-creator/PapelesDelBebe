import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SCRIPT = Path(__file__).with_name("superagente_amazon_audit.py")
spec = importlib.util.spec_from_file_location("affiliate_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class AmazonAffiliateAuditTests(unittest.TestCase):
    def test_valid_affiliate_link(self):
        self.assertEqual(audit.check_amazon_url("https://www.amazon.es/s?k=cuna&tag=example-21", affiliate_id="example-21"), [])

    def test_missing_tracking_tag(self):
        self.assertIn("missing_affiliate_tag", audit.check_amazon_url("https://www.amazon.es/s?k=cuna"))

    def test_reject_misleading_host(self):
        self.assertIn("unapproved_destination", audit.check_amazon_url("https://amazon.es.evil.example/s?k=x&tag=x-21"))

    def test_reject_insecure_http(self):
        self.assertIn("non_https", audit.check_amazon_url("http://amazon.es/s?k=x&tag=x-21"))

    def test_js_dynamic_affiliate_is_detected(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text(
                "<p>Publicidad: como afiliado recibimos una comisión</p>"
                "<script>const products=[{affiliate:'https://www.amazon.es/s?k=trona&tag=test-21'}];</script>",
                encoding="utf-8"
            )
            report = audit.scan(root)
            self.assertEqual(report["total_amazon_links"], 1)
            self.assertEqual(report["issue_count"], 0)
            self.assertFalse(report["publication_allowed"])

    def test_visible_link_needs_rel(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text(
                '<a href="https://www.amazon.es/s?k=cuna&tag=test-21">Comprar</a>',
                encoding="utf-8"
            )
            result = audit.scan(root)
            self.assertEqual(result["issue_count"], 1)
            self.assertIn("missing_sponsored_or_nofollow", result["issues"][0]["issues"])
            self.assertIn("no_affiliate_disclosure_found", result["issues"][0]["issues"])

    def test_external_blank_is_not_sufficient_for_ad_label(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text(
                '<p>Enlace publicitario</p><a target="_blank" rel="noopener noreferrer" '
                'href="https://amazon.es/s?k=x&tag=test-21">Ver</a>', encoding="utf-8"
            )
            report = audit.scan(root)
            self.assertIn("missing_sponsored_or_nofollow", report["issues"][0]["issues"])

    def test_ignored_build_directory(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "dist").mkdir()
            (root / "dist/index.html").write_text(
                '<a href="https://www.amazon.es/">x</a>', encoding="utf-8"
            )
            self.assertEqual(audit.scan(root)["total_amazon_links"], 0)

if __name__ == "__main__":
    unittest.main()
