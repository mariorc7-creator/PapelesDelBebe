import importlib.util
from pathlib import Path
from hashlib import sha256
import unittest

P=Path(__file__).with_name("superagente_fast_path.py")
s=importlib.util.spec_from_file_location("fast_path",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
SOURCES=["https://official.example/a","https://official.example/b","https://official.example/c"]
def data(statuses):
    wl={"sources":[{"url":u,"page":"https://www.papelesdelbebe.es/a/"} for u in SOURCES]}
    rep={"results":[]}
    snap={"snapshots":[]}
    for u,status in zip(SOURCES,statuses):
        item={"url":u,"status":status}
        if status in ("unchanged","changed_needs_review","baseline_missing"):
            h=sha256(u.encode()).hexdigest()
            item["sha256"]=h
            snap["snapshots"].append({"url":u,"sha256":h,"text":u})
        rep["results"].append(item)
    return wl,rep,snap

class FastPathTests(unittest.TestCase):
    def test_no_changes_skips_expensive_checks(self):
        out=m.plan(*data(["unchanged","unchanged","unchanged"]))
        self.assertTrue(out["expensive_review_skipped"])
        self.assertEqual(out["changed_count"],0)
        self.assertEqual(out["filtered"]["watchlist"]["sources"],[])
        self.assertEqual(out["filtered"]["snapshots"]["snapshots"],[])
        self.assertFalse(out["auto_publish_allowed"])
    def test_one_change_only_one_expensive_source(self):
        out=m.plan(*data(["unchanged","changed_needs_review","unchanged"]))
        self.assertEqual(out["changed_urls"],[SOURCES[1]])
        self.assertEqual(out["changed_count"],1)
        self.assertEqual(len(out["filtered"]["snapshots"]["snapshots"]),1)
        self.assertEqual(len(out["filtered"]["report"]["results"]),1)
        self.assertFalse(out["expensive_review_skipped"])
    def test_failure_is_reported_but_no_semantic_for_it(self):
        out=m.plan(*data(["fetch_failed","unchanged","unchanged"]))
        self.assertEqual(out["changed_count"],0)
        self.assertEqual(out["followup_required"][0]["status"],"fetch_failed")
    def test_first_baseline_is_not_misreported_as_change(self):
        out=m.plan(*data(["baseline_missing","unchanged","unchanged"]))
        self.assertEqual(out["changed_count"],0)
        self.assertEqual(out["followup_required"][0]["status"],"baseline_missing")
    def test_concurrent_change_and_fetch_failure(self):
        out=m.plan(*data(["changed_needs_review","fetch_failed","unchanged"]))
        self.assertEqual(out["changed_count"],1)
        self.assertEqual(len(out["followup_required"]),1)
    def test_status_report_requires_every_source(self):
        wl,rep,snap=data(["unchanged"]*3)
        rep["results"].pop()
        with self.assertRaises(ValueError):m.plan(wl,rep,snap)
    def test_changed_source_must_have_fresh_capture(self):
        wl,rep,snap=data(["changed_needs_review","unchanged","unchanged"])
        snap["snapshots"].pop(0)
        with self.assertRaises(ValueError):m.plan(wl,rep,snap)
    def test_changed_source_hash_must_match_report(self):
        wl,rep,snap=data(["changed_needs_review","unchanged","unchanged"])
        snap["snapshots"][0]["sha256"]="0"*64
        with self.assertRaises(ValueError):m.plan(wl,rep,snap)
    def test_duplicate_report_is_not_trusted(self):
        wl,rep,snap=data(["unchanged"]*3)
        rep["results"].append(rep["results"][0])
        with self.assertRaises(ValueError):m.plan(wl,rep,snap)
    def test_unknown_source_is_not_trusted(self):
        wl,rep,snap=data(["unchanged"]*3)
        snap["snapshots"].append({"url":"https://evil.example/","sha256":"0"*64})
        with self.assertRaises(ValueError):m.plan(wl,rep,snap)
    def test_invalid_state_rejected(self):
        wl,rep,snap=data(["unchanged"]*3)
        rep["results"][0]["status"]="auto_approved"
        with self.assertRaises(ValueError):m.plan(wl,rep,snap)
    def test_all_sources_changed_are_preserved(self):
        out=m.plan(*data(["changed_needs_review"]*3))
        self.assertEqual(out["changed_count"],3)
    def test_never_edits_site_or_claims_review(self):
        out=m.plan(*data(["unchanged"]*3))
        self.assertFalse(out["website_edited"])
        self.assertIn("does not certify legal currency",out["warning"])
if __name__=="__main__":unittest.main()
