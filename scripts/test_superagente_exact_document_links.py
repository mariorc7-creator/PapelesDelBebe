#!/usr/bin/env python3
"""Offline tests: exact-document claim validation rejects host-only trust."""
import hashlib
import importlib.util
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location("links",Path(__file__).with_name("superagente_exact_document_links.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
URL="https://sede.agenciatributaria.gob.es/Sede/procedimientos/GZ25.shtml"
HOST="sede.agenciatributaria.gob.es"
TEXT="La deducción por maternidad requiere comprobar los requisitos de acceso."
WATCH={"sources":[{"url":URL,"approved_host":HOST}]}
def cap(text=TEXT,sha=None,url=URL):
    return {"captures":[{"source_url":url,"text":text,
                          "sha256":sha or hashlib.sha256(text.encode()).hexdigest()}]}
def claims(url=URL,excerpt="deducción por maternidad"):
    return {"claims":[{"source_url":url,"source_excerpt":excerpt}]}
class ExactLinkTests(unittest.TestCase):
    def test_same_exact_document_and_excerpt(self):
        result=p.check(claims(),cap(),WATCH)
        self.assertEqual(result["blocked"],0)
        self.assertFalse(result["results"][0]["publishable"])
        self.assertFalse(result["results"][0]["source_provenance_verified"])
    def test_other_path_same_host_blocked(self):
        r=p.check(claims(url="https://"+HOST+"/Sede/otra"),cap(),WATCH)
        self.assertIn("unapproved:exact_document",r["results"][0]["errors"])
    def test_no_capture_blocked(self):
        self.assertEqual(p.check(claims(),{"captures":[]},WATCH)["blocked"],1)
    def test_tampered_capture_blocked(self):
        self.assertIn("mismatch:capture_digest",p.check(claims(),cap(sha="0"*64),WATCH)["results"][0]["errors"])
    def test_excerpt_missing_blocked(self):
        self.assertIn("missing:document_excerpt",p.check(claims(excerpt="palabras que no existen"),cap(),WATCH)["results"][0]["errors"])
    def test_homepage_not_approved(self):
        w={"sources":[{"url":"https://"+HOST+"/","approved_host":HOST}]}
        self.assertEqual(p.check(claims(),cap(),w)["blocked"],1)
    def test_candidate_not_approval(self):
        self.assertEqual(p.check(claims(),cap(),{"sources":[{"url":"https://www.boe.es/","approved_host":"www.boe.es"}]})["blocked"],1)
    def test_duplicate_capture_blocked(self):
        with self.assertRaises(ValueError):
            p.check(claims(),{"captures":cap()["captures"]*2},WATCH)
    def test_duplicate_approved_url_blocked(self):
        with self.assertRaises(ValueError):
            p.check(claims(),cap(),{"sources":WATCH["sources"]*2})
    def test_unapproved_host_blocked(self):
        self.assertEqual(p.check(claims(url="https://fake.example/doc"),cap(),WATCH)["blocked"],1)
    def test_redirect_like_url_not_approved(self):
        self.assertFalse(p.url_is_exact_https("https://"+HOST+"/#frag",HOST))
    def test_empty_comparisons_fail(self):
        with self.assertRaises(ValueError): p.check({"claims":[]},cap(),WATCH)
if __name__=="__main__":
    unittest.main()
