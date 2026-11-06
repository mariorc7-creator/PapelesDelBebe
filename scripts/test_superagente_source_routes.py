#!/usr/bin/env python3
"""Unit tests for the read-only source discovery routing queue."""
import importlib.util
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location("routes", Path(__file__).with_name("superagente_source_routes.py"))
routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routes)
PAGE = "https://www.papelesdelbebe.es/deduccion-maternidad/"
VALID = {"page": PAGE, "topic": "deduccion_maternidad", "jurisdiction": "ES",
         "priority": "P0", "authority": "AEAT",
         "source_status": "needs_exact_official_document"}
def check(items, urls=None):
    return routes.validate_routes({"schema_version": 1, "routes": items}, {PAGE} if urls is None else urls)
class RouteTests(unittest.TestCase):
    def test_valid_route_is_not_verified(self):
        result = check([VALID])
        self.assertEqual(result["accepted"], 1)
        self.assertFalse(result["queue"][0]["publishable"])
        self.assertFalse(result["queue"][0]["legal_verification"])
    def test_unknown_page_blocked(self):
        self.assertIn("missing:sitemap_page", check([VALID], set())["problems"][0]["errors"])
    def test_duplicate_page_blocked(self):
        self.assertIn("duplicate:page", check([VALID, VALID])["problems"][0]["errors"])
    def test_fake_verification_blocked(self):
        self.assertIn("blocked:unsupported_verification_claim", check([{**VALID, "approved": True}])["problems"][0]["errors"])
    def test_source_url_not_accepted_in_discovery(self):
        self.assertIn("blocked:unsupported_verification_claim", check([{**VALID, "source_url": "https://www.boe.es/"}])["problems"][0]["errors"])
    def test_invalid_priority(self):
        self.assertIn("invalid:priority", check([{**VALID, "priority": "P9"}])["problems"][0]["errors"])
    def test_missing_authority(self):
        self.assertIn("missing:authority", check([{**VALID, "authority": ""}])["problems"][0]["errors"])
    def test_malformed_route(self):
        self.assertIn("invalid:route", check([None])["problems"][0]["errors"])
    def test_empty_routes_fail(self):
        with self.assertRaises(ValueError):
            check([])
    def test_schema_version_required(self):
        with self.assertRaises(ValueError):
            routes.validate_routes({"schema_version": 2, "routes": [VALID]}, {PAGE})
if __name__ == "__main__":
    unittest.main()
