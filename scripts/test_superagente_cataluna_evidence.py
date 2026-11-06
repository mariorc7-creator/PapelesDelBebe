#!/usr/bin/env python3
"""Hermetic tests of source excerpt matching without editorial approval."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("cat",Path(__file__).with_name("superagente_cataluna_evidence.py"))
cat=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cat)
class CataloniaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        p=self.root/"ayuda-nacimiento-cataluna/index.html"
        p.parent.mkdir(parents=True)
        p.write_text("<p>Contenido original</p>",encoding="utf-8")
        self.page=p
        self.source=" ".join([*cat.TOPICS.values(),*cat.ADDITIONAL.values()])
        self.capture={"captures":[{"source_url":cat.URL,"text":self.source,
            "sha256":hashlib.sha256(self.source.encode()).hexdigest(),
            "fetch_method":"https_pinned_public_ip_tls_hostname_no_redirect",
            "captured_at_utc":"2026-11-06T11:00:00+00:00"}]}
    def tearDown(self):self.tmp.cleanup()
    def test_seven_topics_present(self):
        before=self.page.read_bytes()
        result=cat.inspect(self.capture,self.root)
        self.assertEqual(result["seven_topics_with_source_excerpt"],7)
        self.assertEqual(result["missing_excerpts"],[])
        self.assertEqual(self.page.read_bytes(),before)
        self.assertFalse(result["editorial_approval"])
        self.assertFalse(result["review_date_update"])
    def test_missing_deadline_blocks(self):
        inp=self.capture.copy()
        value=self.source.replace(cat.TOPICS["deadline"],"")
        inp={"captures":[{**self.capture["captures"][0],"text":value,
                          "sha256":hashlib.sha256(value.encode()).hexdigest()}]}
        self.assertIn("deadline",cat.inspect(inp,self.root)["missing_excerpts"])
    def test_tampered_digest_blocks(self):
        self.capture["captures"][0]["sha256"]="0"*64
        with self.assertRaises(ValueError):cat.inspect(self.capture,self.root)
    def test_wrong_fetch_method_blocks(self):
        self.capture["captures"][0]["fetch_method"]="untrusted_method"
        with self.assertRaises(ValueError):cat.inspect(self.capture,self.root)
    def test_duplicate_source_blocks(self):
        self.capture["captures"]*=2
        with self.assertRaises(ValueError):cat.inspect(self.capture,self.root)
    def test_missing_source_blocks(self):
        with self.assertRaises(ValueError):cat.inspect({"captures":[]},self.root)
    def test_missing_page_blocks(self):
        self.page.unlink()
        with self.assertRaises(ValueError):cat.inspect(self.capture,self.root)
    def test_extra_old_deadline_must_exist(self):
        value=self.source.replace(cat.ADDITIONAL["old_deadline"],"")
        cap={"captures":[{**self.capture["captures"][0],"text":value,
                          "sha256":hashlib.sha256(value.encode()).hexdigest()}]}
        self.assertIn("old_deadline",cat.inspect(cap,self.root)["missing_excerpts"])
if __name__=="__main__":unittest.main()
