#!/usr/bin/env python3
"""Offline tests: preview never changes original HTML."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("preview", Path(__file__).with_name("superagente_editorial_preview.py"))
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)
ITEM = {"path":"example/index.html", "url":"https://www.papelesdelbebe.es/example/",
        "search":"Texto antiguo.", "replacement":"Texto nuevo.",
        "finding":"clarification", "source_urls":["https://www.boe.es/"]}
MANIFEST = {"status":"proposal_not_approved", "publication_allowed":False, "changes":[ITEM]}

class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.page = self.root / "example/index.html"
        self.page.parent.mkdir()
        self.page.write_text("<p>Texto antiguo.</p>\n", encoding="utf-8")
    def tearDown(self):
        self.tmp.cleanup()
    def test_diff_generated_without_mutating_source(self):
        before = self.page.read_bytes()
        report = preview.build(self.root, MANIFEST)
        self.assertIn("+<p>Texto nuevo.</p>", report["diffs"][0]["unified_diff"])
        self.assertEqual(self.page.read_bytes(), before)
        self.assertFalse(report["publication_allowed"])
    def test_stale_anchor_blocks(self):
        with self.assertRaisesRegex(ValueError, "stale"):
            preview.build(self.root, {**MANIFEST, "changes":[{**ITEM,"search":"Ausente"}]})
    def test_ambiguous_anchor_blocks(self):
        self.page.write_text("Texto antiguo. Texto antiguo.")
        with self.assertRaisesRegex(ValueError, "unique"):
            preview.build(self.root, MANIFEST)
    def test_path_traversal_blocks(self):
        with self.assertRaises(ValueError):
            preview.build(self.root, {**MANIFEST, "changes":[{**ITEM,"path":"../outside.html"}]})
    def test_publication_flag_blocks(self):
        with self.assertRaises(ValueError):
            preview.build(self.root, {**MANIFEST,"publication_allowed":True})
    def test_approved_status_blocks(self):
        with self.assertRaises(ValueError):
            preview.build(self.root, {**MANIFEST,"status":"approved"})
    def test_invalid_source_blocks(self):
        with self.assertRaises(ValueError):
            preview.build(self.root, {**MANIFEST,"changes":[{**ITEM,"source_urls":["http://example.com"]}]})
    def test_duplicate_page_blocks(self):
        with self.assertRaises(ValueError):
            preview.build(self.root, {**MANIFEST,"changes":[ITEM,ITEM]})
    def test_noop_blocks(self):
        with self.assertRaises(ValueError):
            preview.build(self.root, {**MANIFEST,"changes":[{**ITEM,"replacement":"Texto antiguo."}]})
    def test_empty_blocks(self):
        with self.assertRaises(ValueError):
            preview.build(self.root, {**MANIFEST,"changes":[]})

if __name__ == "__main__":
    unittest.main()
