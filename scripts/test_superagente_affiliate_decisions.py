import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("superagente_affiliate_decisions.py")
spec = importlib.util.spec_from_file_location("affiliate_decisions", MODULE)
decisions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decisions)

def monthly(clicks=None, categories=None, commissions=None, verified=False):
    return {
        "schema_version": 1, "month": "2026-11", "mode": "offline_review_only",
        "publication_allowed": False, "automatic_website_changes": False,
        "source_files_independently_verified": verified,
        "clicks": clicks, "clicks_by_category": categories,
        "amazon_ordered_items": None, "amazon_shipped_items": None,
        "clicks_coverage_days": None, "amazon_coverage_days": None,
        "amazon_commissions_eur": commissions,
        "conversion_rate": None, "customer_attribution": None,
    }

class AffiliateDecisionsTests(unittest.TestCase):
    def test_no_data_requires_both_exports_and_verification(self):
        plan = decisions.build_decisions(monthly())
        ids = [t["id"] for t in plan["tasks"]]
        self.assertEqual(ids, ["verify-source-exports", "obtain-amazon-report", "obtain-clicks"])
        self.assertFalse(plan["publication_allowed"])
        self.assertFalse(plan["monetization_claims_allowed"])

    def test_provenance_gate_remains_explicit(self):
        plan = decisions.build_decisions(monthly(3, {"cuna": 3}, "1.00"))
        self.assertEqual(plan["data_status"], "unverified_export")
        self.assertEqual(plan["tasks"][0]["id"], "verify-source-exports")

    def test_verified_clicks_prioritise_review_not_sale_claims(self):
        plan = decisions.build_decisions(monthly(10, {"trona": 7, "cuna": 2, "carrito": 1}, "5.00", True))
        category_tasks = [t for t in plan["tasks"] if t["id"].startswith("review-category-")]
        self.assertEqual([t["evidence"]["category"] for t in category_tasks], ["trona", "cuna", "carrito"])
        self.assertFalse(plan["affiliate_attribution_available"])
        self.assertTrue(all(not t["website_changes_allowed"] for t in plan["tasks"]))

    def test_zero_clicks_does_not_imply_failures(self):
        plan = decisions.build_decisions(monthly(0, {}, "0.00", True))
        self.assertIn("inspect-zero-clicks", [t["id"] for t in plan["tasks"]])
        self.assertFalse(plan["automatic_website_changes"])

    def test_mismatched_category_totals_rejected(self):
        with self.assertRaises(ValueError):
            decisions.build_decisions(monthly(10, {"cuna": 9}))

    def test_reject_fake_conversion_rates(self):
        bad = monthly(10, {"cuna": 10})
        bad["conversion_rate"] = 0.3
        with self.assertRaises(ValueError):
            decisions.build_decisions(bad)

    def test_reject_publish_permission(self):
        bad = monthly()
        bad["publication_allowed"] = True
        with self.assertRaises(ValueError):
            decisions.build_decisions(bad)

    def test_top_3_categories_only_and_safety(self):
        plan = decisions.build_decisions(monthly(10, {"a": 1, "b": 2, "c": 3, "d": 4}, verified=True))
        selected = [x["evidence"]["category"] for x in plan["tasks"] if x["id"].startswith("review-category")]
        self.assertEqual(sorted(selected), ["b", "c", "d"])
        self.assertFalse(plan["seo_ux_protection"]["modify_review_dates"])
        self.assertTrue(plan["seo_ux_protection"]["require_mobile_seo_regression_tests"])

if __name__ == "__main__":
    unittest.main()
