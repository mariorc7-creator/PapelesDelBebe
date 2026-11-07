import importlib.util
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

P=Path(__file__).with_name("superagente_semantic_evidence.py")
sp=importlib.util.spec_from_file_location("semantic",P)
sem=importlib.util.module_from_spec(sp);sp.loader.exec_module(sem)
URL="https://www.juntaex.es/w/natalidad"
PAGE="https://www.papelesdelbebe.es/comunidades/extremadura/"
FILE="comunidades/extremadura/index.html"
SOURCE="Las ayudas por nacimiento son de 500 euros para las familias elegibles. El plazo de solicitud es de 30 días hábiles."
HTML='''<!doctype html><html><head><title>Extremadura</title></head><body><header>Inicio</header>
<main><h1>Ayudas en Extremadura</h1><p>Convocatoria anterior: 300 euros.</p></main>
<footer>Footer</footer></body></html>'''

class SemanticEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.file=self.root/FILE
        self.file.parent.mkdir(parents=True)
        self.file.write_text(HTML,encoding="utf-8")
        self.watchlist={"sources":[{"url":URL,"page":PAGE}]}
        self.report={"results":[{"url":URL,"status":"changed_needs_review","sha256":sha256(SOURCE.encode()).hexdigest()}]}
        self.snapshots={"snapshots":[{"url":URL,"text":SOURCE,"sha256":sha256(SOURCE.encode()).hexdigest()}]}
    def tearDown(self):self.temp.cleanup()
    def run_check(self):
        return sem.compare(self.watchlist,self.report,self.snapshots,self.root)
    def test_real_monetary_change_becomes_review_candidate(self):
        r=self.run_check()
        self.assertGreaterEqual(r["candidate_count"],1)
        self.assertFalse(r["auto_publish_allowed"])
        self.assertEqual(r["verified_legal_changes"],0)
        self.assertEqual(r["automatic_edits"],0)
        self.assertIn("500 euros",r["results"][0]["candidates"][0]["source_excerpt"])
    def test_source_snapshot_must_match_report_sha(self):
        self.snapshots["snapshots"][0]["text"]="Changed source 700 euros."
        with self.assertRaises(ValueError):self.run_check()
    def test_unchanged_never_generates_revision_candidate(self):
        self.report["results"][0]["status"]="unchanged"
        self.assertEqual(self.run_check()["candidate_count"],0)
    def test_failed_capture_does_not_claim_legal_change(self):
        self.report["results"][0]={"url":URL,"status":"fetch_failed"}
        self.snapshots["snapshots"]=[]
        r=self.run_check()
        self.assertEqual(r["results"][0]["status"],"not_comparable")
    def test_missing_snapshots_block(self):
        self.snapshots["snapshots"]=[]
        with self.assertRaises(ValueError):self.run_check()
    def test_unknown_official_source_blocks(self):
        self.report["results"][0]["url"]="https://evil.test"
        with self.assertRaises(ValueError):self.run_check()
    def test_outside_site_mapping_blocks(self):
        self.watchlist["sources"][0]["page"]="https://evil.test/foo/"
        with self.assertRaises(ValueError):self.run_check()
    def test_nonexistent_site_file_blocks(self):
        self.file.unlink()
        with self.assertRaises(ValueError):self.run_check()
    def test_page_with_matching_claim_yields_no_numeric_candidate(self):
        self.file.write_text(HTML.replace("300 euros","500 euros y plazo de 30 días"),encoding="utf-8")
        self.assertEqual(self.run_check()["candidate_count"],0)
    def test_missing_report_blocks(self):
        self.report["results"]=[]
        with self.assertRaises(ValueError):self.run_check()
    def test_duplicate_captures_block(self):
        self.snapshots["snapshots"].append(self.snapshots["snapshots"][0])
        with self.assertRaises(ValueError):self.run_check()
    def test_no_arbitrary_html_replacement(self):
        r=self.run_check()
        self.assertNotIn("replacement",r["results"][0]["candidates"][0])
        self.assertEqual(self.file.read_text(encoding="utf-8"),HTML)
if __name__=="__main__":unittest.main()
