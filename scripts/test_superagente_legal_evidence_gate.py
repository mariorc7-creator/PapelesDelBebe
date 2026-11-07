import importlib.util
from copy import deepcopy
from datetime import date
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

DIR=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("superagente_legal_evidence_gate",DIR/"superagente_legal_evidence_gate.py")
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
URL="https://www.juntaex.es/w/0702824"
PAGE="https://www.papelesdelbebe.es/comunidades/extremadura/"
PATH="comunidades/extremadura/index.html"
SOURCE="La ayuda por nacimiento es de 500 euros para familias que cumplan los requisitos y estén dentro de plazo."
HTML='''<!doctype html><html><head><title>Extremadura</title></head><body><main><h1>Extremadura</h1><p>La ayuda es de 300 euros.</p></main></body></html>'''
def fingerprint(x):return sha256(x.encode()).hexdigest()

class LegalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.page=self.root/PATH;self.page.parent.mkdir(parents=True)
        self.page.write_text(HTML,encoding="utf-8")
        self.sources={"sources":[{"url":URL,"approved_host":"www.juntaex.es","page":PAGE}]}
        self.reports={"results":[{"url":URL,"status":"changed_needs_review","sha256":fingerprint(SOURCE)}]}
        self.snapshots={"snapshots":[{"url":URL,"sha256":fingerprint(SOURCE),"text":SOURCE}]}
        self.claim={"source_url":URL,"source_sha256":fingerprint(SOURCE),
            "source_quote":SOURCE,"page_sha256":fingerprint(HTML),"path":PATH,
            "old_claim":"300 euros","new_claim":"500 euros",
            "kind":"amount",
            "scope":{"jurisdiction":"Extremadura","benefit":"Natalidad","beneficiaries":"Familias elegibles",
                "effective_from":"2026-01-01","effective_until":"2026-12-31",
                "exceptions":"Consultar límites y requisitos","application_status":"open"},
            "legal_conflict_detected":False,
            "reviewer":{"name":"revisor","reviewed_at":date.today().isoformat(),
                "independent_factual_check":True,"scope_and_exceptions_checked":True,
                "evidence_ref":"ficha_oficial_vigente"}}
    def tearDown(self):self.tmp.cleanup()
    def check(self):
        return gate.verify({"schema_version":1,"publication_allowed":False,
                           "claims":[self.claim]},self.sources,self.reports,self.snapshots,self.root)
    def assert_blocks(self):
        with self.assertRaises(ValueError):self.check()
    def test_verified_documentary_record_is_not_auto_published(self):
        out=self.check()
        self.assertEqual(out["validated_count"],1)
        self.assertFalse(out["automatic_legal_truth_established"])
        self.assertFalse(out["automatic_publication_allowed"])
        self.assertEqual(self.page.read_text(),HTML)
    def test_missing_source_quote_blocks(self):
        self.claim["source_quote"]="something false long enough to be a quote";self.assert_blocks()
    def test_stale_source_blocks(self):
        self.snapshots["snapshots"][0]["text"]+=" changed";self.assert_blocks()
    def test_inconsistent_report_hash_blocks(self):
        self.reports["results"][0]["sha256"]="b"*64;self.assert_blocks()
    def test_mismatched_page_sha_blocks(self):
        self.page.write_text(HTML+"changed");self.assert_blocks()
    def test_unreviewed_claim_blocks(self):
        self.claim["reviewer"]["independent_factual_check"]=False;self.assert_blocks()
    def test_incomplete_scope_blocks(self):
        self.claim["scope"].pop("beneficiaries");self.assert_blocks()
    def test_uncertain_open_status_blocks(self):
        self.claim["scope"]["application_status"]="uncertain";self.assert_blocks()
    def test_missing_conflict_attestation_blocks(self):
        self.claim.pop("legal_conflict_detected");self.assert_blocks()
    def test_conflict_detected_blocks(self):
        self.claim["legal_conflict_detected"]=True;self.assert_blocks()
    def test_bad_date_order_blocks(self):
        self.claim["scope"]["effective_from"]="2027-01-01";self.assert_blocks()
    def test_future_editorial_attestation_blocks(self):
        self.claim["reviewer"]["reviewed_at"]="2099-01-01";self.assert_blocks()
    def test_closed_but_attested_is_not_automatically_published(self):
        self.claim["scope"]["application_status"]="closed"
        self.assertFalse(self.check()["automatic_publication_allowed"])
    def test_unmapped_page_blocks(self):
        self.sources["sources"][0]["page"]="https://evil.example/a/";self.assert_blocks()
    def test_source_redirect_host_mismatch_blocks(self):
        self.sources["sources"][0]["approved_host"]="evil.example";self.assert_blocks()
    def test_missing_source_capture_blocks(self):
        self.reports["results"][0]["status"]="fetch_failed";self.assert_blocks()
    def test_duplicate_claim_blocks(self):
        with self.assertRaises(ValueError):
            gate.verify({"schema_version":1,"publication_allowed":False,
                "claims":[self.claim,deepcopy(self.claim)]},
                self.sources,self.reports,self.snapshots,self.root)
    def test_html_changes_disallowed(self):
        self.claim["new_claim"]="<h1>500 euros</h1>";self.assert_blocks()
    def test_verified_record_generates_non_publishable_manifest(self):
        out=gate.to_branch_manifest(self.check(),date.today().isoformat())
        self.assertFalse(out["publication_allowed"])
        self.assertEqual(out["changes"][0]["search"],"300 euros")
        self.assertEqual(out["changes"][0]["replacement"],"500 euros")
        self.assertEqual(out["changes"][0]["source_sha256"],fingerprint(SOURCE))
    def test_unverified_report_rejected_for_manifest(self):
        with self.assertRaises(ValueError):
            gate.to_branch_manifest({"mode":"arbitrary","records":[]},date.today().isoformat())
    def test_multi_changes_same_page_requires_combined_review(self):
        report=self.check()
        report["records"].append(deepcopy(report["records"][0]))
        with self.assertRaises(ValueError):
            gate.to_branch_manifest(report,date.today().isoformat())
if __name__=="__main__":unittest.main()
