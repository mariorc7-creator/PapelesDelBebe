#!/usr/bin/env python3
"""Guard production deployment and explicitly suppress noisy SuperAgente previews.

This test is read-only and never calls the Vercel API or triggers deployments.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feature/superagente-foundations-20261106"
STAGING = "staging/superagente-cataluna-v04-20261106"

class VercelDeploymentPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        cls.rules = cls.config["git"]["deploymentEnabled"]
    def test_only_long_lived_feature_branch_is_suppressed(self):
        self.assertEqual(self.rules, {BRANCH: False})
    def test_main_remains_enabled(self):
        self.assertIsNot(self.rules.get("main", True), False)
    def test_staging_remains_eligible_for_recovery(self):
        self.assertIsNot(self.rules.get(STAGING, True), False)
    def test_site_build_configuration_intact(self):
        self.assertEqual(self.config["buildCommand"], "node scripts/build-static.cjs")
        self.assertEqual(self.config["outputDirectory"], "dist")
    def test_legacy_routes_remain_available(self):
        self.assertGreater(len(self.config.get("redirects", [])), 5)

if __name__ == "__main__":
    unittest.main()
