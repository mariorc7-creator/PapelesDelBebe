import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

MODULE = Path(__file__).with_name("superagente_affiliate_monthly.py")
spec = importlib.util.spec_from_file_location("superagente_affiliate_monthly", MODULE)
monthly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monthly)

class AffiliateMonthlyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def csv(self, filename, value):
        path = self.root / filename
        path.write_text(value, encoding="utf-8")
        return path

    def test_reject_no_data(self):
        with self.assertRaises(ValueError):
            monthly.build_monthly_brief("2026-11")

    def test_month_validation(self):
        path = self.csv("clicks.csv", "date,category,clicks\n")
        for month in ("2026-00", "2026-13", "2026-1", "November 2026", "2026-11-01"):
            with self.subTest(month=month), self.assertRaises(ValueError):
                monthly.build_monthly_brief(month, clicks_csv=path)

    def test_monthly_period_does_not_include_other_month(self):
        path = self.csv("clicks.csv", "date,category,clicks\n2026-10-31,cuna,8\n2026-11-01,cuna,2\n2026-12-01,cuna,9\n")
        b = monthly.build_monthly_brief("2026-11", clicks_csv=path)
        self.assertEqual(b["clicks"], 2)
        self.assertEqual(b["clicks_coverage_days"], 1)
        self.assertEqual(b["from"], "2026-11-01")
        self.assertEqual(b["to"], "2026-11-30")
        self.assertFalse(b["full_month_coverage_confirmed"])

    def test_sales_and_clicks_are_independent(self):
        clicks = self.csv("clicks.csv", "date,category,clicks\n2026-11-01,trona,7\n")
        sales = self.csv("sales.csv", "date,ordered_items,shipped_items,commission_eur\n2026-11-01,2,1,5.00\n2026-11-02,0,0,-1.00\n")
        b = monthly.build_monthly_brief("2026-11",clicks_csv=clicks,amazon_csv=sales)
        self.assertEqual(b["amazon_commissions_eur"], "4.00")
        self.assertEqual(b["clicks"], 7)
        self.assertIsNone(b["conversion_rate"])
        self.assertIsNone(b["customer_attribution"])
        self.assertFalse(b["source_files_independently_verified"])
        self.assertFalse(b["publication_allowed"])

    def test_no_sales_file_is_unknown_not_zero(self):
        clicks = self.csv("clicks.csv", "date,category,clicks\n")
        b = monthly.build_monthly_brief("2026-11",clicks_csv=clicks)
        self.assertIsNone(b["amazon_commissions_eur"])
        self.assertIn("Sin datos", monthly.format_markdown(b))

    def test_markdown_cannot_claim_proven_revenue(self):
        sales = self.csv("sales.csv", "date,ordered_items,shipped_items,commission_eur\n2026-11-01,1,1,7.00\n")
        b = monthly.build_monthly_brief("2026-11",amazon_csv=sales)
        text = monthly.format_markdown(b)
        self.assertIn("origen pendiente de verificar", text)
        self.assertIn("No calculable", text)
        self.assertIn("7.00 €", text)
        self.assertFalse(b["automatic_website_changes"])

if __name__ == "__main__":
    unittest.main()
