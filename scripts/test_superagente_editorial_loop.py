import importlib.util
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date
import unittest

DIR=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("editorial_loop",DIR/"superagente_editorial_loop.py")
loop=importlib.util.module_from_spec(spec)
spec.loader.exec_module(loop)

SRC="https://www.asturias.es/ayudas-nacimiento"
PAGE="https://www.papelesdelbebe.es/comunidades/asturias/"
PATH="comunidades/asturias/index.html"
TEXT='''<!doctype html><html><head><title>Asturias</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.papelesdelbebe.es/comunidades/asturias/">
<script type="application/ld+json">{"dateModified":"2026-10-01"}</script>
</head><body><header><nav><a href="/">Inicio</a></nav></header>
<main><h1>Asturias</h1><section id="info"><p>Ayuda anterior.</p></section>
<p>Información revisada: 1 de octubre de 2026</p>
<p>Última revisión: <time datetime="2026-10-01">1 de octubre de 2026</time></p>
</main><footer>Final</footer></body></html>'''
SH="a"*64

def wl():
    return {"sources":[{"url":SRC,"page":PAGE,"topics":["ayuda_asturias"]}]}
def report(status="changed_needs_review",sha=SH):
    return {"results":[{"url":SRC,"status":status,"sha256":sha}]}
def approval(action="change"):
    item={
        "path":PATH, "original_sha256":sha256(TEXT.encode()).hexdigest(),
        "source_sha256":SH,"official_source_url":SRC,
        "action":action,"review_date":date.today().isoformat(),
        "independent_source_verification":True,
        "editorial_approval":True,
        "reviewer":"human_editor", "evidence_ref":"official-document-reviewed"
    }
    if action=="change":
        item.update(search="Ayuda anterior.",replacement="Ayuda actualizada.")
    else:
        item["unchanged_confirmed"]=True
    return {"schema_version":1,"status":"editorially_verified_for_branch_only",
            "publication_allowed":False,"changes":[item]}

class LoopTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.file=self.root/PATH
        self.file.parent.mkdir(parents=True)
        self.file.write_text(TEXT,encoding="utf-8")
    def tearDown(self):
        self.temp.cleanup()
    def test_changed_source_creates_review_template_without_edits(self):
        r=loop.orchestrate(wl(),report(),self.root)
        self.assertEqual(r["templates"][0]["suggested_action"],"change")
        self.assertFalse(r["templates"][0]["ready_to_apply"])
        self.assertEqual(self.file.read_text(),TEXT)
        self.assertEqual(r["website_updates"],0)
    def test_reviewed_claim_updates_only_on_batch_branch(self):
        r=loop.orchestrate(wl(),report(),self.root,approved=approval(),apply=True,branch="batch/autumn")
        self.assertEqual(r["website_updates"],1)
        self.assertIn("Ayuda actualizada.",self.file.read_text())
        self.assertFalse(r["batch_result"]["publishing_authorized"])
    def test_dry_run_no_edit_even_when_reviewed(self):
        r=loop.orchestrate(wl(),report(),self.root,approved=approval())
        self.assertEqual(r["website_updates"],0)
        self.assertEqual(self.file.read_text(),TEXT)
    def test_changed_without_editorial_approval_cannot_write(self):
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(),self.root,apply=True,branch="batch/a")
    def test_no_write_to_main(self):
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(),self.root,approved=approval(),apply=True,branch="main")
        self.assertEqual(self.file.read_text(),TEXT)
    def test_no_write_to_feature_branch(self):
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(),self.root,approved=approval(),apply=True,branch="feature/agent")
    def test_source_fingerprint_change_blocks_old_approval(self):
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(sha="b"*64),self.root,approved=approval())
    def test_page_sha_change_blocks_old_approval(self):
        self.file.write_text(TEXT+"changed",encoding="utf-8")
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(),self.root,approved=approval())
    def test_missing_legal_attestation_blocks(self):
        a=approval()
        a["changes"][0]["independent_source_verification"]=False
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(),self.root,approved=a,apply=True,branch="batch/x")
    def test_unchanged_source_prohibits_factual_edit(self):
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report("unchanged"),self.root,approved=approval())
    def test_unchanged_source_allows_human_review_date_only(self):
        r=loop.orchestrate(wl(),report("unchanged"),self.root,
            approved=approval("review_only"),apply=True,branch="batch/review")
        self.assertEqual(r["website_updates"],1)
        self.assertIn('"dateModified":"2026-10-01"',self.file.read_text())
    def test_changed_source_cannot_claim_review_only(self):
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(),self.root,approved=approval("review_only"))
    def test_unmapped_source_refused(self):
        a=approval()
        a["changes"][0]["official_source_url"]="https://other.example"
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(),self.root,approved=a)
    def test_missing_page_refused(self):
        self.file.unlink()
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(),self.root)
    def test_bad_source_hash_refused(self):
        with self.assertRaises(ValueError):
            loop.orchestrate(wl(),report(sha="not-a-hash"),self.root)
if __name__=="__main__":
    unittest.main()
