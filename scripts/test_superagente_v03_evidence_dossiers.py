#!/usr/bin/env python3
"""Offline dossier tests: no fabricated legal evidence or approval."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
spec=importlib.util.spec_from_file_location("dossiers",Path(__file__).with_name("superagente_v03_evidence_dossiers.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
PAGE="https://www.papelesdelbebe.es/deduccion-maternidad/"
SOURCE="https://sede.agenciatributaria.gob.es/Sede/procedimientos/GZ25.shtml"
def batch(pages=None):
    return {"publication_allowed":False, "batch":pages or [{"page":PAGE,"priority":0,"state":"no_receipt"}]}
def refs(items=None):
    return {"references":[{"page":PAGE,"authority":"AEAT",
                           "status":"candidate_needs_document_review",
                           "source_url":SOURCE,
                           "approved_host":"sede.agenciatributaria.gob.es"}] if items is None else items}
def routes(items=None):
    return {"routes":[{"page":PAGE,"authority":"AEAT","jurisdiction":"ES"}] if items is None else items}
class DossierTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.file=self.root/"deduccion-maternidad/index.html"
        self.file.parent.mkdir(parents=True)
        self.file.write_text("<main>Modelo 140</main>",encoding="utf-8")
    def tearDown(self): self.tmp.cleanup()
    def run_report(self,b=None,r=None,rt=None):
        return mod.dossiers(b or batch(), r or refs(), rt or routes(), self.root)
    def test_snapshot_and_citation_only(self):
        raw=self.file.read_bytes()
        report=self.run_report()
        row=report["dossiers"][0]
        self.assertEqual(row["page_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(row["candidate_source_url"],SOURCE)
        self.assertFalse(row["document_reviewed"])
        self.assertEqual(report["source_claims_verified"],0)
        self.assertEqual(self.file.read_bytes(),raw)
    def test_all_seven_evidence_slots_unverified(self):
        row=self.run_report()["dossiers"][0]
        self.assertEqual(len(row["evidence_slots"]),7)
        self.assertTrue(all(x["state"]=="not_evaluated" for x in row["evidence_slots"].values()))
    def test_missing_source_stays_pending(self):
        row=self.run_report(r=refs([]))["dossiers"][0]
        self.assertIsNone(row["candidate_source_url"])
        self.assertEqual(row["source_status"],"source_needed")
    def test_duplicate_page_blocks(self):
        with self.assertRaises(ValueError):
            self.run_report(b=batch([{"page":PAGE},{"page":PAGE}]))
    def test_unapproved_batch_required(self):
        with self.assertRaises(ValueError):
            self.run_report(b={**batch(),"publication_allowed":True})
    def test_unknown_authority_blocks(self):
        with self.assertRaises(ValueError):
            self.run_report(rt=routes([{"page":PAGE,"authority":"Otra"}]))
    def test_unsafe_source_host_blocks(self):
        item=refs()["references"][0]
        with self.assertRaises(ValueError):
            self.run_report(r=refs([{**item,"source_url":"https://example.com/a"}]))
    def test_homepage_source_blocks(self):
        item=refs()["references"][0]
        with self.assertRaises(ValueError):
            self.run_report(r=refs([{**item,"source_url":"https://sede.agenciatributaria.gob.es/"}]))
    def test_duplicate_candidate_blocks(self):
        item=refs()["references"][0]
        with self.assertRaises(ValueError):
            self.run_report(r=refs([item,item]))
    def test_missing_html_blocks(self):
        self.file.unlink()
        with self.assertRaises(ValueError): self.run_report()
    def test_wrong_site_blocks(self):
        with self.assertRaises(ValueError):
            self.run_report(b=batch([{"page":"https://other.example/deduccion-maternidad/"}]))
    def test_missing_route_for_existing_candidate_blocks(self):
        with self.assertRaises(ValueError):
            self.run_report(rt=routes([]))
if __name__=="__main__":
    unittest.main()
