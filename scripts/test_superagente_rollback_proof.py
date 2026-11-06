#!/usr/bin/env python3
"""Regression tests for byte-exact rollback without touching originals."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("rollback", Path(__file__).with_name("superagente_rollback_proof.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ITEM = {"path": "ayuda/index.html", "url": "https://www.papelesdelbebe.es/ayuda/",
        "search": "Plazo antiguo.", "replacement": "Plazo nuevo.",
        "finding": "clarification", "source_urls": ["https://www.boe.es/"]}
def manifest(items=None):
    return {"package_id": "test", "status": "proposal_not_approved",
            "publication_allowed": False, "changes": [ITEM] if items is None else items}
class RollbackProofTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.html = self.root / "ayuda/index.html"
        self.html.parent.mkdir(parents=True)
        self.original = "<html>\n<p>Plazo antiguo.</p>\n</html>\n".encode("utf-8")
        self.html.write_bytes(self.original)
    def tearDown(self):
        self.tmp.cleanup()
    def test_original_never_changed(self):
        result = module.prove(self.root, manifest())
        self.assertEqual(self.html.read_bytes(), self.original)
        self.assertTrue(result["files"][0]["byte_exact_rollback"])
        self.assertEqual(result["files"][0]["restored_sha256"], result["files"][0]["original_sha256"])
    def test_production_rollback_not_claimed(self):
        result = module.prove(self.root, manifest())
        self.assertFalse(result["production_rollback_tested"])
        self.assertFalse(result["publishable"])
    def test_two_files(self):
        other = self.root / "otra/index.html"
        other.parent.mkdir(parents=True)
        other.write_text("<p>Texto viejo.</p>", encoding="utf-8")
        second = {**ITEM, "path": "otra/index.html", "search": "Texto viejo.",
                  "replacement": "Texto nuevo."}
        report = module.prove(self.root, manifest([ITEM, second]))
        self.assertEqual(len(report["files"]), 2)
        self.assertEqual(other.read_text(), "<p>Texto viejo.</p>")
    def test_missing_anchor_fails(self):
        with self.assertRaises(ValueError):
            module.prove(self.root, manifest([{**ITEM, "search": "Ausente"}]))
        self.assertEqual(self.html.read_bytes(), self.original)
    def test_ambiguous_anchor_fails(self):
        self.html.write_text("Plazo antiguo. Plazo antiguo.", encoding="utf-8")
        with self.assertRaises(ValueError):
            module.prove(self.root, manifest())
    def test_nonapproved_manifest_fails(self):
        with self.assertRaises(ValueError):
            module.prove(self.root, {**manifest(), "publication_allowed": True})
    def test_duplicate_path_fails(self):
        with self.assertRaises(ValueError):
            module.prove(self.root, manifest([ITEM, ITEM]))
    def test_missing_page_fails(self):
        with self.assertRaises(ValueError):
            module.prove(self.root, manifest([{**ITEM, "path": "missing/index.html"}]))
    def test_unicode_roundtrip(self):
        self.html.write_bytes("<p>Plazo antiguo. € niño á</p>".encode("utf-8"))
        before = self.html.read_bytes()
        report = module.prove(self.root, manifest())
        self.assertEqual(self.html.read_bytes(), before)
        self.assertEqual(report["files"][0]["original_sha256"], report["files"][0]["restored_sha256"])
    def test_path_traversal_fails(self):
        with self.assertRaises(ValueError):
            module.prove(self.root, manifest([{**ITEM, "path": "../outside/index.html"}]))

if __name__ == "__main__":
    unittest.main()
