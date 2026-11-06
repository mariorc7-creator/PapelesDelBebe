#!/usr/bin/env python3
"""Verify the disposable preview never mutates original HTML."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location("sandbox", Path(__file__).with_name("superagente_preview_sandbox.py"))
import sys
sys.path.insert(0, str(Path(__file__).parent))
sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox)
def manifest():
    return {"status":"proposal_not_approved","publication_allowed":False,
            "changes":[{"path":"ayudas/index.html","url":"https://example.test/ayudas/",
                        "finding":"clarification","search":"Antiguo","replacement":"Nuevo",
                        "source_urls":["https://www.boe.es/"]}]}
class SandboxTests(unittest.TestCase):
    def test_stages_only_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/"repo"
            page = root/"ayudas/index.html"
            page.parent.mkdir(parents=True)
            page.write_text("<p>Antiguo</p>",encoding="utf-8")
            target = Path(temp)/"staging"
            result = sandbox.stage(root, manifest(), target)
            self.assertEqual(page.read_text(),"<p>Antiguo</p>")
            self.assertEqual((target/"ayudas/index.html").read_text(),"<p>Nuevo</p>")
            self.assertFalse(result["publishable"])
    def test_reject_same_root(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                sandbox.stage(Path(temp), manifest(), Path(temp))
    def test_reject_nested_root(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                sandbox.stage(Path(temp), manifest(), Path(temp)/"nested")
    def test_refuse_existing_sandbox(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"site"
            page=root/"ayudas/index.html"
            page.parent.mkdir(parents=True)
            page.write_text("Antiguo",encoding="utf-8")
            existing=Path(temp)/"existing"
            existing.mkdir()
            with self.assertRaises(ValueError):
                sandbox.stage(root, manifest(), existing)
if __name__=="__main__":
    unittest.main()
