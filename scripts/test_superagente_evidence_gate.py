#!/usr/bin/env python3
"""Regression tests: evidence validation fails closed."""
import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location("gate", Path(__file__).with_name("superagente_evidence_gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
BASE = dict(page="/ayudas/", claim="Cuantía", jurisdiction="Cataluña",
            source_url="https://www.gencat.cat/", source_title="Ficha oficial",
            consulted_on="2026-11-06", effective_on="2026-01-01",
            evidence_excerpt="Extracto verificable", verdict="coincide", reviewer="editor")

class EvidenceGateTests(unittest.TestCase):
    def test_valid_review(self):
        self.assertEqual(gate.validate(BASE), [])
    def test_missing_evidence(self):
        self.assertIn("missing:evidence_excerpt", gate.validate({**BASE, "evidence_excerpt": ""}))
    def test_insecure_source(self):
        self.assertIn("invalid:source_url", gate.validate({**BASE, "source_url": "http://example.org"}))
    def test_invalid_url_port(self):
        self.assertIn("invalid:source_url", gate.validate({**BASE, "source_url": "https://example.org:8080/"}))
    def test_difference_needs_correction(self):
        self.assertIn("missing:proposed_correction", gate.validate({**BASE, "verdict": "difiere"}))
    def test_difference_with_correction_is_valid(self):
        self.assertEqual(gate.validate({**BASE, "verdict": "difiere", "proposed_correction": "Corregir cuantía"}), [])
    def test_unverified_never_publishes(self):
        self.assertIn("blocked:publication_approval_not_supported", gate.validate({**BASE, "verdict": "no_verificable", "approved_for_publication": True}))
    def test_review_is_not_publication(self):
        self.assertIn("blocked:publication_approval_not_supported", gate.validate({**BASE, "approved_for_publication": True}))
    def test_non_dict_record(self):
        self.assertEqual(gate.validate(None), ["invalid:record"])
    def test_bad_date(self):
        self.assertIn("invalid:effective_on", gate.validate({**BASE, "effective_on": "today"}))
    def test_future_consultation(self):
        future = (date.today() + timedelta(days=1)).isoformat()
        self.assertIn("future:consulted_on", gate.validate({**BASE, "consulted_on": future}))

if __name__ == "__main__":
    unittest.main()
