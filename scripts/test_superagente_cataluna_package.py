#!/usr/bin/env python3
"""Offline non-mutating multi-edit Catalonia package tests."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("pkg",Path(__file__).with_name("superagente_cataluna_package.py"))
pkg=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pkg)
REL="ayuda-nacimiento-cataluna/index.html"
SOURCE="https://tramits.gencat.cat/es/tramits/tramits-temes/Prestacio-per-a-families-amb-infants?moda=1"
def manifest():
    return {"package_id":"test","path":REL,"source_url":SOURCE,
            "evidence_report":"superagente/research/evidence.json",
            "status":"proposal_not_approved","publication_allowed":False,"merge_allowed":False,
            "changes":[{"id":"plazo","search":"Plazo antiguo.","replacement":"Plazo nuevo.","evidence_topic":"deadline"},
                       {"id":"residencia","search":"Residencia vaga.","replacement":"Residencia detallada.","evidence_topic":"eligibility"}]}
class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.file=self.root/REL
        self.file.parent.mkdir(parents=True)
        self.file.write_text("<p>Plazo antiguo.</p>\n<p>Residencia vaga.</p>",encoding="utf-8")
        evidence=self.root/"superagente/research/evidence.json"
        evidence.parent.mkdir(parents=True)
        evidence.write_text(json.dumps({"page_source_path":REL,"source_url":SOURCE,
            "editorial_approval":False,"checks":[{"topic":"deadline","source_excerpt":"Texto oficial","recommended_action":"Corregir"},
                {"topic":"eligibility","source_excerpt":"Texto oficial","recommended_action":"Aclarar"}]}),encoding="utf-8")
        self.item=manifest()
    def tearDown(self):self.temp.cleanup()
    def test_atomic_combined_diff_and_no_source_changes(self):
        before=self.file.read_bytes()
        result=pkg.build(self.root,self.item)
        self.assertEqual(result["edit_ids"],["plazo","residencia"])
        self.assertIn("Plazo nuevo.",result["unified_diff"])
        self.assertIn("Residencia detallada.",result["unified_diff"])
        self.assertTrue(result["byte_exact_local_rollback"])
        self.assertEqual(self.file.read_bytes(),before)
        self.assertFalse(result["production_rollback_tested"])
    def test_stale_anchor_blocks(self):
        self.item["changes"][0]["search"]="Inexistente"
        with self.assertRaisesRegex(ValueError,"anchor"):pkg.build(self.root,self.item)
    def test_ambiguous_anchor_blocks(self):
        self.file.write_text("Plazo antiguo. Plazo antiguo. Residencia vaga.")
        with self.assertRaisesRegex(ValueError,"anchor"):pkg.build(self.root,self.item)
    def test_duplicate_anchor_blocks(self):
        self.item["changes"][1]["search"]="Plazo antiguo."
        with self.assertRaisesRegex(ValueError,"anchor"):pkg.build(self.root,self.item)
    def test_path_traversal_blocks(self):
        self.item["path"]="../outside.html"
        with self.assertRaises(ValueError):pkg.build(self.root,self.item)
    def test_approved_manifest_blocks(self):
        self.item["publication_allowed"]=True
        with self.assertRaises(ValueError):pkg.build(self.root,self.item)
    def test_missing_evidence_topic_blocks(self):
        self.item["changes"][1]["evidence_topic"]="unsupported"
        with self.assertRaisesRegex(ValueError,"finding"):pkg.build(self.root,self.item)
    def test_mismatched_source_blocks(self):
        self.item["source_url"]=SOURCE+"other"
        with self.assertRaises(ValueError):pkg.build(self.root,self.item)
    def test_replacement_present_blocks(self):
        self.file.write_text("Plazo antiguo. Plazo nuevo. Residencia vaga.")
        with self.assertRaisesRegex(ValueError,"already present"):pkg.build(self.root,self.item)
    def test_noop_blocks(self):
        self.item["changes"][0]["replacement"]="Plazo antiguo."
        with self.assertRaisesRegex(ValueError,"invalid edit"):pkg.build(self.root,self.item)
if __name__=="__main__":unittest.main()
