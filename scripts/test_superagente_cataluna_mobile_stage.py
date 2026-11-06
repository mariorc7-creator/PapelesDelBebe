#!/usr/bin/env python3
"""Offline tests for two-step disposable Catalonia responsive preview."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
spec=importlib.util.spec_from_file_location("stage",Path(__file__).with_name("superagente_cataluna_mobile_stage.py"))
stage=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)
REL="ayuda-nacimiento-cataluna/index.html"
URL="https://tramits.gencat.cat/es/tramits/tramits-temes/Prestacio-per-a-families-amb-infants?moda=1"
class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        t=Path(self.temp.name)
        self.root=t/"repo";self.sandbox=t/"sandbox"
        for base in (self.root,self.sandbox):
            f=base/REL;f.parent.mkdir(parents=True)
        self.original=b"<p>Plazo antiguo.</p><p>Residencia vaga.</p>"
        (self.root/REL).write_bytes(self.original)
        (self.sandbox/REL).write_bytes(b"<p>Plazo nuevo.</p><p>Residencia vaga.</p>")
        evidence=self.root/"superagente/research/evidence.json"
        evidence.parent.mkdir(parents=True)
        evidence.write_text(json.dumps({"page_source_path":REL,"source_url":URL,
            "editorial_approval":False,"checks":[{"topic":"deadline","source_excerpt":"x","recommended_action":"x"},
                {"topic":"eligibility","source_excerpt":"x","recommended_action":"x"}]}))
        self.pkg={"package_id":"test","path":REL,"source_url":URL,
                  "evidence_report":"superagente/research/evidence.json","status":"proposal_not_approved",
                  "publication_allowed":False,"merge_allowed":False,
                  "changes":[{"id":"deadline_pre_2026_07_14","search":"Plazo antiguo.","replacement":"Plazo nuevo.","evidence_topic":"deadline"},
                   {"id":"residence_requirement_clarification","search":"Residencia vaga.","replacement":"Residencia clara.","evidence_topic":"eligibility"}]}
    def tearDown(self):self.temp.cleanup()
    def test_both_edits_in_preview_checkout_untouched(self):
        report=stage.add_residence(self.root,self.sandbox,self.pkg)
        self.assertTrue(report["preview_has_both_edits"])
        self.assertIn(b"Residencia clara.",(self.sandbox/REL).read_bytes())
        self.assertEqual((self.root/REL).read_bytes(),self.original)
    def test_wrong_existing_preview_blocks(self):
        (self.sandbox/REL).write_text("Otra version",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"does not match"):
            stage.add_residence(self.root,self.sandbox,self.pkg)
    def test_sandbox_inside_checkout_blocks(self):
        with self.assertRaises(ValueError):
            stage.add_residence(self.root,self.root/"temp",self.pkg)
    def test_missing_sandbox_file_blocks(self):
        (self.sandbox/REL).unlink()
        with self.assertRaises(ValueError):
            stage.add_residence(self.root,self.sandbox,self.pkg)
    def test_wrong_manifest_blocks(self):
        self.pkg["publication_allowed"]=True
        with self.assertRaises(ValueError):
            stage.add_residence(self.root,self.sandbox,self.pkg)
if __name__=="__main__":unittest.main()
