import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=Path(__file__).with_name("superagente_real_legal_cases.py")
spec=importlib.util.spec_from_file_location("real_cases",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RegionalAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book=json.loads((ROOT/"superagente/acceptance/regional-legal-2026.json").read_text(encoding="utf-8"))
    def test_all_official_2026_regression_scenarios(self):
        r=m.validate_casebook(self.book)
        self.assertEqual(r["passed"],len(self.book["cases"]))
        self.assertGreaterEqual(r["passed"],20)
        self.assertFalse(r["production_publication_allowed"])
        self.assertFalse(r["automatic_legal_truth_established"])
    def test_each_answer_still_requires_real_eligibility_review(self):
        for row in self.book["cases"]:
            with self.subTest(id=row["id"]):
                r=m.assess(row["input"],row.get("as_of","2026-11-07"))
                self.assertFalse(r["eligible_confirmed"])
                self.assertFalse(r["publication_allowed"])
                self.assertTrue(r["source"].startswith("https://"))
    def test_nonexistent_scheme_is_blocked(self):
        with self.assertRaises(ValueError):
            m.assess({"scheme":"fictional","event_date":"2026-05-01"})
    def test_invalid_date_is_blocked(self):
        with self.assertRaises(ValueError):
            m.assess({"scheme":"cataluna","event_date":"2026-02-31"})
    def test_asturias_general_portal_deadline_does_not_override_individual_cutoff(self):
        r=m.assess({"scheme":"asturias","event_date":"2026-04-15","child_order":1,"depopulated_municipality":False})
        self.assertEqual(r["verdict"],"individual_deadline_passed")
        self.assertEqual(r["deadline"],"2026-06-15")
    def test_cataluna_month_end_respects_calendar(self):
        self.assertEqual(m.add_months(m.as_date("2026-08-31"),3).isoformat(),"2026-11-30")
        self.assertEqual(m.add_months(m.as_date("2026-01-31"),1).isoformat(),"2026-02-28")
    def test_extremadura_closed_does_not_mean_future_calls_closed(self):
        r=m.assess({"scheme":"extremadura","event_date":"2026-06-01","population":1000},
                   "2026-11-07")
        self.assertEqual(r["verdict"],"closed")
        self.assertIn("2026",r["reason"])
    def test_missing_pop_not_assumed_small(self):
        r=m.assess({"scheme":"extremadura","event_date":"2026-06-01"})
        self.assertEqual(r["verdict"],"manual_review")
    def test_prepublished_asturias_needs_extract(self):
        r=m.assess({"scheme":"asturias","event_date":"2026-03-31"})
        self.assertEqual(r["verdict"],"manual_review")
        self.assertIsNone(r["deadline"])
    def test_casebook_rejects_relabelled_expected_legal_answer(self):
        b=json.loads(json.dumps(self.book))
        b["cases"][0]["expected"]["verdict"]="open_pending_checks"
        with self.assertRaises(ValueError):
            m.validate_casebook(b)

if __name__=="__main__":
    unittest.main()
