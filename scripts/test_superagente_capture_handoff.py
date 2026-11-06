#!/usr/bin/env python3
"""Offline checks for manual captured-document dossier handoff."""
import hashlib
import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("handoff",Path(__file__).with_name("superagente_capture_handoff.py"))
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
URL="https://sede.agenciatributaria.gob.es/Sede/procedimientos/GZ25.shtml"
PAGE="https://www.papelesdelbebe.es/deduccion-maternidad/"
TEXT="Modelo 140: solicitud del abono anticipado de la deducción."
def d(candidate=URL):
    return {"dossiers":[{"page":PAGE,"page_sha256":"ab"*32,"candidate_source_url":candidate}]}
def w():
    return {"sources":[{"url":URL,"approved_host":"sede.agenciatributaria.gob.es","page":PAGE}]}
def capture(text=TEXT,sha=None):
    return {"captures":[{"source_url":URL,"text":text,"sha256":sha or hashlib.sha256(text.encode()).hexdigest(),
        "source_provenance_verified":False,"fetch_method":"https_pinned_public_ip_tls_hostname_no_redirect",
        "captured_at_utc":"2026-11-06T10:00:00+00:00"}],"failures":[]}
class HandoffTests(unittest.TestCase):
    def test_capture_integrity_and_no_approval(self):
        res=m.link(d(),w(),capture())
        self.assertEqual(res["integrity_checked"],1)
        self.assertFalse(res["publication_allowed"])
        self.assertFalse(res["results"][0]["editorial_approval"])
    def test_missing_capture_stays_pending(self):
        res=m.link(d(),w(),{"captures":[],"failures":[]})
        self.assertEqual(res["results"][0]["capture_status"],"capture_not_executed")
    def test_failed_capture(self):
        res=m.link(d(),w(),{"captures":[],"failures":[{"url":URL,"error":"timeout"}]})
        self.assertEqual(res["results"][0]["capture_status"],"capture_failed")
    def test_digest_tampering_rejected(self):
        with self.assertRaises(ValueError):m.link(d(),w(),capture(sha="0"*64))
    def test_wrong_capture_method_rejected(self):
        inp=capture();inp["captures"][0]["fetch_method"]="urllib_unpinned"
        with self.assertRaises(ValueError):m.link(d(),w(),inp)
    def test_fake_provenance_rejected(self):
        inp=capture();inp["captures"][0]["source_provenance_verified"]=True
        with self.assertRaises(ValueError):m.link(d(),w(),inp)
    def test_duplicate_capture_rejected(self):
        inp=capture();inp["captures"]*=2
        with self.assertRaises(ValueError):m.link(d(),w(),inp)
    def test_unapproved_capture_rejected(self):
        inp=capture();inp["captures"][0]["source_url"]="https://other.example/doc"
        with self.assertRaises(ValueError):m.link(d(),w(),inp)
    def test_changed_candidate_not_silently_approved(self):
        res=m.link(d("https://sede.agenciatributaria.gob.es/Sede/other.html"),w(),capture())
        self.assertEqual(res["results"][0]["capture_status"],"candidate_url_differs_from_capture")
    def test_unknown_failure_rejected(self):
        with self.assertRaises(ValueError):m.link(d(),w(),{"captures":[],"failures":[{"url":"https://bad.example/"}]})
    def test_no_source_selected(self):
        res=m.link(d(),{"sources":[]},{"captures":[],"failures":[]})
        self.assertEqual(res["results"][0]["capture_status"],"no_exact_source_selected")
    def test_duplicate_dossier_rejected(self):
        inp=d();inp["dossiers"]*=2
        with self.assertRaises(ValueError):m.link(inp,w(),capture())
if __name__=="__main__":
    unittest.main()
