#!/usr/bin/env python3
"""Offline regression tests for claim linkage and stale-text blocking."""
import importlib.util
import unittest
from datetime import date
from pathlib import Path
spec = importlib.util.spec_from_file_location("linked", Path(__file__).with_name("superagente_linked_triage.py"))
import sys
sys.path.insert(0, str(Path(__file__).parent))
linked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linked)
SOURCE = {"page": "https://www.papelesdelbebe.es/ayudas/",
          "claim_id": "abc123", "paragraph_sha256": "hash123", "kind": "amount",
          "published_value": "100 euros", "official_value": "200 euros",
          "source_url": "https://www.boe.es/", "source_excerpt": "Ejemplo",
          "consulted_on": "2026-11-06", "effective_on": "2026-01-01",
          "jurisdiction": "España", "reviewer": "editor"}
INVENTORY = {"pages": [{"url": SOURCE["page"],
                        "claims": [{"claim_id": "abc123", "paragraph_sha256": "hash123",
                                    "published_value": "100 euros", "kind": "amount",
                                    "selector_hint": "p:nth-of-type(1)"}]}]}

class LinkTests(unittest.TestCase):
    def check(self, claim=SOURCE, inventory=INVENTORY):
        return linked.reconcile(inventory, {"claims": [claim]}, today=date(2026, 11, 6))["results"][0]
    def test_matches_anchored_and_non_publishable(self):
        result = self.check()
        self.assertEqual(result["status"], "difference_needs_review")
        self.assertFalse(result["publishable"])
    def test_stale_paragraph_blocked(self):
        self.assertIn("stale:paragraph", self.check({**SOURCE, "paragraph_sha256": "old"})["errors"])
    def test_altered_published_value_blocked(self):
        self.assertIn("stale:published_value", self.check({**SOURCE, "published_value": "99 euros"})["errors"])
    def test_missing_claim_blocked(self):
        self.assertIn("missing:inventory_claim", self.check({**SOURCE, "claim_id": "missing"})["errors"])
    def test_kind_mismatch_blocked(self):
        self.assertIn("mismatch:kind", self.check({**SOURCE, "kind": "deadline"})["errors"])
    def test_duplicate_submissions_blocked(self):
        report = linked.reconcile(INVENTORY, {"claims": [SOURCE, SOURCE]}, today=date(2026, 11, 6))
        self.assertIn("duplicate:comparison", report["results"][1]["errors"])
    def test_invalid_source_blocked(self):
        self.assertIn("invalid:source_url", self.check({**SOURCE, "source_url": "http://example.com/"})["errors"])
    def test_duplicate_inventory_ambiguous(self):
        duplicated = {"pages": [INVENTORY["pages"][0], INVENTORY["pages"][0]]}
        self.assertIn("ambiguous:claim", self.check(inventory=duplicated)["errors"])
    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            linked.reconcile(INVENTORY, {"claims": []})
    def test_matching_text_still_non_publishable(self):
        result = self.check({**SOURCE, "official_value": "100 euros"})
        self.assertEqual(result["status"], "text_matches_needs_review")
        self.assertFalse(result["publishable"])

if __name__ == "__main__":
    unittest.main()
