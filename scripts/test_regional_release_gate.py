import importlib.util
from pathlib import Path
import unittest

FILE=Path(__file__).with_name("regional_release_gate.py")
spec=importlib.util.spec_from_file_location("regional_release_gate",FILE)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class RegionalReleaseGateTests(unittest.TestCase):
    def test_all_versions_present(self):
        self.assertEqual(len(gate.REGIONS),7)
        self.assertIn("comunidades/islas-baleares/index.html",gate.REGIONS.values())

    def test_no_changes_blocks_release(self):
        evidence={key:{k:True for k in gate.NEEDED} for key in gate.REGIONS}
        result=gate.release_readiness(set(),evidence,set(gate.REGIONS.values()))
        self.assertFalse(result["production_deploy_allowed"])
        self.assertEqual(result["ready_count"],0)

    def test_missing_official_sources_blocks_release(self):
        evidence={key:{k:True for k in gate.NEEDED} for key in gate.REGIONS}
        evidence["v3.1"]["verified_official_sources"]=False
        result=gate.release_readiness(set(gate.REGIONS.values()),evidence,set(gate.REGIONS.values()))
        self.assertFalse(result["production_deploy_allowed"])

    def test_missing_remote_rollback_blocks_release(self):
        evidence={key:{k:True for k in gate.NEEDED} for key in gate.REGIONS}
        evidence["v2.5"]["rollback_remotely_verified"]=False
        result=gate.release_readiness(set(gate.REGIONS.values()),evidence,set(gate.REGIONS.values()))
        self.assertFalse(result["production_deploy_allowed"])

    def test_missing_mobile_qa_blocks_release(self):
        evidence={key:{k:True for k in gate.NEEDED} for key in gate.REGIONS}
        evidence["v2.8"]["mobile_qa_passed"]=False
        result=gate.release_readiness(set(gate.REGIONS.values()),evidence,set(gate.REGIONS.values()))
        self.assertFalse(result["production_deploy_allowed"])

    def test_missing_page_blocks_release(self):
        evidence={key:{k:True for k in gate.NEEDED} for key in gate.REGIONS}
        result=gate.release_readiness(set(gate.REGIONS.values()),evidence,set())
        self.assertFalse(result["production_deploy_allowed"])

    def test_only_all_verified_all_changed_passes_structural_gate(self):
        evidence={key:{k:True for k in gate.NEEDED} for key in gate.REGIONS}
        result=gate.release_readiness(set(gate.REGIONS.values()),evidence,set(gate.REGIONS.values()))
        self.assertTrue(result["production_deploy_allowed"])

    def test_unverified_receipt_boolean_must_be_literal_true(self):
        evidence={key:{k:True for k in gate.NEEDED} for key in gate.REGIONS}
        evidence["v2.7"]["editorial_approval"]="yes"
        result=gate.release_readiness(set(gate.REGIONS.values()),evidence,set(gate.REGIONS.values()))
        self.assertFalse(result["production_deploy_allowed"])

if __name__=="__main__":
    unittest.main()
