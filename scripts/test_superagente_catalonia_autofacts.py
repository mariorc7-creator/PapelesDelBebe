import importlib.util
from datetime import date
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
P=Path(__file__).with_name("superagente_catalonia_autofacts.py")
s=importlib.util.spec_from_file_location("catalonia_auto",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
SRC=m.SOURCE
OLD_SOURCE=("Prestación para familias con hijos. "
            "El importe de la prestación es de 650 euros por niño. "
            "Para las familias que tienen reconocido el título de familia numerosa o monoparental, "
            "en relación con el hijo que da lugar a solicitar la prestación, el importe es de 750 euros. "
            "Familias que han tenido un hijo y no superan un nivel de ingresos.")
NEW_SOURCE=OLD_SOURCE.replace("650 euros","800 euros").replace("750 euros","950 euros")
PAGES=list(m.PAGES)
POLICY={"schema_version":1,"publication_allowed":False,"scheme":"cataluna-family-benefit",
        "year":2026,"source_url":SRC,"pages":PAGES,"last_published_amounts":[650,750]}
def evidence(text,status="changed_needs_review"):
    hash=sha256(text.encode()).hexdigest()
    return {"results":[{"url":SRC,"status":status,"sha256":hash}]},{"snapshots":[{"url":SRC,"sha256":hash,"text":text}]}
def html():
    return '''<!doctype html><html><head><title>Ayuda en Cataluña 650 € o 750 €</title>
<meta name="description" content="Importe 650 € general, 750 € especial.">
<meta name="robots" content="index,follow">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="https://www.papelesdelbebe.es/ayuda-nacimiento-cataluna/">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{"dateModified":"2026-10-01","@type":"FAQPage","text":"650 euros o 750 euros"}</script>
</head><body><header><nav><a href="/">Inicio</a></nav></header>
<main><h1>Ayuda de nacimiento Cataluña 650 € o 750 €</h1>
<p>Prestación por nacimiento: 650 € para familias y 750 € para familias numerosas o monoparentales.</p>
<p>El plazo es independiente de las cuantías.</p></main><footer>Pie</footer></body></html>'''

class CataloniaAutoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.root=Path(self.tmp.name)
        for rel in PAGES:
            target=self.root/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(html(),encoding="utf-8")
        self.policy=POLICY.copy()
        self.policy["pages"]=PAGES[:]
    def tearDown(self):self.tmp.cleanup()
    def plan(self,text=NEW_SOURCE,status="changed_needs_review",day=date(2026,11,8)):
        rep,snap=evidence(text,status)
        return m.build(self.policy,rep,snap,self.root,day)
    def test_real_source_amounts_parsed(self):
        self.assertEqual(m.extract(OLD_SOURCE),[650,750])
        self.assertEqual(m.extract(NEW_SOURCE),[800,950])
    def test_new_amounts_update_all_three_localized_pages(self):
        decision=self.plan()
        self.assertTrue(decision["changed"])
        self.assertEqual(len(decision["changes"]),3)
        for row in decision["changes"]:
            updated=row["after"]
            self.assertIn("800 €",updated)
            self.assertIn("950 euros",updated)
            self.assertIn('"dateModified":"2026-11-08"',updated)
            self.assertIn('href="/style.css"',updated)
            self.assertNotIn("650 €",updated)
        self.assertFalse(decision["seo_optimizations"])
        self.assertTrue(decision["factual_metadata_consistency"])
    def test_unchanged_source_skips_redeployment(self):
        self.assertFalse(self.plan(OLD_SOURCE,"unchanged")["changed"])
    def test_apply_is_transactionally_verified(self):
        decision=self.plan()
        path=self.root/"superagente/catalonia-amount-contract.json"
        path.parent.mkdir(parents=True)
        path.write_text("{}")
        count=m.apply(self.root,decision,path,True)
        self.assertEqual(count,3)
        self.assertIn("800 €",(self.root/PAGES[1]).read_text())
        self.assertEqual(__import__("json").loads(path.read_text())["last_published_amounts"],[800,950])
    def test_dry_run_never_changes_pages(self):
        decision=self.plan()
        self.assertEqual(m.apply(self.root,decision,self.root/"foo.json",False),0)
        self.assertEqual((self.root/PAGES[1]).read_text(),html())
    def test_stale_target_aborts_before_first_write(self):
        decision=self.plan()
        (self.root/PAGES[2]).write_text("changed concurrently")
        path=self.root/"superagente/policy.json"
        with self.assertRaises(ValueError):m.apply(self.root,decision,path,True)
        self.assertEqual((self.root/PAGES[0]).read_text(),html())
    def test_incomplete_source_blocks(self):
        with self.assertRaises(ValueError):self.plan("Prestación para familias con hijos. La ayuda ahora es de 800 euros.")
    def test_missing_beneficiary_clause_blocks(self):
        x=OLD_SOURCE.replace("familia numerosa o monoparental","familias sin ningún requisito")
        with self.assertRaises(ValueError):self.plan(x)
    def test_multiple_conflicting_numbers_blocks(self):
        with self.assertRaises(ValueError):self.plan(OLD_SOURCE+" "+OLD_SOURCE.replace("650","800"))
    def test_forged_source_hash_blocks(self):
        rep,snap=evidence(NEW_SOURCE)
        snap["snapshots"][0]["text"]="altered"
        with self.assertRaises(ValueError):m.build(self.policy,rep,snap,self.root,date(2026,11,8))
    def test_source_fetch_failure_blocks(self):
        rep,snap=evidence(NEW_SOURCE,"fetch_failed")
        with self.assertRaises(ValueError):m.build(self.policy,rep,snap,self.root,date(2026,11,8))
    def test_outside_2026_policy_blocks(self):
        with self.assertRaises(ValueError):self.plan(day=date(2027,1,1))
    def test_unregistered_page_with_same_benefit_blocks(self):
        f=self.root/"extra/old/index.html"
        f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text("<main><p>La ayuda por nacimiento en Cataluña es de 650 € o 750 €.</p></main>")
        with self.assertRaises(ValueError):self.plan()
    def test_missing_page_blocks(self):
        (self.root/PAGES[0]).unlink()
        with self.assertRaises(ValueError):self.plan()
    def test_policy_cannot_inject_other_path(self):
        self.policy["pages"].append("../secrets/index.html")
        with self.assertRaises(ValueError):self.plan()
    def test_unreasonable_amounts_block(self):
        with self.assertRaises(ValueError):self.plan(OLD_SOURCE.replace("650 euros","50000 euros"))
if __name__=="__main__":unittest.main()
