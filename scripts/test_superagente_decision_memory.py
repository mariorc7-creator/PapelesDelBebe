import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

MODULE = Path(__file__).with_name("superagente_decision_memory.py")
spec = importlib.util.spec_from_file_location("decision_memory", MODULE)
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)

def decision(id_="fix-navigation"):
    return {
        "schema_version": 1, "event_type": "decision", "decision_id": id_,
        "date": "2026-11-07", "title": "Revisar navegación", "reason": "Dificultad para localizar trámite",
        "evidence_ref": "issue-123", "category": "ux", "seo_risk": "low",
        "approved": False, "deployed": False,
    }

def outcome(id_="fix-navigation",result="negative"):
    return {
        "schema_version": 1, "event_type": "outcome", "decision_id": id_,
        "date": "2026-11-14", "result": result, "evidence_ref": "qa-report-9",
        "manually_verified": True, "approved": False, "deployed": False,
    }

def candidate(id_="fix-navigation",risk="low",basis="hypothesis",benefit="50",category="ux"):
    return {
        "id": id_, "title": "Revisar navegación", "evidence_ref": "issue-123",
        "category": category, "seo_risk": risk, "urgency": "high",
        "impact_basis": basis,
        "expected_monthly_benefit_eur": benefit,
        "impact_evidence_ref": "revenue-report" if basis == "verified" else None,
        "cost_eur": "10", "effort_hours": "2"
    }

class DecisionMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.history = Path(self.tmp.name) / "private-history.jsonl"

    def test_append_and_replay_history(self):
        self.assertEqual(memory.append_event(self.history, decision()), 1)
        self.assertEqual(memory.append_event(self.history, outcome()), 2)
        self.assertEqual(len(memory.read_history(self.history)), 2)

    def test_reject_duplicate_decision(self):
        memory.append_event(self.history, decision())
        with self.assertRaises(ValueError):
            memory.append_event(self.history, decision())
        self.assertEqual(len(memory.read_history(self.history)), 1)

    def test_reject_unlinked_outcome(self):
        with self.assertRaises(ValueError):
            memory.append_event(self.history, outcome())

    def test_reject_outcome_without_manual_verification(self):
        memory.append_event(self.history, decision())
        event = outcome()
        event["manually_verified"] = False
        with self.assertRaises(ValueError):
            memory.append_event(self.history, event)

    def test_reject_events_that_can_publish(self):
        event = decision()
        event["deployed"] = True
        with self.assertRaises(ValueError):
            memory.append_event(self.history, event)

    def test_previous_negative_result_blocks_repeating_change(self):
        history = [decision(), outcome()]
        plan = memory.priority_plan([candidate()], history)
        item = plan["items"][0]
        self.assertTrue(item["prior_negative_outcome"])
        self.assertEqual(item["status"], "hold_for_manual_risk_review")
        self.assertFalse(item["publication_allowed"])

    def test_critical_risk_is_held_even_for_large_benefit(self):
        plan = memory.priority_plan([candidate(risk="critical", benefit="100000")], [])
        self.assertEqual(plan["items"][0]["status"], "hold_for_manual_risk_review")

    def test_legal_changes_always_held(self):
        plan = memory.priority_plan([candidate(category="legal", risk="low")], [])
        self.assertEqual(plan["items"][0]["status"], "hold_for_manual_risk_review")

    def test_unknown_impact_requires_missing_numeric_estimate(self):
        good = candidate(basis="unknown", benefit=None)
        self.assertIsNone(memory.priority_plan([good], [])["items"][0]["estimated_monthly_benefit_eur"])
        with self.assertRaises(ValueError):
            memory.priority_plan([candidate(basis="unknown", benefit="200")], [])

    def test_verified_impact_requires_reference(self):
        item = candidate(basis="verified")
        item["impact_evidence_ref"] = ""
        with self.assertRaises(ValueError):
            memory.priority_plan([item], [])

    def test_no_automatic_publishing_or_seo_changes(self):
        plan = memory.priority_plan([candidate()], [])
        self.assertFalse(plan["automatic_publication"])
        self.assertFalse(plan["automated_deployment"])
        self.assertTrue(plan["require_seo_mobile_qa"])
        self.assertTrue(plan["require_editorial_approval"])

    def test_deterministic_ranking(self):
        a = candidate(id_="a", benefit="100")
        b = candidate(id_="b", benefit="10")
        self.assertEqual(memory.priority_plan([a,b], []), memory.priority_plan([b,a], []))
        self.assertEqual(memory.priority_plan([a,b], [])["items"][0]["id"], "a")

    def test_reject_negative_cost(self):
        item = candidate()
        item["cost_eur"] = "-1"
        with self.assertRaises(ValueError):
            memory.priority_plan([item], [])

    def test_reject_fake_boolean_cost(self):
        item = candidate()
        item["cost_eur"] = True
        with self.assertRaises(ValueError):
            memory.priority_plan([item], [])

if __name__ == "__main__":
    unittest.main()
