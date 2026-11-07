import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).with_name("superagente_integrated.py")
spec = importlib.util.spec_from_file_location("superagente_integrated", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def candidate(id_="ux-fix",risk="medium",price="0"):
    return {"id": id_, "title":"Revisar navegación", "category":"ux",
            "evidence_ref":"internal-review-123","seo_risk":risk,
            "urgency":"medium","impact_basis":"unknown",
            "expected_monthly_benefit_eur":None,"cost_eur":price,"effort_hours":"2"}

def monthly(verified=False):
    return {"schema_version":1,"mode":"offline_review_only","publication_allowed":False,
            "automatic_website_changes":False,"source_files_independently_verified":verified,
            "month":"2026-11","clicks":5,"clicks_by_category":{"cuna":5},
            "amazon_commissions_eur":None,"conversion_rate":None,"customer_attribution":None,
            "amazon_ordered_items":None,"amazon_shipped_items":None,
            "clicks_coverage_days":1,"amazon_coverage_days":None}

def staging(verified=False):
    return {"environment":"vercel_preview_not_production",
            "rollback":{"vercel_rollback_verified":verified}}

def audit():
    return {"schema_version":1,"mode":"read_only","publication_allowed":False,
            "issues":[{"page":"preparativos-bebe/index.html",
            "url":"https://amazon.es.evil.example/s?k=cuna",
            "issues":["unapproved_destination"]}]}

class IntegratedSuperAgentTests(unittest.TestCase):
    def test_empty_input_does_not_invent_tasks_or_income(self):
        result = mod.build_integrated_plan()
        self.assertEqual(result["summary"]["total_tasks"],0)
        self.assertTrue(result["gates"]["missing_affiliate_revenue_data"])
        self.assertFalse(result["gates"]["publish_to_production_allowed"])
        self.assertTrue(result["no_live_data_or_revenue_inferred"])

    def test_integration_from_3_module_inputs(self):
        result = mod.build_integrated_plan(proposals=[candidate()],
               amazon_audit=audit(), affiliate_monthly=monthly(), staging_report=staging(False))
        self.assertGreaterEqual(result["summary"]["total_tasks"],5)
        self.assertTrue(result["gates"]["staging_requires_reverification"])
        self.assertEqual(result["summary"]["source_modules"]["affiliate_monthly"],True)
        self.assertFalse(result["gates"]["automation_enabled"])

    def test_critical_affiliate_issue_is_risk_held(self):
        result = mod.build_integrated_plan(amazon_audit=audit())
        self.assertEqual(result["summary"]["held_for_risk_review"],1)
        self.assertFalse(result["priorities"][0]["auto_deploy_allowed"])

    def test_high_risk_explicit_proposal_never_publishes(self):
        result = mod.build_integrated_plan(proposals=[candidate(risk="critical")])
        self.assertEqual(result["summary"]["held_for_risk_review"],1)
        self.assertFalse(result["gates"]["publish_to_production_allowed"])

    def test_budget_cap_flags_expensive_batch(self):
        result = mod.build_integrated_plan(proposals=[candidate(price="150")],budget_eur="100")
        self.assertTrue(result["gates"]["candidate_cost_exceeds_budget"])
        self.assertIn("Estimate exceeds supplied budget", result["gates"]["known_blockers"])

    def test_no_budget_is_unknown_not_zero(self):
        result = mod.build_integrated_plan(proposals=[candidate(price="10")])
        self.assertIsNone(result["gates"]["budget_eur"])
        self.assertIsNone(result["gates"]["candidate_cost_exceeds_budget"])

    def test_duplicate_task_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            mod.build_integrated_plan(proposals=[candidate(),candidate()])

    def test_invalid_affiliate_attribution_rejected(self):
        report = monthly()
        report["conversion_rate"] = .5
        with self.assertRaises(ValueError):
            mod.build_integrated_plan(affiliate_monthly=report)

    def test_unauthorized_staging_report_rejected(self):
        with self.assertRaises(ValueError):
            mod.build_integrated_plan(staging_report={"environment":"production"})

    def test_negative_history_blocks_duplicate_recommendation(self):
        hist=[{"schema_version":1,"event_type":"decision","decision_id":"ux-fix",
              "date":"2026-11-01","title":"Mejora","reason":"Prueba",
              "evidence_ref":"review","category":"ux","seo_risk":"medium","approved":False,"deployed":False},
              {"schema_version":1,"event_type":"outcome","decision_id":"ux-fix",
              "date":"2026-11-04","result":"negative","evidence_ref":"manual-review",
              "manually_verified":True,"approved":False,"deployed":False}]
        result = mod.build_integrated_plan(proposals=[candidate()],history=hist)
        self.assertEqual(result["summary"]["held_for_risk_review"],1)

    def test_executive_report_does_not_claim_sales(self):
        result = mod.build_integrated_plan(affiliate_monthly=monthly())
        md = mod.format_executive(result)
        self.assertIn("Comisiones verificadas: No",md)
        self.assertIn("ninguna publicación",md)
        self.assertNotIn("Crecimiento confirmado",md)

    def test_results_are_deterministic(self):
        a,b=candidate("a"),candidate("b")
        r1=mod.build_integrated_plan(proposals=[a,b])
        r2=mod.build_integrated_plan(proposals=[b,a])
        self.assertEqual(r1,r2)

if __name__ == "__main__":
    unittest.main()
