import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
P=Path(__file__).with_name("superagente_cross_page_impact.py")
spec=importlib.util.spec_from_file_location("impact",P)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
URL="https://www.juntaex.es/w/0702824"
POLICY={"schema_version":1,"publication_allowed":False,"benefits":[{
  "id":"extremadura-natalidad-2026","official_source_url":URL,
  "territory_tokens":["Extremadura"],"benefit_tokens":["natalidad","nacimiento"],
  "old_claim_tokens":["fuera de plazo","convocatoria 2026 cerrada"]}]}
class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.root=Path(self.tmp.name)
        self.p="comunidades/extremadura/index.html"
        self.q="ayuda-natalidad-extremadura/index.html"
    def tearDown(self):self.tmp.cleanup()
    def put(self,path,html):
        f=self.root/path;f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text(html,encoding="utf-8")
    def html(self,main,header="Inicio"):
        return f'<html><head><title>Papeles</title></head><body><header>{header}</header><main>{main}</main></body></html>'
    def check(self,paths=()):
        return mod.impacted(self.root,POLICY,paths)
    def test_stale_claim_on_other_page_blocks_auto_publication(self):
        self.put(self.p,self.html(f'<p>Extremadura natalidad: convocatoria abierta. <a href="{URL}">Fuente</a></p>'))
        self.put(self.q,self.html('<p>Extremadura natalidad: convocatoria 2026 cerrada.</p>'))
        r=self.check([self.p])
        self.assertFalse(r["ready_for_auto_publication"])
        self.assertEqual(r["findings"][0]["uncovered_old_claims"],[self.q])
    def test_stale_claim_in_changed_page_still_blocks(self):
        self.put(self.p,self.html('<p>Extremadura natalidad: convocatoria abierta.</p><p>Extremadura natalidad: convocatoria 2026 cerrada.</p>'))
        r=self.check([self.p])
        self.assertFalse(r["ready_for_auto_publication"])
        self.assertEqual(r["findings"][0]["uncovered_old_claims"],[self.p])
    def test_complete_update_across_pages_allows_factual_batch(self):
        self.put(self.p,self.html(f'<p>Extremadura natalidad: convocatoria abierta. <a href="{URL}">Fuente</a></p>'))
        self.put(self.q,self.html(f'<p>Extremadura natalidad: convocatoria abierta. <a href="{URL}">Fuente</a></p>'))
        r=self.check([self.p,self.q])
        self.assertTrue(r["ready_for_auto_publication"])
        self.assertEqual(r["findings"][0]["uncovered_old_claims"],[])
        self.assertFalse(r["seo_modified"])
        self.assertFalse(r["automatic_legal_truth_established"])
    def test_unrelated_general_birth_page_not_included(self):
        self.put(self.p,self.html(f'<p>Extremadura natalidad: convocatoria abierta. <a href="{URL}">Fuente</a></p>'))
        self.put("comunidades/cataluna/index.html",self.html('<p>Cataluña: ayuda por nacimiento fuera de plazo.</p>'))
        r=self.check([self.p])
        self.assertTrue(r["ready_for_auto_publication"])
        self.assertEqual(len(r["findings"][0]["references"]),1)
    def test_generic_outdated_word_with_no_region_is_not_match(self):
        self.put(self.p,self.html(f'<p>Extremadura natalidad: convocatoria abierta. <a href="{URL}">Fuente</a></p>'))
        self.put("ayudas-nacimiento/index.html",self.html('<p>Convocatoria 2026 cerrada de otra ayuda.</p>'))
        self.assertTrue(self.check([self.p])["ready_for_auto_publication"])
    def test_script_only_reference_not_fact(self):
        self.put(self.p,self.html(f'<p>Extremadura natalidad: convocatoria abierta. <a href="{URL}">Fuente</a></p>'))
        self.put(self.q,self.html('<script>Extremadura natalidad: convocatoria 2026 cerrada.</script>'))
        self.assertTrue(self.check([self.p])["ready_for_auto_publication"])
    def test_stale_meta_description_blocks_even_if_visible_page_correct(self):
        self.put(self.p,'<html><head><title>Extremadura</title>'
                 '<meta name="description" content="Extremadura natalidad: convocatoria 2026 cerrada.">'
                 '</head><body><main><p>Extremadura natalidad: convocatoria abierta.'
                 f'<a href="{URL}">Fuente</a></p></main></body></html>')
        r=self.check([self.p])
        self.assertFalse(r["ready_for_auto_publication"])
        self.assertTrue(r["findings"][0]["references"][0]["seo_metadata_contains_old_claim"])
    def test_stale_structured_faq_blocks(self):
        self.put(self.p,'<html><head><script type="application/ld+json">'
                 '{"@type":"FAQPage","answer":"Extremadura natalidad: convocatoria 2026 cerrada."}'
                 '</script></head><body><main><p>Extremadura natalidad: convocatoria abierta.'
                 f'<a href="{URL}">Fuente</a></p></main></body></html>')
        r=self.check([self.p])
        self.assertFalse(r["ready_for_auto_publication"])
        self.assertEqual(r["findings"][0]["uncovered_old_claims"],[self.p])
    def test_no_changed_files_cannot_auto_publish(self):
        self.put(self.p,self.html('<p>Extremadura natalidad: convocatoria abierta.</p>'))
        self.assertFalse(self.check()["ready_for_auto_publication"])
    def test_no_matched_pages_cannot_auto_publish(self):
        self.put(self.p,self.html('<p>Receta de zanahorias.</p>'))
        self.assertFalse(self.check([self.p])["ready_for_auto_publication"])
    def test_policy_requires_allowlisted_https(self):
        bad={"schema_version":1,"publication_allowed":False,"benefits":[{
            **POLICY["benefits"][0],"official_source_url":"http://evil.example"}]}
        with self.assertRaises(ValueError):mod.impacted(self.root,bad,[self.p])
    def test_policy_prevents_auto_grant(self):
        bad={**POLICY,"publication_allowed":True}
        with self.assertRaises(ValueError):mod.impacted(self.root,bad,[self.p])
    def test_duplicate_or_missing_tokens_rejected(self):
        bad={"schema_version":1,"publication_allowed":False,"benefits":[{
            **POLICY["benefits"][0],"old_claim_tokens":[]}]}
        with self.assertRaises(ValueError):mod.impacted(self.root,bad,[self.p])
    def test_factual_reference_not_in_head_or_footer(self):
        self.put(self.p,self.html(f'<p>Extremadura natalidad: convocatoria abierta. <a href="{URL}">Fuente</a></p>',header="Extremadura natalidad convocatoria 2026 cerrada"))
        self.assertTrue(self.check([self.p])["ready_for_auto_publication"])
if __name__=="__main__":unittest.main()
