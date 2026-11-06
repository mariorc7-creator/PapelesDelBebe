#!/usr/bin/env python3
"""Offline regression tests for the evidence gate."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("gate", Path(__file__).with_name("superagente_evidence_gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
BASE = dict(page="/ayudas/", claim="Cuantía de la ayuda", jurisdiction="Cataluña",
            source_url="https://www.gencat.cat/", source_title="Ficha oficial",
            consulted_on="2026-11-06", effective_on="2026-01-01",
            evidence_excerpt="Extracto verificable", verdict="coincide", reviewer="editor")

class EvidenceGateTests(unittest.TestCase):
    def test_valid_review(self):
        self.assertEqual(gate.validate(BASE), [])
    def test_missing_evidence(self):
        r = {**BASE, "evidence_excerpt": ""}
        self.assertIn("missing:evidence_excerpt", gate.validate(r))
    def test_insecure_source(self):
        r = {**BASE, "source_url": "http://example.org"}
        self.assertIn("invalid:source_url", gate.validate(r))
    def test_difference_needs_correction(self):
        r = {**BASE, "verdict": "difiere"}
        self.assertIn("missing:proposed_correction", gate.validate(r))
    def test_unverified_never_publishes(self):
        r = {**BASE, "verdict": "no_verificable", "approved_for_publication": True}
        self.assertIn("blocked:unverified_publication", gate.validate(r))
    def test_review_is_not_publication(self):
        r = {**BASE, "approved_for_publication": True}
        self.assertIn("blocked:publication_requires_diff", gate.validate(r))

if __name__ == "__main__":
    unittest.main()
