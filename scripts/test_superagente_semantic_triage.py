#!/usr/bin/env python3
"""Offline tests for claim triage; no external network calls."""
import importlib.util
import unittest
from datetime import date
from pathlib import Path

spec = importlib.util.spec_from_file_location("triage", Path(__file__).with_name("superagente_semantic_triage.py"))
triage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triage)
GOOD = {"page": "/ayudas/ejemplo/", "claim_id": "amount:1", "kind": "amount",
        "published_value": "100 euros", "official_value": "200 euros",
        "source_url": "https://www.boe.es/", "source_excerpt": "Referencia de ejemplo",
        "consulted_on": "2026-11-06", "effective_on": "2026-01-01",
        "jurisdiction": "España", "reviewer": "editor"}

class TriageTests(unittest.TestCase):
    def test_difference_is_not_publishable(self):
        result = triage.assess(GOOD, today=date(2026, 11, 6))
        self.assertEqual(result["status"], "difference_needs_review")
        self.assertFalse(result["publishable"])
        self.assertEqual(result["proposed_value"], "200 euros")
    def test_text_match_still_needs_review(self):
        result = triage.assess({**GOOD, "official_value": " 100  EUROS "}, today=date(2026, 11, 6))
        self.assertEqual(result["status"], "text_matches_needs_review")
        self.assertTrue(result["requires_human_or_verified_semantic_review"])
    def test_block_no_evidence(self):
        self.assertIn("missing:source_excerpt", triage.assess({**GOOD, "source_excerpt": ""})["errors"])
    def test_block_non_https(self):
        self.assertIn("invalid:source_url", triage.assess({**GOOD, "source_url": "http://boe.es"})["errors"])
    def test_block_future_effective_date(self):
        result = triage.assess({**GOOD, "effective_on": "2027-01-01"}, today=date(2026, 11, 6))
        self.assertIn("future:effective_on", result["errors"])
    def test_block_future_consultation(self):
        result = triage.assess({**GOOD, "consulted_on": "2027-01-01"}, today=date(2026, 11, 6))
        self.assertIn("future:consulted_on", result["errors"])
    def test_malformed_record(self):
        self.assertEqual(triage.assess(None)["status"], "blocked")
    def test_invalid_kind(self):
        self.assertIn("invalid:kind", triage.assess({**GOOD, "kind": "whatever"})["errors"])
    def test_empty_payload(self):
        with self.assertRaises(ValueError):
            triage.evaluate({"claims": []})
    def test_mixed_counts(self):
        report = triage.evaluate({"claims": [GOOD, {**GOOD, "official_value": "100 euros"}, {"bad": 1}]}, today=date(2026, 11, 6))
        self.assertEqual(report["counts"], {"blocked": 1, "difference_needs_review": 1, "text_matches_needs_review": 1})

if __name__ == "__main__":
    unittest.main()
