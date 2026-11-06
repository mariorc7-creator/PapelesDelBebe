#!/usr/bin/env python3
"""Offline tests for links to concrete administration pages."""
import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("docs",Path(__file__).with_name("superagente_document_candidates.py"))
docs=importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)
PAGE="https://www.papelesdelbebe.es/deduccion-maternidad/"
GOOD={"page":PAGE,"source_url":"https://sede.agenciatributaria.gob.es/Sede/procedimientos/GZ25.shtml",
      "approved_host":"sede.agenciatributaria.gob.es","authority":"AEAT",
      "document_type":"tramite","status":"candidate_needs_document_review"}
ROUTING={"routes":[{"page":PAGE,"authority":"AEAT"}]}
def check(refs, routing=ROUTING, pages=None):
    return docs.validate({"references":refs},routing,{PAGE} if pages is None else pages)
class Tests(unittest.TestCase):
    def test_candidate_is_not_legal_verification(self):
        r=check([GOOD])
        self.assertEqual(r["blocked"],0)
        self.assertFalse(r["results"][0]["publishable"])
    def test_unmapped_page(self):
        self.assertIn("unmapped:page",check([GOOD],pages=set())["results"][0]["errors"])
    def test_homepage_not_exact(self):
        self.assertIn("invalid:exact_official_url",check([{**GOOD,"source_url":"https://sede.agenciatributaria.gob.es/"}])["results"][0]["errors"])
    def test_foreign_host(self):
        self.assertIn("invalid:exact_official_url",check([{**GOOD,"source_url":"https://example.org/Sede/procedimientos/GZ25.shtml"}])["results"][0]["errors"])
    def test_authority_mismatch(self):
        self.assertIn("mismatch:authority",check([{**GOOD,"authority":"Otra"}])["results"][0]["errors"])
    def test_false_verified_flag(self):
        self.assertIn("blocked:verification_not_supported",check([{**GOOD,"verified":True}])["results"][0]["errors"])
    def test_false_status(self):
        self.assertIn("invalid:verification_claim",check([{**GOOD,"status":"verified"}])["results"][0]["errors"])
    def test_duplicate(self):
        r=check([GOOD,GOOD])
        self.assertIn("duplicate:page",r["results"][1]["errors"])
    def test_missing_field(self):
        self.assertIn("missing:approved_host",check([{**GOOD,"approved_host":""}])["results"][0]["errors"])
    def test_empty(self):
        with self.assertRaises(ValueError):
            check([])
if __name__=="__main__":
    unittest.main()
