#!/usr/bin/env python3
"""Source capture tests using fake network responses; no outbound requests."""
import importlib.util
import io
import unittest
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path

spec = importlib.util.spec_from_file_location("capture", Path(__file__).with_name("superagente_source_capture.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ENTRY = {"url": "https://www.boe.es/", "approved_host": "www.boe.es"}
def resolver(*args, **kwargs):
    return [(None, None, None, None, ("8.8.8.8", 443))]
class Reply:
    def __init__(self, body=b"<p>Plazo de 15 dias</p>", content_type="text/html; charset=utf-8", final="https://www.boe.es/"):
        self.stream = io.BytesIO(body)
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.final = final
    def __enter__(self): return self
    def __exit__(self, *args): self.stream.close()
    def read(self, count): return self.stream.read(count)
    def geturl(self): return self.final
class Opener:
    def __init__(self, reply): self.reply = reply
    def open(self, req, timeout): return self.reply
class CaptureTests(unittest.TestCase):
    def test_capture_integrity(self):
        result = mod.capture(ENTRY, opener=Opener(Reply()), resolver=resolver,
                             now=datetime(2026, 11, 6, tzinfo=timezone.utc))
        self.assertEqual(result["text"], "Plazo de 15 dias")
        self.assertEqual(result["captured_on"], "2026-11-06")
        self.assertFalse(result["source_provenance_verified"])
    def test_reject_different_host(self):
        with self.assertRaises(ValueError):
            mod.validate_url({**ENTRY, "url": "https://evil.example/"}, resolver)
    def test_reject_private_address(self):
        with self.assertRaises(ValueError):
            mod.validate_url(ENTRY, lambda *args, **kwargs: [(None,None,None,None,("127.0.0.1",443))])
    def test_reject_redirect(self):
        with self.assertRaises(ValueError):
            mod.capture(ENTRY, opener=Opener(Reply(final="https://elsewhere.test/")), resolver=resolver)
    def test_reject_non_html(self):
        with self.assertRaises(ValueError):
            mod.capture(ENTRY, opener=Opener(Reply(content_type="application/pdf")), resolver=resolver)
    def test_reject_oversize(self):
        with self.assertRaises(ValueError):
            mod.capture(ENTRY, opener=Opener(Reply(body=b"x" * (mod.MAX_BYTES + 1))), resolver=resolver)
    def test_reject_empty(self):
        with self.assertRaises(ValueError):
            mod.capture(ENTRY, opener=Opener(Reply(body=b"<script>hidden</script>")), resolver=resolver)
    def test_skips_script(self):
        result = mod.capture(ENTRY, opener=Opener(Reply(body=b"<p>Valid</p><script>Fake</script>")), resolver=resolver)
        self.assertEqual(result["text"], "Valid")
    def test_failure_recorded(self):
        report = mod.run({"sources": [ENTRY]}, fetch=lambda item: (_ for _ in ()).throw(ValueError("blocked")))
        self.assertEqual(len(report["failures"]), 1)
    def test_empty_watchlist(self):
        with self.assertRaises(ValueError):
            mod.run({"sources": []})
if __name__ == "__main__":
    unittest.main()
