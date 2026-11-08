import importlib.util
from datetime import date
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

P=Path(__file__).with_name("superagente_status_autopublisher.py")
spec=importlib.util.spec_from_file_location("status_autopublisher",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
URL="https://www.juntaex.es/w/0702824"
PATH="comunidades/extremadura/index.html"
START="<!-- superagente:extremadura-2026:start -->"
END="<!-- superagente:extremadura-2026:end -->"
TEXT='''<!doctype html><html><head><title>Ayudas Extremadura</title>
<meta name="robots" content="index, follow"><link rel="canonical" href="https://www.papelesdelbebe.es/comunidades/extremadura/">
<script type="application/ld+json">{"dateModified":"2026-08-15"}</script></head>
<body><header><nav><a href="/">Inicio</a></nav></header><main><h1>Ayudas</h1>
<p>''' + START + '''<strong>Ayuda rural por natalidad de 500 €: en plazo.</strong>''' + END + '''</p></main>
<footer>Pie</footer></body></html>'''
SOURCE_OPEN=("Ayudas por natalidad a otorgar a las familias residentes en Extremadura. "
             "En plazo. Plazo de presentación Desde: 07/08/2026 Hasta: 30/09/2026. "
             "La ayuda tendrá una cuantía de 500 euros.")
SOURCE_CLOSED=SOURCE_OPEN.replace("En plazo.","Fuera de plazo.")
POLICY={"schema_version":1,"publication_allowed":False,
        "rules":[{"id":"extremadura-natalidad-2026","type":"extremadura_2026_status",
                  "source_url":URL,"page":PATH}]}
def inputs(text,status="changed_needs_review"):
    digest=sha256(text.encode()).hexdigest()
    return {"results":[{"url":URL,"sha256":digest,"status":status}]},{"snapshots":[{"url":URL,"sha256":digest,"text":text}]}

class AutoStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.root=Path(self.tmp.name)
        self.file=self.root/PATH;self.file.parent.mkdir(parents=True)
        self.file.write_text(TEXT,encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def call(self,source=SOURCE_CLOSED,when=date(2026,11,8),policy=POLICY):
        report,snapshots=inputs(source)
        return m.plan(policy,report,snapshots,self.root,when)
    def test_real_calendar_closure_is_a_bounded_content_change(self):
        result=self.call()
        self.assertEqual(len(result["edits"]),1)
        self.assertFalse(result["incidents"])
        self.assertIn("fuera de plazo",result["edits"][0]["new_content"])
        self.assertEqual(self.file.read_text(),TEXT)
        self.assertFalse(result["seo_fields_changed"])
    def test_apply_writes_only_managed_content(self):
        result=self.call()
        out=m.apply(self.root,result,True)
        self.assertEqual(out["changed_pages"],1)
        modified=self.file.read_text()
        self.assertIn("<title>Ayudas Extremadura</title>",modified)
        self.assertIn('rel="canonical" href="https://www.papelesdelbebe.es/comunidades/extremadura/"',modified)
        self.assertIn("fuera de plazo",modified)
        self.assertIn('"dateModified":"2026-08-15"',modified)
    def test_no_new_changes_no_redeploy(self):
        text=TEXT.replace("en plazo.","fuera de plazo.")
        self.file.write_text(text,encoding="utf-8")
        result=self.call()
        self.assertEqual(result["edits"],[])
        self.assertEqual(m.apply(self.root,result,True)["changed_pages"],0)
    def test_calendar_and_source_disagree_blocks(self):
        result=self.call(SOURCE_OPEN)
        self.assertEqual(result["edits"],[])
        self.assertEqual(len(result["incidents"]),1)
    def test_other_status_claim_blocks_partial_page_change(self):
        self.file.write_text(TEXT.replace("<h1>Ayudas</h1>","<h1>Ayudas</h1><p>Convocatoria abierta.</p>"))
        result=self.call()
        self.assertEqual(len(result["incidents"]),1)
        self.assertEqual(result["edits"],[])
        with self.assertRaises(ValueError):m.apply(self.root,result,True)
    def test_missing_source_hash_blocks(self):
        report,snapshots=inputs(SOURCE_CLOSED)
        snapshots["snapshots"][0]["text"]+="altered"
        result=m.plan(POLICY,report,snapshots,self.root,date(2026,11,8))
        self.assertEqual(result["incidents"][0]["reason"],"source_unavailable_or_stale")
    def test_fetch_error_does_not_change_page(self):
        report,snapshots=inputs(SOURCE_CLOSED,status="fetch_failed")
        result=m.plan(POLICY,report,snapshots,self.root,date(2026,11,8))
        self.assertEqual(result["edits"],[])
    def test_unknown_new_year_requires_separate_approval(self):
        result=self.call(SOURCE_CLOSED.replace("2026","2027"),date(2027,11,8))
        self.assertEqual(result["edits"],[])
        self.assertTrue(result["incidents"])
    def test_rule_not_allowlisted_blocks(self):
        policy={"schema_version":1,"publication_allowed":False,
                "rules":[{**POLICY["rules"][0],"source_url":"https://evil.example/"}]}
        with self.assertRaises(ValueError):self.call(policy=policy)
    def test_dry_run_never_modifies_html(self):
        result=self.call()
        self.assertEqual(m.apply(self.root,result,False)["changed_pages"],0)
        self.assertEqual(self.file.read_text(),TEXT)
    def test_duplicate_managed_marker_blocks(self):
        self.file.write_text(TEXT+START)
        result=self.call()
        self.assertTrue(result["incidents"])
    def test_stale_document_cannot_be_applied(self):
        decision=self.call()
        self.file.write_text(TEXT+" ")
        with self.assertRaises(ValueError):m.apply(self.root,decision,True)
    def test_page_already_has_conflicting_seo_meta_holds_for_review(self):
        self.file.write_text(TEXT.replace("<title>Ayudas Extremadura</title>","<title>Convocatoria abierta Extremadura</title>"))
        decision=self.call()
        self.assertTrue(decision["incidents"])
if __name__=="__main__":unittest.main()
