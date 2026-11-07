import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

MODULE = Path(__file__).with_name("superagente_affiliate_performance.py")
spec = importlib.util.spec_from_file_location("affiliate_performance", MODULE)
performance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(performance)

class AffiliatePerformanceTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def write(self, filename, data):
        path = self.root / filename
        path.write_text(data, encoding="utf-8")
        return path

    def test_requires_actual_source(self):
        with self.assertRaises(ValueError):
            performance.build_report()

    def test_clicks_only_does_not_invent_commissions(self):
        clicks = self.write("clicks.csv", "date,category,clicks\n2026-11-01,trona,2\n2026-11-02,cuna,3\n")
        result = performance.build_report(clicks_path=clicks)
        self.assertEqual(result["clicks"]["total"], 5)
        self.assertIsNone(result["amazon"]["commissions_eur"])
        self.assertIsNone(result["conversion_rate"])
        self.assertFalse(result["verified_import"])
        self.assertFalse(result["publication_allowed"])

    def test_amazon_only_does_not_invent_clicks(self):
        sales = self.write("amazon.csv", "date,ordered_items,shipped_items,commission_eur\n2026-11-02,2,1,4.50\n")
        result = performance.build_report(amazon_path=sales)
        self.assertEqual(result["amazon"]["ordered_items"], 2)
        self.assertEqual(result["amazon"]["commissions_eur"], "4.50")
        self.assertIsNone(result["clicks"]["total"])

    def test_separate_sources_never_claim_conversion(self):
        clicks = self.write("clicks.csv", "date,category,clicks\n2026-11-01,coche,20\n")
        sales = self.write("amazon.csv", "date,ordered_items,shipped_items,commission_eur\n2026-11-01,1,1,10.00\n")
        result = performance.build_report(clicks_path=clicks, amazon_path=sales)
        self.assertEqual(result["clicks"]["by_category"], {"coche": 20})
        self.assertEqual(result["amazon"]["commissions_eur"], "10.00")
        self.assertIsNone(result["conversion_rate"])

    def test_date_filter_keeps_only_explicit_rows(self):
        clicks = self.write("clicks.csv", "date,category,clicks\n2026-10-01,cuna,3\n2026-11-01,cuna,4\n")
        result = performance.build_report(clicks_path=clicks,start="2026-11-01",end="2026-11-30")
        self.assertEqual(result["clicks"]["total"], 4)
        self.assertEqual(result["clicks"]["days_with_report_rows"], 1)

    def test_empty_file_keeps_zero_distinct_from_missing_source(self):
        clicks = self.write("clicks.csv", "date,category,clicks\n")
        result = performance.build_report(clicks_path=clicks)
        self.assertEqual(result["clicks"]["total"], 0)
        self.assertIsNone(result["amazon"]["ordered_items"])

    def test_negative_commissions_capture_refunds(self):
        sales = self.write("amazon.csv", "date,ordered_items,shipped_items,commission_eur\n2026-11-01,1,1,4.00\n2026-11-02,0,0,-1.00\n")
        self.assertEqual(performance.build_report(amazon_path=sales)["amazon"]["commissions_eur"], "3.00")

    def test_reject_nan_commissions(self):
        sales = self.write("amazon.csv", "date,ordered_items,shipped_items,commission_eur\n2026-11-01,1,1,NaN\n")
        with self.assertRaises(ValueError):
            performance.build_report(amazon_path=sales)

    def test_reject_unexpected_columns(self):
        clicks = self.write("clicks.csv", "date,category,clicks,secret\n2026-11-01,cuna,2,foo\n")
        with self.assertRaises(ValueError):
            performance.build_report(clicks_path=clicks)

    def test_reject_bad_date(self):
        clicks = self.write("clicks.csv", "date,category,clicks\n2026-02-30,cuna,2\n")
        with self.assertRaises(ValueError):
            performance.build_report(clicks_path=clicks)

    def test_reject_reverse_period(self):
        clicks = self.write("clicks.csv", "date,category,clicks\n")
        with self.assertRaises(ValueError):
            performance.build_report(clicks_path=clicks,start="2026-11-30",end="2026-11-01")

if __name__ == "__main__":
    unittest.main()
