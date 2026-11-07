import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("superagente_amazon_queue.py")
spec = importlib.util.spec_from_file_location("amazon_queue", MODULE)
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)

def audit(issues):
    return {"schema_version": 1, "mode": "read_only", "publication_allowed": False, "issues": issues}

def issue(page, url, *codes):
    return {"page": page, "url": url, "issues": list(codes)}

class AmazonQueueTests(unittest.TestCase):
    def test_empty_audit_is_valid_and_never_fabricates_sales(self):
        result = queue_module.make_queue(audit([]))
        self.assertEqual(result["total_review_items"], 0)
        self.assertIsNone(result["growth_opportunities"]["commission_revenue"])
        self.assertIsNone(result["growth_opportunities"]["attributed_orders"])
        self.assertFalse(result["publication_allowed"])

    def test_highest_risk_comes_first(self):
        result = queue_module.make_queue(audit([
            issue("z.html", "https://amazon.es/a", "no_affiliate_disclosure_found"),
            issue("b.html", "https://amazon.es.evil.test/b", "unapproved_destination"),
            issue("a.html", "http://amazon.es/c", "non_https")
        ]))
        self.assertEqual([item["priority"] for item in result["queue"]], ["critical", "high", "medium"])
        self.assertEqual(result["priority_counts"], {"critical": 1, "high": 1, "medium": 1})

    def test_multiple_findings_for_same_link_are_grouped(self):
        result = queue_module.make_queue(audit([
            issue("a.html", "https://amazon.es/a", "missing_affiliate_tag"),
            issue("a.html", "https://amazon.es/a", "missing_sponsored_or_nofollow"),
            issue("a.html", "https://amazon.es/a", "missing_affiliate_tag")
        ]))
        self.assertEqual(result["total_review_items"], 1)
        self.assertEqual(len(result["queue"][0]["finding_codes"]), 2)
        self.assertFalse(result["queue"][0]["automated_fix_allowed"])

    def test_deterministic_order(self):
        items = [
            issue("z.html", "https://amazon.es/z", "missing_affiliate_tag"),
            issue("a.html", "https://amazon.es/a", "missing_affiliate_tag")
        ]
        first = queue_module.make_queue(audit(items))
        second = queue_module.make_queue(audit(list(reversed(items))))
        self.assertEqual(first, second)

    def test_reject_publishable_audit(self):
        data = audit([])
        data["publication_allowed"] = True
        with self.assertRaises(ValueError):
            queue_module.make_queue(data)

    def test_reject_missing_evidence(self):
        data = audit([])
        del data["issues"]
        with self.assertRaises(ValueError):
            queue_module.make_queue(data)

    def test_reject_unknown_problem_code(self):
        with self.assertRaises(ValueError):
            queue_module.make_queue(audit([issue("index.html", "https://amazon.es", "made_up_issue")]))

    def test_seo_protection_cannot_be_bypassed(self):
        result = queue_module.make_queue(audit([issue("foo.html", "https://amazon.es/a", "invalid_url")]))
        self.assertFalse(result["seo_safety"]["rewrite_indexed_html"])
        self.assertFalse(result["seo_safety"]["change_urls_canonicals_or_sitemaps"])
        self.assertFalse(result["seo_safety"]["change_review_dates"])
        self.assertTrue(result["requires_human_approval"])

if __name__ == "__main__":
    unittest.main()
