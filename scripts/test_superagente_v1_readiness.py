import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("superagente_v1_readiness.py")
spec=importlib.util.spec_from_file_location("v1_readiness",P)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

def integrated(rollback=False):
    return {"mode":"offline_integrated_review","gates":{
        "publish_to_production_allowed":False,"automation_enabled":False,
        "rollback_verified_in_remote_preview":rollback,
        "staging_requires_reverification":not rollback,
        "candidate_cost_exceeds_budget":False}}

def evidence(value):
    return {key:value for key in gate.REQUIRED}

class V1ReadinessTests(unittest.TestCase):
    def test_defaults_fail_closed(self):
        result=gate.assess(integrated(),{})
        self.assertEqual(result["operational_readiness"],"blocked")
        self.assertFalse(result["automatic_activation_allowed"])
        self.assertFalse(result["production_deployment_allowed"])
        self.assertFalse(result["gsc_wizard_allowed"])

    def test_reversal_proof_requires_real_remote_state(self):
        r=gate.assess(integrated(rollback=False),evidence(True))
        self.assertIn("rollback_verified_in_remote_preview",r["blocking_reasons"])
        self.assertEqual(r["operational_readiness"],"blocked")

    def test_missing_one_criterion_blocks(self):
        for name in gate.REQUIRED:
            with self.subTest(name=name):
                manifest=evidence(True)
                manifest[name]=False
                self.assertIn(name,gate.assess(integrated(True),manifest)["blocking_reasons"])

    def test_even_all_confirmed_never_enables_auto_release(self):
        r=gate.assess(integrated(True),evidence(True))
        self.assertEqual(r["operational_readiness"],"ready_for_human_go_no_go")
        self.assertFalse(r["automatic_activation_allowed"])
        self.assertFalse(r["production_deployment_allowed"])

    def test_refuse_upstream_publishable_report(self):
        obj=integrated()
        obj["gates"]["publish_to_production_allowed"]=True
        with self.assertRaises(ValueError):
            gate.assess(obj,evidence(True))

    def test_budget_overrun_blocks(self):
        obj=integrated(True)
        obj["gates"]["candidate_cost_exceeds_budget"]=True
        self.assertIn("budget_exceeded",gate.assess(obj,evidence(True))["blocking_reasons"])

    def test_invalid_report_rejected(self):
        with self.assertRaises(ValueError):
            gate.assess({"mode":"published"},evidence(True))

if __name__=="__main__":
    unittest.main()
