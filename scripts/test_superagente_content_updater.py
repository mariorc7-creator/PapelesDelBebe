import importlib.util
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

P=Path(__file__).with_name("superagente_content_updater.py")
spec=importlib.util.spec_from_file_location("superagente_content_updater",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
HTML='''<!doctype html><html><head><title>Ayuda</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.papelesdelbebe.es/comunidades/asturias/">
<script type="application/ld+json">{"dateModified":"2026-10-01"}</script>
</head><body><header><nav><a href="/">Inicio</a></nav></header><main><h1>Ayuda</h1>
<section id="info"><p>Plazo original.</p></section><p>Información revisada: 1 de octubre de 2026</p>
<p>Última revisión: <time datetime="2026-10-01">1 de octubre de 2026</time></p></main><footer>Pie</footer></body></html>'''
PATH="comunidades/asturias/index.html"
TODAY=date.today().isoformat()

def candidate(action="change"):
    return {"schema_version":1,"status":"editorially_verified_for_branch_only",
        "publication_allowed":False,"changes":[{
            "path":PATH,"original_sha256":sha256(HTML.encode()).hexdigest(),
            "action":action,"review_date":TODAY,
            "official_source_url":"https://www.asturias.es/ayudas",
            "independent_source_verification":True,"editorial_approval":True,
            "reviewer":"editorial","evidence_ref":"verified-official-document-1",
            **({"search":"Plazo original.","replacement":"Plazo actualizado."}
               if action=="change" else {"unchanged_confirmed":True})
        }]}
class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.root=Path(self.tmp.name)
        self.page=self.root/PATH;self.page.parent.mkdir(parents=True)
        self.page.write_text(HTML,encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_dry_run_does_not_change_files(self):
        r=m.run(self.root,candidate())
        self.assertEqual(r["mode"],"dry_run")
        self.assertEqual(self.page.read_text(),HTML)
        self.assertFalse(r["publishing_authorized"])
    def test_valid_change_updates_content_and_dates(self):
        r=m.run(self.root,candidate(),True)
        html=self.page.read_text()
        self.assertIn("Plazo actualizado.",html)
        self.assertIn('"dateModified":"'+TODAY+'"',html)
        self.assertIn('datetime="'+TODAY+'"',html)
        self.assertFalse(r["production_changed"])
    def test_review_only_never_changes_modification_date(self):
        m.run(self.root,candidate("review_only"),True)
        self.assertIn('"dateModified":"2026-10-01"',self.page.read_text())
        self.assertIn('datetime="'+TODAY+'"',self.page.read_text())
        self.assertIn("Plazo original.",self.page.read_text())
    def test_missing_source_verification_blocks(self):
        data=candidate();data["changes"][0]["independent_source_verification"]=False
        with self.assertRaises(ValueError):m.run(self.root,data,True)
        self.assertEqual(self.page.read_text(),HTML)
    def test_duplicate_or_stale_search_blocks(self):
        data=candidate();data["changes"][0]["search"]="not present"
        with self.assertRaises(ValueError):m.run(self.root,data,True)
    def test_stale_snapshot_blocks(self):
        data=candidate();self.page.write_text(HTML+" ")
        with self.assertRaises(ValueError):m.run(self.root,data,True)
    def test_cannot_change_canonical(self):
        data=candidate();data["changes"][0]["search"]="/comunidades/asturias/";data["changes"][0]["replacement"]="/comunidades/madrid/"
        with self.assertRaises(ValueError):m.run(self.root,data,True)
    def test_cannot_add_second_h1(self):
        data=candidate();data["changes"][0]["replacement"]="<h1>Nuevo</h1>"
        with self.assertRaises(ValueError):m.run(self.root,data,True)
    def test_review_only_requires_unchanged_confirmation(self):
        data=candidate("review_only");data["changes"][0]["unchanged_confirmed"]=False
        with self.assertRaises(ValueError):m.run(self.root,data)
    def test_no_publishable_manifest(self):
        data=candidate();data["publication_allowed"]=True
        with self.assertRaises(ValueError):m.run(self.root,data)
    def test_all_or_nothing_preflight(self):
        data=candidate();data["changes"].append({**data["changes"][0],"path":"comunidades/missing/index.html"})
        with self.assertRaises(ValueError):m.run(self.root,data,True)
        self.assertEqual(self.page.read_text(),HTML)
    def test_unsafe_link_change_disallowed_by_structure(self):
        data=candidate();data["changes"][0]["replacement"]="<a href='https://malicious.example'>X</a>"
        with self.assertRaises(ValueError):m.run(self.root,data)
if __name__=="__main__":
    unittest.main()
