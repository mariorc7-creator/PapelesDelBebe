import importlib.util
from pathlib import Path
from copy import deepcopy
import unittest
P=Path(__file__).with_name("superagente_scope_verifier.py")
s=importlib.util.spec_from_file_location("scope_verifier",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

TEXT=("La Prestación por nacimiento de Cataluña se concede a Familias con renta limitada. "
      "Se aplican Excepciones por domicilio. Vigencia desde 2026-01-01 hasta 2026-12-31. "
      "La convocatoria está abierta.")
SCOPE={"jurisdiction":"Cataluña","benefit":"Prestación por nacimiento",
       "beneficiaries":"Familias con renta limitada","exceptions":"Excepciones por domicilio",
       "effective_from":"2026-01-01","effective_until":"2026-12-31","application_status":"open"}
LITERALS={"jurisdiction":"Cataluña","benefit":"Prestación por nacimiento",
       "beneficiaries":"Familias con renta limitada","exceptions":"Excepciones por domicilio",
       "effective_from":"2026-01-01","effective_until":"2026-12-31","application_status":"abierta"}

def evidence():
    return {k:{"quote":TEXT,"literal":v} for k,v in LITERALS.items()}

class ScopeTests(unittest.TestCase):
    def test_positive_with_seven_source_bound_quotes(self):
        r=m.verify_scope(SCOPE,evidence(),TEXT)
        self.assertEqual(len(r["scope_citations"]),7)
        self.assertFalse(r["legal_applicability_proven"])
        self.assertFalse(r["automatic_publication_allowed"])
    def test_missing_exception_evidence_blocks(self):
        e=evidence();e.pop("exceptions")
        with self.assertRaises(ValueError):m.verify_scope(SCOPE,e,TEXT)
    def test_invented_beneficiary_blocks(self):
        s=dict(SCOPE);s["beneficiaries"]="Todas las familias"
        with self.assertRaises(ValueError):m.verify_scope(s,evidence(),TEXT)
    def test_unsupported_quote_blocks(self):
        e=evidence();e["jurisdiction"]["quote"]="La prestación en Murcia está abierta."
        with self.assertRaises(ValueError):m.verify_scope(SCOPE,e,TEXT)
    def test_fabricated_exception_blocks(self):
        e=evidence();e["exceptions"]["literal"]="Sin excepciones"
        with self.assertRaises(ValueError):m.verify_scope(SCOPE,e,TEXT)
    def test_wrong_effective_date_blocks(self):
        s=dict(SCOPE);s["effective_from"]="2025-01-01"
        with self.assertRaises(ValueError):m.verify_scope(s,evidence(),TEXT)
    def test_invalid_calendar_date_blocks(self):
        s=dict(SCOPE);s["effective_until"]="2026-02-31"
        with self.assertRaises(ValueError):m.verify_scope(s,evidence(),TEXT)
    def test_status_closed_not_supported_by_open_quote(self):
        s=dict(SCOPE);s["application_status"]="closed"
        with self.assertRaises(ValueError):m.verify_scope(s,evidence(),TEXT)
    def test_status_conflict_in_quote_blocks(self):
        text=TEXT+" Pero la convocatoria anterior estaba cerrada."
        e=evidence()
        for item in e.values():item["quote"]=text
        with self.assertRaises(ValueError):m.verify_scope(SCOPE,e,text)
    def test_vague_exception_blocks(self):
        e=evidence(); e["exceptions"]["literal"]="Consultar"
        with self.assertRaises(ValueError):m.verify_scope(SCOPE,e,TEXT)
    def test_future_dates_reverse_blocks(self):
        s=dict(SCOPE);s["effective_from"],s["effective_until"]=s["effective_until"],s["effective_from"]
        with self.assertRaises(ValueError):m.verify_scope(s,evidence(),TEXT)
    def test_negation_flags_specialist_review(self):
        text=TEXT.replace("Excepciones por domicilio","Sin personas excluidas")
        s=dict(SCOPE);s["exceptions"]="Sin personas excluidas"
        e=evidence()
        e["exceptions"]["literal"]="Sin personas excluidas"
        for item in e.values():item["quote"]=text
        r=m.verify_scope(s,e,text)
        self.assertTrue(r["potential_exclusion_requires_review"])
    def test_absent_full_source_blocks(self):
        with self.assertRaises(ValueError):m.verify_scope(SCOPE,evidence(),"")
    def test_empty_benefit_blocks(self):
        s=dict(SCOPE);s["benefit"]=""
        with self.assertRaises(ValueError):m.verify_scope(s,evidence(),TEXT)
if __name__=="__main__": unittest.main()
