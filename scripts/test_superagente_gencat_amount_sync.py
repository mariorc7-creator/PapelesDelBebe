import importlib.util
from datetime import date,timedelta
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

FILE=Path(__file__).with_name("superagente_gencat_amount_sync.py")
sp=importlib.util.spec_from_file_location("gencat_sync",FILE)
sync=importlib.util.module_from_spec(sp);sp.loader.exec_module(sync)
URL=sync.SOURCE_URL
TODAY=date.today()
SCOPE=" ".join(sync.REQUIRED_SCOPE)
def source(general=650,special=750):
    return (f"El importe de la prestación es de {general} euros por niño. "
            f"Para las familias que tienen reconocido el título de familia numerosa o monoparental, "
            f"en relación con el hijo que da lugar a solicitar la prestación, el importe es de {special} euros. "
            + SCOPE)
def inputs(text,status="changed_needs_review",captured=None):
    h=sha256(text.encode("utf-8")).hexdigest()
    return ({"results":[{"url":URL,"status":status,"sha256":h}]},
            {"snapshots":[{"url":URL,"sha256":h,"text":text,
                            "captured_on":(captured or TODAY).isoformat()}]})
def policy():
    return {"schema_version":1,"mode":"gencat-2026-two-amounts",
            "publication_allowed":False,"official_url":URL,
            "pages":list(sync.PAGES),"current_amounts":[650,750]}
def html():
    return (f'<!doctype html><html><head><title>Ayuda en Cataluña 650 € o 750 €</title>'
            f'<meta name="description" content="Cataluña: ayuda 650 € o 750 €">'
            f'<link rel="canonical" href="https://www.papelesdelbebe.es/ayuda-nacimiento-cataluna/">'
            f'<script type="application/ld+json">{{"dateModified":"2026-10-01",'
            f'"FAQ":"La prestación es de 650 euros y 750 euros."}}</script></head>'
            f'<body><header><nav><a href="/">Inicio</a></nav></header>'
            f'<main><h1>Ayudas Cataluña 650 € o 750 €</h1>'
            f'<p>Prestación de 650/750 € para familias que cumplan requisitos.</p>'
            f'<a href="{URL}">Fuente oficial Gencat</a></main>'
            f'<footer>Pie</footer></body></html>')

class GencatSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.root=Path(self.temp.name)
        for rel in sync.PAGES:
            file=self.root/rel;file.parent.mkdir(parents=True,exist_ok=True)
            content=html()
            if rel.startswith("ca/"):
                content=content.replace(URL,URL.replace("/es/tramits/","/ca/tramits/"))
            file.write_text(content,encoding="utf-8")
        (self.root/"superagente").mkdir(exist_ok=True)
        self.p=policy()
    def tearDown(self):self.temp.cleanup()
    def check(self,src=None,reported=None,snapshots=None):
        if reported is None or snapshots is None:
            reported,snapshots=inputs(src or source())
        return sync.propose(self.root,self.p,reported,snapshots,TODAY)
    def test_matching_source_causes_no_seo_edit_or_deploy(self):
        output=self.check()
        self.assertTrue(output["verified_unchanged"])
        self.assertEqual(sync.apply(self.root,output,True)["changed_pages"],0)
    def test_official_nonbreaking_spaces_and_linebreaks_are_accepted(self):
        raw=source(650,750)
        raw=raw.replace("El importe de la prestación es de 650 euros por niño. Para las", "El importe de la prestación es de 650 euros por niño.\nPara las")
        raw=raw.replace("durante 3 meses", "durante 3\u00a0meses")
        raw=raw.replace("Para el año 2026 el límite es:", "Para el año 2026\u00a0el límite es:")
        raw=raw.replace("título de familia numerosa o monoparental", "título de familia numerosa\t o monoparental")
        output=self.check(raw)
        self.assertTrue(output["verified_unchanged"])
        self.assertEqual(output["changes"],[])

    def test_changed_deadline_with_nonbreaking_space_still_blocks(self):
        raw=source(700,800).replace("durante 3 meses", "durante 2\u00a0meses")
        with self.assertRaises(ValueError):
            self.check(raw)

    def test_new_explicit_amounts_update_three_pages_atomically(self):
        d=self.check(source(700,800))
        self.assertEqual(len(d["changes"]),3)
        self.assertEqual(d["amounts_after"],[700,800])
        self.assertEqual(sync.apply(self.root,d,True)["changed_pages"],3)
        for rel in sync.PAGES:
            text=(self.root/rel).read_text(encoding="utf-8")
            self.assertIn("700 € o 800 €",text)
            self.assertIn("700/800 €",text)
            self.assertIn('"dateModified":"'+TODAY.isoformat()+'"',text)
            self.assertIn('rel="canonical" href="https://www.papelesdelbebe.es/ayuda-nacimiento-cataluna/"',text)
        saved=json.loads((self.root/"superagente/gencat-amount-policy.json").read_text())
        self.assertEqual(saved["current_amounts"],[700,800])
    def test_one_amount_change_and_one_unchanged_is_valid(self):
        d=self.check(source(700,750))
        self.assertEqual(len(d["changes"]),3)
        self.assertEqual(d["amounts_after"],[700,750])
        sync.apply(self.root,d,True)
        self.assertIn("700 € o 750 €",(self.root/sync.PAGES[0]).read_text())
    def test_stale_snapshot_digest_blocks(self):
        report,snapshot=inputs(source(700,800))
        snapshot["snapshots"][0]["text"]+=" altered"
        with self.assertRaises(ValueError):self.check(reported=report,snapshots=snapshot)
    def test_missing_scope_beneficiary_blocks(self):
        with self.assertRaises(ValueError):
            self.check(source(700,800).replace("título de familia numerosa o monoparental","algún requisito"))
    def test_changed_2026_income_threshold_blocks(self):
        with self.assertRaises(ValueError):
            self.check(source(700,800).replace("27.904,32","30.000,00"))
    def test_changed_deadline_blocks(self):
        with self.assertRaises(ValueError):
            self.check(source(700,800).replace("durante 3 meses","durante 2 meses"))
    def test_duplicate_money_paragraph_blocks(self):
        with self.assertRaises(ValueError):self.check(source(700,800)+source(700,800))
    def test_missing_site_page_blocks_whole_batch(self):
        (self.root/sync.PAGES[-1]).unlink()
        with self.assertRaises(ValueError):self.check(source(700,800))
    def test_tampered_official_source_url_blocks(self):
        self.p["official_url"]="https://evil.example"
        with self.assertRaises(ValueError):self.check(source(700,800))
    def test_rejects_stale_capture(self):
        report,snapshot=inputs(source(700,800),captured=TODAY-timedelta(days=4))
        with self.assertRaises(ValueError):self.check(reported=report,snapshots=snapshot)
    def test_rejects_unrelated_program(self):
        with self.assertRaises(ValueError):self.check("Otras deducciones de 700 euros y 800 euros. "+SCOPE)
    def test_rejects_impossible_relative_amount(self):
        with self.assertRaises(ValueError):self.check(source(850,700))
    def test_modified_meta_does_not_modify_links_or_markup(self):
        d=self.check(source(700,800))
        self.assertEqual(len(d["changes"]),3)
        old=html()
        new=d["changes"][0]["content"]
        self.assertIn('<meta name="description" content="Cataluña: ayuda 700 € o 800 €">',new)
        self.assertIn('<a href="'+URL+'">Fuente oficial Gencat</a>',new)
        sync.guard_factual_page(old,new,sync.PAGES[0])
    def test_stale_page_aborts_before_any_writes(self):
        d=self.check(source(700,800))
        (self.root/sync.PAGES[-1]).write_text(html()+"changed")
        with self.assertRaises(ValueError):sync.apply(self.root,d,True)
        self.assertIn("650 €",(self.root/sync.PAGES[0]).read_text())
    def test_dry_run_never_modifies_any_page(self):
        d=self.check(source(700,800))
        self.assertEqual(sync.apply(self.root,d,False)["changed_pages"],0)
        self.assertEqual((self.root/sync.PAGES[0]).read_text(),html())
if __name__=="__main__":unittest.main()
