from datetime import date
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import unittest

P=Path(__file__).with_name("superagente_verified_batch.py")
spec=importlib.util.spec_from_file_location("verified_batch",P)
batch=importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)
URL="https://www.juntaex.es/w/0702824"
PAGE="https://www.papelesdelbebe.es/comunidades/extremadura/"
PATH="comunidades/extremadura/index.html"
SOURCE="La ayuda por nacimiento se eleva a 500 euros para familias elegibles según la convocatoria de 2026."
HTML='''<!doctype html><html><head><title>Extremadura</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.papelesdelbebe.es/comunidades/extremadura/">
<script type="application/ld+json">{"dateModified":"2026-10-01"}</script>
</head><body><header><nav><a href="/">Inicio</a></nav></header><main><h1>Extremadura</h1>
<p>La ayuda anterior es de 300 euros.</p><p>Información revisada: 1 de octubre de 2026</p>
<p>Última revisión: <time datetime="2026-10-01">1 de octubre de 2026</time></p>
</main><footer>Pie</footer></body></html>'''
def sh(s): return sha256(s.encode()).hexdigest()

class VerifiedBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.root=Path(self.tmp.name)
        self.page=self.root/PATH;self.page.parent.mkdir(parents=True)
        self.page.write_text(HTML,encoding="utf-8")
        self.watchlist={"sources":[{"url":URL,"page":PAGE,"approved_host":"www.juntaex.es"}]}
        self.report={"results":[{"url":URL,"status":"changed_needs_review","sha256":sh(SOURCE)}]}
        self.snapshots={"snapshots":[{"url":URL,"sha256":sh(SOURCE),"text":SOURCE}]}
        self.claims={"schema_version":1,"publication_allowed":False,"claims":[{
            "source_url":URL,"source_sha256":sh(SOURCE),"source_quote":SOURCE,
            "path":PATH,"page_sha256":sh(HTML),"old_claim":"300 euros","new_claim":"500 euros",
            "kind":"amount","legal_conflict_detected":False,
            "scope":{"jurisdiction":"Extremadura","benefit":"Ayuda por nacimiento","beneficiaries":"Familias con requisitos",
                     "effective_from":"2026-01-01","effective_until":"2026-12-31",
                     "exceptions":"Sujetos a renta","application_status":"closed"},
            "reviewer":{"name":"reviewer","reviewed_at":date.today().isoformat(),
                        "independent_factual_check":True,"scope_and_exceptions_checked":True,
                        "evidence_ref":"gazette-2026-verified"}
        }]}
    def tearDown(self):self.tmp.cleanup()
    def run_batch(self,apply=False,branch=None):
        return batch.execute(self.root,self.watchlist,self.report,self.snapshots,self.claims,
                             date.today().isoformat(),apply=apply,branch=branch)
    def test_end_to_end_dry_run_keeps_site_unchanged(self):
        result=self.run_batch()
        self.assertEqual(result["documentary_evidence_count"],1)
        self.assertEqual(result["pages_updated"],0)
        self.assertFalse(result["production_deployment_allowed"])
        self.assertEqual(self.page.read_text(),HTML)
    def test_real_reviewed_change_written_only_to_batch(self):
        result=self.run_batch(True,"batch/review-nov")
        self.assertEqual(result["pages_updated"],1)
        self.assertIn("500 euros",self.page.read_text())
        self.assertNotIn("300 euros",self.page.read_text())
        self.assertIn('"dateModified":"'+date.today().isoformat()+'"',self.page.read_text())
    def test_branch_main_refuses_write(self):
        with self.assertRaises(ValueError):
            self.run_batch(True,"main")
        self.assertEqual(self.page.read_text(),HTML)
    def test_unreviewed_source_refuses_write(self):
        self.claims["claims"][0]["reviewer"]["independent_factual_check"]=False
        with self.assertRaises(ValueError):
            self.run_batch(True,"batch/x")
    def test_unmatched_source_quote_refuses_write(self):
        self.claims["claims"][0]["source_quote"]="Texto distinto de la ley inexistente."
        with self.assertRaises(ValueError):
            self.run_batch(True,"batch/x")
    def test_stale_website_refuses_write(self):
        self.page.write_text(HTML+" NUEVO",encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_batch(True,"batch/x")
    def test_source_changed_since_approval_refuses_write(self):
        self.snapshots["snapshots"][0]["text"]+=" editado"
        with self.assertRaises(ValueError):
            self.run_batch(True,"batch/x")
if __name__=="__main__":unittest.main()
