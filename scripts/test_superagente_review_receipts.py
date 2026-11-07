#!/usr/bin/env python3
"""Offline tests for complete, page-anchored editorial receipts."""
import hashlib
import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

spec = importlib.util.spec_from_file_location("receipts", Path(__file__).with_name("superagente_review_receipts.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
PAGE = "https://www.papelesdelbebe.es/ayuda-ejemplo/"
SOURCE = "https://tramits.gencat.cat/ca/tramits/tramits-temes/example"
def checks():
    return {key: {"finding": "confirmed", "reason": "Se ha comprobado el dato concreto para este supuesto.",
                  "source_url": SOURCE} for key in mod.REQUIRED_TOPICS}

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.file = self.root / "ayuda-ejemplo/index.html"
        self.file.parent.mkdir(parents=True)
        self.file.write_text("<h1>Ayuda vigente</h1>", encoding="utf-8")
        self.receipt = {"page": PAGE, "page_sha256": hashlib.sha256(self.file.read_bytes()).hexdigest(),
                        "reviewed_on": "2026-11-06", "reviewer": "Editor verificador",
                        "result": "unchanged", "checks": checks()}
    def tearDown(self): self.temp.cleanup()
    def evaluate(self, entries=None):
        return mod.evaluate({"schema_version": 1, "receipts": [self.receipt] if entries is None else entries},
                            {PAGE}, self.root, date(2026,11,6))
    def errors(self, entry):
        return self.evaluate([entry])["results"][0]["errors"]
    def test_valid_receipt_never_publishable(self):
        out = self.evaluate()
        self.assertEqual(out["blocked"], 0)
        self.assertFalse(out["results"][0]["publishable"])
        self.assertFalse(out["results"][0]["changes_review_date"])
    def test_no_html_modification(self):
        before = self.file.read_bytes()
        self.evaluate()
        self.assertEqual(self.file.read_bytes(), before)
    def test_missing_topic_blocks(self):
        c = checks(); c.pop("deadline")
        self.assertIn("missing:complete_topic_coverage", self.errors({**self.receipt, "checks": c}))
    def test_stale_snapshot_blocks(self):
        self.file.write_text("<h1>Cambiado</h1>", encoding="utf-8")
        self.assertIn("stale:page_hash", self.errors(self.receipt))
    def test_future_review_blocks(self):
        self.assertIn("invalid:future_review", self.errors({**self.receipt, "reviewed_on": "2099-01-01"}))
    def test_short_reason_blocks(self):
        c = checks(); c["amount"]["reason"] = "sí"
        self.assertIn("missing:reason_amount", self.errors({**self.receipt, "checks": c}))
    def test_missing_source_blocks(self):
        c = checks(); c["deadline"]["source_url"] = "http://example.org"
        self.assertIn("missing:source_deadline", self.errors({**self.receipt, "checks": c}))
    def test_unverifiable_cannot_mark_unchanged(self):
        c = checks(); c["amount"]["finding"] = "unverifiable"
        self.assertIn("inconsistent:unchanged", self.errors({**self.receipt, "checks": c}))
    def test_difference_cannot_mark_unchanged(self):
        c = checks(); c["amount"]["finding"] = "difference"
        self.assertIn("inconsistent:unchanged", self.errors({**self.receipt, "checks": c}))
    def test_changed_requires_difference(self):
        self.assertIn("inconsistent:change_proposed", self.errors({**self.receipt, "result": "change_proposed"}))
    def test_unknown_page_blocks(self):
        self.assertIn("invalid:page", self.errors({**self.receipt, "page": "https://www.papelesdelbebe.es/desconocida/"}))
    def test_duplicate_page_blocks(self):
        self.assertEqual(self.evaluate([self.receipt, self.receipt])["blocked"], 1)
    def test_empty_receipts_are_not_certification(self):
        self.assertEqual(self.evaluate([])["total"], 0)
    def test_invalid_schema_blocks(self):
        with self.assertRaises(ValueError):
            mod.evaluate({"schema_version": 2, "receipts": []}, {PAGE}, self.root)
if __name__=="__main__":
    unittest.main()
