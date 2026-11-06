#!/usr/bin/env python3
"""V0.3 editorial prioritization must never invent verified reviews."""
import importlib.util
import unittest
from datetime import date
from pathlib import Path

spec=importlib.util.spec_from_file_location("workplan",Path(__file__).with_name("superagente_v03_review_workplan.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
P="https://www.papelesdelbebe.es/deduccion-maternidad/"
Q="https://www.papelesdelbebe.es/empadronar-bebe/"
R="https://www.papelesdelbebe.es/herramientas/"
TODAY=date(2026,11,6)
ROUTES={"routes":[{"page":P,"priority":"P0"},{"page":Q,"priority":"P1"}]}
CANDIDATES={"references":[{"page":P,"status":"candidate_needs_document_review"}]}
EVIDENCE={"date":"2026-11-01","result":"unchanged","sources":["https://sede.agenciatributaria.gob.es/faq"],
          "evidence":"Official FAQ corroborated the stated conditions in context.","reviewer":"Editorial reviewer"}

def build(registry=None, urls=None, routes=ROUTES, candidates=CANDIDATES):
    return mod.plan([P,Q,R] if urls is None else urls,
                    {"pages":{}} if registry is None else registry,routes,candidates,TODAY)

class WorkplanTests(unittest.TestCase):
    def test_candidate_is_not_verified(self):
        p=build()
        item=next(x for x in p["items"] if x["url"]==P)
        self.assertEqual(item["official_reference_status"],"candidate_unverified")
        self.assertFalse(item["page_verified_by_this_plan"])
        self.assertIsNone(item["last_documented_review"])
    def test_priorities(self):
        self.assertEqual([x["url"] for x in build()["items"][:2]],[P,Q])
    def test_review_date_requires_history(self):
        p=build({"pages":{P:{"last_reviewed":"2026-11-06","status":"unchanged","history":[]}}})
        self.assertIsNone(p["items"][0]["last_documented_review"])
    def test_unchanged_review_preserved_without_html(self):
        p=build({"pages":{P:{"history":[EVIDENCE]}}})
        item=p["items"][0]
        self.assertEqual(item["last_documented_review"],"2026-11-01")
        self.assertEqual(item["days_since_review"],5)
        self.assertFalse(item["modify_content"])
        self.assertFalse(item["update_review_date"])
    def test_future_review_rejected(self):
        p=build({"pages":{P:{"history":[{**EVIDENCE,"date":"2099-01-01"}]}}})
        self.assertIsNone(p["items"][0]["last_documented_review"])
    def test_review_without_sources_rejected(self):
        p=build({"pages":{P:{"history":[{**EVIDENCE,"sources":[]}]}}})
        self.assertIsNone(p["items"][0]["last_documented_review"])
    def test_unverifiable_does_not_advance_last_review(self):
        p=build({"pages":{P:{"history":[{**EVIDENCE,"result":"unverifiable"}]}}})
        self.assertIsNone(p["items"][0]["last_documented_review"])
    def test_empty_sitemap_rejected(self):
        with self.assertRaises(ValueError):
            build(urls=[])
    def test_duplicate_urls_rejected(self):
        with self.assertRaises(ValueError):
            build(urls=[P,P])
    def test_unrecognized_site_rejected(self):
        with self.assertRaises(ValueError):
            build(urls=["https://example.com/private"])
    def test_unmapped_priority(self):
        p=build()
        item=next(x for x in p["items"] if x["url"]==R)
        self.assertEqual(item["action"],"inventory_and_evaluate")
    def test_route_without_reference_prompts_discovery(self):
        p=build()
        item=next(x for x in p["items"] if x["url"]==Q)
        self.assertEqual(item["action"],"locate_specific_official_document")

if __name__=="__main__":
    unittest.main()
