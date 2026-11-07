#!/usr/bin/env python3
"""Offline regression suite for documentary evidence comparison."""
import hashlib
import importlib.util
import unittest
from datetime import date
from pathlib import Path

spec = importlib.util.spec_from_file_location("documentary", Path(__file__).with_name("superagente_documentary_evidence.py"))
doc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doc)
TEXT = "El trámite de ejemplo establece un plazo de 15 días. Documento de ejemplo."
CLAIM = {"source_url": "https://www.boe.es/example", "source_excerpt": "un plazo de 15 días",
         "consulted_on": "2026-11-06"}
CAPTURE = {"source_url": CLAIM["source_url"], "text": TEXT,
           "sha256": hashlib.sha256(TEXT.encode("utf-8")).hexdigest(),
           "captured_on": "2026-11-06"}

class DocumentaryTests(unittest.TestCase):
    def verify(self, claim=None, capture=None):
        return doc.check({"claims": [CLAIM if claim is None else claim]},
                         {"captures": [CAPTURE if capture is None else capture]})["results"][0]
    def test_excerpt_present_but_not_publishable(self):
        r = self.verify()
        self.assertEqual(r["status"], "excerpt_present_in_supplied_capture")
        self.assertFalse(r["publishable"])
    def test_incorrect_excerpt(self):
        self.assertIn("missing:excerpt_in_capture", self.verify(claim={**CLAIM, "source_excerpt": "30 días"})["errors"])
    def test_invalid_hash(self):
        self.assertIn("mismatch:capture_hash", self.verify(capture={**CAPTURE, "sha256": "fake"})["errors"])
    def test_missing_capture(self):
        r = doc.check({"claims": [CLAIM]}, {"captures": []})
        self.assertEqual(r["results"][0]["errors"], ["missing:capture"])
    def test_duplicate_capture(self):
        r = doc.check({"claims": [CLAIM]}, {"captures": [CAPTURE, CAPTURE]})
        self.assertIn("duplicate:capture", r["results"][0]["errors"])
    def test_future_capture(self):
        r = self.verify(capture={**CAPTURE, "captured_on": "2099-01-01"})
        self.assertIn("future:capture_or_consultation", r["errors"])
    def test_out_of_order_consultation(self):
        r = self.verify(claim={**CLAIM, "consulted_on": "2026-11-05"})
        self.assertIn("stale:consultation_before_capture", r["errors"])
    def test_bad_dates(self):
        self.assertIn("invalid:capture_dates", self.verify(capture={**CAPTURE, "captured_on": "yesterday"})["errors"])
    def test_malformed_claim(self):
        r = doc.check({"claims": [None]}, {"captures": [CAPTURE]})
        self.assertEqual(r["results"][0]["status"], "blocked")
    def test_empty_claims(self):
        with self.assertRaises(ValueError):
            doc.check({"claims": []}, {"captures": [CAPTURE]})
    def test_whitespace_normalization(self):
        self.assertEqual(self.verify(claim={**CLAIM, "source_excerpt": "un   plazo de 15 días"})["status"],
                         "excerpt_present_in_supplied_capture")

if __name__ == "__main__":
    unittest.main()
