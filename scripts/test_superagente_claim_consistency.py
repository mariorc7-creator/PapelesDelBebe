import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("superagente_claim_consistency.py")
spec=importlib.util.spec_from_file_location("claim_consistency",P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ClaimConsistencyTests(unittest.TestCase):
    def check(self,kind,old,new,source):
        return m.check_claim(kind,old,new,source)
    def blocked(self,*args):
        with self.assertRaises(ValueError):self.check(*args)
    def test_source_amount_evidence_matches(self):
        r=self.check("amount","300 euros","500 euros",
          "La ayuda por nacimiento para las familias solicitantes es de 500 euros.")
        self.assertTrue(r["mechanical_consistency"])
        self.assertFalse(r["legal_applicability_proven"])
    def test_fabricated_1000_euro_claim_rejected(self):
        self.blocked("amount","300 euros","1.000 euros",
          "La ayuda por nacimiento para las familias solicitantes es de 500 euros.")
    def test_euro_numeric_format_normalized(self):
        self.assertTrue(self.check("amount","300 €","1500 €",
            "La prestación máxima es de 1.500 euros.")["mechanical_consistency"])
    def test_amount_does_not_conflate_150_and_1500(self):
        self.blocked("amount","150 euros","1500 euros",
            "La prestación es de 150 euros.")
    def test_percent_unsupported(self):
        self.blocked("eligibility","Renta máxima 30 %","Renta máxima 40 %",
           "La renta máxima es 30 %.")
    def test_percent_supported(self):
        self.assertTrue(self.check("requirements","Porcentaje 30 %","Porcentaje 40 %",
           "El porcentaje de renta máximo es 40 %.")["mechanical_consistency"])
    def test_deadline_duration_matches(self):
        self.assertTrue(self.check("deadline","Plazo de 1 mes","Plazo de 3 meses",
           "El plazo para solicitar es de 3 meses desde el nacimiento.")["mechanical_consistency"])
    def test_deadline_duration_mismatch(self):
        self.blocked("deadline","Plazo 1 mes","Plazo 3 meses",
           "El plazo para solicitar es de 1 mes desde el nacimiento.")
    def test_dates_spanish_and_iso_equivalent(self):
        self.assertTrue(self.check("deadline","Hasta el 2026-08-01",
           "Hasta el 30 de septiembre de 2026",
           "La convocatoria termina el 2026-09-30.")["mechanical_consistency"])
    def test_deadline_unsupported_date(self):
        self.blocked("deadline","Hasta 2026-08-01","Hasta 2026-12-31",
           "La convocatoria termina el 30 de septiembre de 2026.")
    def test_closed_status_proven_as_literal_not_eligibility(self):
        r=self.check("application_status","Convocatoria abierta",
          "Convocatoria cerrada","La convocatoria se encuentra cerrada.")
        self.assertFalse(r["legal_applicability_proven"])
    def test_false_claim_open_when_closed(self):
        self.blocked("application_status","Convocatoria cerrada",
          "Convocatoria abierta","La convocatoria se encuentra cerrada.")
    def test_both_open_and_closed_in_source_is_ambiguous(self):
        self.blocked("application_status","Convocatoria abierta",
          "Convocatoria cerrada","Antes abierta, ahora cerrada.")
    def test_no_status_token_blocks(self):
        self.blocked("application_status","Plazo anterior","Ya no se admiten solicitudes",
          "Ya no se admiten solicitudes.")
    def test_no_numeric_for_amount_blocks(self):
        self.blocked("amount","Cuantía antigua","Cuantía modificada",
          "La cuantía se modifica.")
    def test_identical_numeric_value_blocks(self):
        self.blocked("amount","Ayuda 500 euros","Prestación 500 euros",
          "La prestación es de 500 euros.")
    def test_eligibility_with_uncheckable_semantic_claim_blocks(self):
        self.blocked("eligibility","Para familias con hijos",
          "Para familias monoparentales",
          "La ayuda es para familias monoparentales.")
    def test_other_must_have_supported_assertion(self):
        self.blocked("other","Texto anterior","Texto completamente nuevo",
          "Este es un nuevo requisito relativo a familias.")
    def test_suspension_status(self):
        self.assertTrue(self.check("application_status","Convocatoria abierta",
          "Convocatoria suspendida","La convocatoria está suspendida.")["mechanical_consistency"])
if __name__=="__main__":
    unittest.main()
