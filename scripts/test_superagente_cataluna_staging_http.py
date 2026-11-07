#!/usr/bin/env python3
"""CI-safe regression checks of candidate deployment and rollback over localhost."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).parent))
spec=importlib.util.spec_from_file_location("staging",Path(__file__).with_name("superagente_cataluna_staging_http.py"))
staging=importlib.util.module_from_spec(spec)
spec.loader.exec_module(staging)

REL="ayuda-nacimiento-cataluna/index.html"
URL="https://tramits.gencat.cat/es/tramits/tramits-temes/Prestacio-per-a-families-amb-infants?moda=1"
class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.original=b"<p>Plazo antiguo.</p><p>Residencia vaga.</p>"
        self.page=self.root/REL
        self.page.parent.mkdir(parents=True)
        self.page.write_bytes(self.original)
        e=self.root/"superagente/research/evidence.json"
        e.parent.mkdir(parents=True)
        e.write_text(json.dumps({
            "page_source_path":REL,"source_url":URL,"editorial_approval":False,
            "checks":[{"topic":"deadline","source_excerpt":"documented","recommended_action":"clarify"},
                      {"topic":"eligibility","source_excerpt":"documented","recommended_action":"clarify"}]
        }),encoding="utf-8")
        self.manifest={"package_id":"test","path":REL,"source_url":URL,
            "evidence_report":"superagente/research/evidence.json",
            "status":"proposal_not_approved","publication_allowed":False,"merge_allowed":False,
            "changes":[
                {"id":"deadline_pre_2026_07_14","evidence_topic":"deadline",
                 "search":"Plazo antiguo.","replacement":"Plazo nuevo."},
                {"id":"residence_requirement_clarification","evidence_topic":"eligibility",
                 "search":"Residencia vaga.","replacement":"Residencia clara."}
            ]}
    def tearDown(self):
        self.temp.cleanup()
    def test_http_baseline_candidate_rollback(self):
        result=staging.stage_and_rollback(self.root,self.manifest)
        self.assertEqual([x["phase"] for x in result["http_probes"]],
                         ["baseline","candidate","rollback"])
        self.assertEqual([x["http_status"] for x in result["http_probes"]],[200,200,200])
        self.assertNotEqual(result["http_probes"][0]["content_sha256"],
                            result["http_probes"][1]["content_sha256"])
        self.assertEqual(result["http_probes"][0]["content_sha256"],
                         result["http_probes"][2]["content_sha256"])
        self.assertEqual(self.page.read_bytes(),self.original)
    def test_no_remote_or_prod_claim(self):
        result=staging.stage_and_rollback(self.root,self.manifest)
        self.assertFalse(result["remote_staging_deployment_tested"])
        self.assertFalse(result["production_rollback_tested"])
        self.assertFalse(result["publication_allowed"])
        self.assertFalse(result["editorial_approval"])
    def test_stale_anchor_refused(self):
        self.manifest["changes"][0]["search"]="Ausente"
        with self.assertRaises(ValueError):
            staging.stage_and_rollback(self.root,self.manifest)
        self.assertEqual(self.page.read_bytes(),self.original)
    def test_manifest_must_remain_unapproved(self):
        self.manifest["publication_allowed"]=True
        with self.assertRaises(ValueError):
            staging.stage_and_rollback(self.root,self.manifest)
    def test_evidence_source_must_match(self):
        self.manifest["source_url"]="https://tramits.gencat.cat/other/"
        with self.assertRaises(ValueError):
            staging.stage_and_rollback(self.root,self.manifest)
    def test_path_traversal_refused(self):
        self.manifest["path"]="../index.html"
        with self.assertRaises(ValueError):
            staging.stage_and_rollback(self.root,self.manifest)
if __name__=="__main__":
    unittest.main()
