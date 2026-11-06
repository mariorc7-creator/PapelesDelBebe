#!/usr/bin/env python3
"""Offline safety tests for source provenance."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("provenance", Path(__file__).with_name("superagente_source_provenance.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
WATCH = {"sources": [{"url": "https://www.boe.es/", "approved_host": "www.boe.es"}]}

class ProvenanceTests(unittest.TestCase):
    def test_exact_approved_host(self):
        hosts = p.approved_hosts(WATCH)
        report = p.validate({"claims": [{"source_url": "https://www.boe.es/diario_boe/"}]}, hosts)
        self.assertEqual(report["blocked"], 0)
        self.assertFalse(report["results"][0]["publishable"])
    def test_unapproved_domain(self):
        report = p.validate({"claims": [{"source_url": "https://example.com/"}]}, p.approved_hosts(WATCH))
        self.assertEqual(report["results"][0]["errors"], ["unapproved:source_host"])
    def test_subdomain_not_implicitly_trusted(self):
        report = p.validate({"claims": [{"source_url": "https://evil.www.boe.es/"}]}, p.approved_hosts(WATCH))
        self.assertEqual(report["blocked"], 1)
    def test_unencrypted_blocked(self):
        self.assertEqual(p.validate({"claims": [{"source_url": "http://www.boe.es/"}]}, p.approved_hosts(WATCH))["blocked"], 1)
    def test_credentials_blocked(self):
        self.assertEqual(p.validate({"claims": [{"source_url": "https://user@www.boe.es/"}]}, p.approved_hosts(WATCH))["blocked"], 1)
    def test_nonstandard_port_blocked(self):
        self.assertEqual(p.validate({"claims": [{"source_url": "https://www.boe.es:8080/"}]}, p.approved_hosts(WATCH))["blocked"], 1)
    def test_malformed_watchlist_blocks(self):
        with self.assertRaises(ValueError):
            p.approved_hosts({"sources": [{"url": "https://example.com/", "approved_host": "www.boe.es"}]})
    def test_empty_watchlist_blocks(self):
        with self.assertRaises(ValueError):
            p.approved_hosts({"sources": []})
    def test_malformed_claim_blocks(self):
        self.assertEqual(p.validate({"claims": [None]}, p.approved_hosts(WATCH))["blocked"], 1)
    def test_empty_claims_fail(self):
        with self.assertRaises(ValueError):
            p.validate({"claims": []}, p.approved_hosts(WATCH))

if __name__ == "__main__":
    unittest.main()
