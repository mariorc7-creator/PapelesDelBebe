#!/usr/bin/env python3
"""Unit tests for source-anchored editorial batch orchestration."""
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location("batch", Path(__file__).with_name("superagente_v03_editorial_batch.py"))
import sys
sys.path.insert(0,str(Path(__file__).parent))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
P="https://www.papelesdelbebe.es/deduccion-maternidad/"
Q="https://www.papelesdelbebe.es/empadronar-bebe/"
R="https://www.papelesdelbebe.es/ayuda-nacimiento-cataluna/"
def wp():
    return {"as_of":"2026-11-06","items":[
        {"url":P,"priority":0,"category":"ayudas","action":"retrieve_and_verify_official_evidence"},
        {"url":Q,"priority":1,"category":"tramites","action":"locate_specific_official_document"},
        {"url":R,"priority":0,"category":"ayudas","action":"retrieve_and_verify_official_evidence"}]}
def rp(*results): return {"results":list(results)}
class EditorialBatchTests(unittest.TestCase):
    def test_no_receipts_never_approve(self):
        result=mod.compile_batch(wp(),rp())
        self.assertEqual(result["counts"]["no_receipt"],3)
        self.assertFalse(result["publication_allowed"])
        self.assertTrue(all(not t["publishable"] for t in result["batch"]))
    def test_stale_receipt_takes_first_within_priority(self):
        result=mod.compile_batch(wp(),rp({"page":R,"status":"blocked","errors":["stale:page_hash"]}))
        self.assertEqual(result["batch"][0]["page"],R)
        self.assertEqual(result["batch"][0]["state"],"stale_snapshot")
    def test_invalid_receipt_requires_repair(self):
        result=mod.compile_batch(wp(),rp({"page":P,"status":"blocked","errors":["missing:source_deadline"]}))
        self.assertEqual(result["batch"][0]["next_action"],"repair_receipt_evidence")
    def test_complete_receipt_only_signoff_pending(self):
        result=mod.compile_batch(wp(),rp({"page":P,"status":"ready_for_editorial_signoff","errors":[]}))
        self.assertEqual(result["batch"][0]["state"],"awaiting_independent_signoff")
        self.assertFalse(result["batch"][0]["independently_verified"])
    def test_limit_works(self):
        result=mod.compile_batch(wp(),rp(),2)
        self.assertEqual(result["batch_size"],2)
        self.assertEqual(result["total_backlog"],3)
    def test_unknown_page_blocks(self):
        with self.assertRaises(ValueError):
            mod.compile_batch(wp(),rp({"page":"https://example.org/a/","status":"blocked"}))
    def test_duplicate_receipts_block(self):
        with self.assertRaises(ValueError):
            mod.compile_batch(wp(),rp({"page":P,"status":"blocked"},{"page":P,"status":"blocked"}))
    def test_duplicate_workplan_pages_block(self):
        data=wp();data["items"].append(data["items"][0])
        with self.assertRaises(ValueError): mod.compile_batch(data,rp())
    def test_invalid_limit(self):
        with self.assertRaises(ValueError): mod.compile_batch(wp(),rp(),0)
    def test_unknown_receipt_status_blocks(self):
        with self.assertRaises(ValueError):
            mod.compile_batch(wp(),rp({"page":P,"status":"approved"}))
    def test_deterministic_order(self):
        a=mod.compile_batch(wp(),rp())
        b=mod.compile_batch(wp(),rp())
        self.assertEqual(a,b)
    def test_no_content_or_review_date_changes(self):
        out=mod.compile_batch(wp(),rp({"page":P,"status":"ready_for_editorial_signoff"}))
        self.assertTrue(all(t["changes_review_date"] is False for t in out["batch"]))
if __name__=="__main__":
    unittest.main()
