import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("superagente_official_baseline.py")
s=importlib.util.spec_from_file_location("official_baseline",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
URL="https://www.euskadi.eus/ayudas-mensuales-a-familias-con-hijas-o-hijos/web01-a2famil/es/"
A="a"*64
B="b"*64
def watch():return {"sources":[{"url":URL}]}
def result(status,sha=None):
    a={"url":URL,"status":status}
    if sha is not None:a["sha256"]=sha
    return {"results":[a]}
class BaselineTest(unittest.TestCase):
    def test_first_capture_is_candidate_only(self):
        r=m.candidate_baseline(watch(),result("baseline_missing",A))
        self.assertEqual(r["baseline_candidate"],{URL:A})
        self.assertTrue(r["requires_manual_commit"])
        self.assertFalse(r["publication_allowed"])
    def test_changed_cannot_replace_baseline(self):
        r=m.candidate_baseline(watch(),result("changed_needs_review",B),{URL:A})
        self.assertEqual(r["baseline_candidate"][URL],A)
        self.assertEqual(r["pending"][0]["new_sha256"],B)
    def test_unchanged_preserves_baseline(self):
        r=m.candidate_baseline(watch(),result("unchanged",A),{URL:A})
        self.assertEqual(r["baseline_candidate"][URL],A)
        self.assertEqual(r["pending"],[])
    def test_failed_source_cannot_bootstrap(self):
        r=m.candidate_baseline(watch(),result("fetch_failed"))
        self.assertEqual(r["baseline_candidate"],{})
    def test_failed_source_preserves_existing(self):
        r=m.candidate_baseline(watch(),result("fetch_failed"),{URL:A})
        self.assertEqual(r["baseline_candidate"],{URL:A})
    def test_wrong_hash_rejected(self):
        with self.assertRaises(ValueError):m.candidate_baseline(watch(),result("baseline_missing","madeup"))
    def test_report_omission_rejected(self):
        with self.assertRaises(ValueError):m.candidate_baseline(watch(),{"results":[]})
    def test_status_baseline_mismatch_rejected(self):
        with self.assertRaises(ValueError):m.candidate_baseline(watch(),result("unchanged",B),{URL:A})
    def test_unmapped_old_url_rejected(self):
        with self.assertRaises(ValueError):m.candidate_baseline(watch(),result("baseline_missing",A),{"https://fake.example":A})
if __name__=="__main__":unittest.main()
