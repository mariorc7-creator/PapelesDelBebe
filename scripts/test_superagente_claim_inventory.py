#!/usr/bin/env python3
"""Offline tests for real-page assertion mapping."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("inventory", Path(__file__).with_name("superagente_claim_inventory.py"))
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)

class InventoryTests(unittest.TestCase):
    def test_claims_anchor_to_real_html_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "ayudas" / "index.html"
            page.parent.mkdir()
            page.write_text('<main><p>La ayuda es de 300 €.</p><p>Plazo de 15 días.</p><script>999 euros</script></main>', encoding="utf-8")
            sitemap = root / "sitemap.xml"
            sitemap.write_text('<urlset><url><loc>https://www.papelesdelbebe.es/ayudas/</loc></url></urlset>', encoding="utf-8")
            before = page.read_bytes()
            report = inventory.extract(root, sitemap)
            claims = report["pages"][0]["claims"]
            self.assertEqual(len(claims), 2)
            self.assertEqual({x["kind"] for x in claims}, {"amount", "deadline"})
            self.assertTrue(all(x["claim_id"] and x["paragraph_sha256"] for x in claims))
            self.assertEqual(page.read_bytes(), before)
            self.assertEqual(report, inventory.extract(root, sitemap))
    def test_ignores_nonrelevant_and_missing_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sitemap = root / "sitemap.xml"
            sitemap.write_text('<urlset><url><loc>https://www.papelesdelbebe.es/contacto/</loc></url><url><loc>https://www.papelesdelbebe.es/ayudas/inexistente/</loc></url></urlset>', encoding="utf-8")
            self.assertEqual(inventory.extract(root, sitemap)["pages"], [])
    def test_no_amount_inside_script_only(self):
        parser = inventory.Segments()
        parser.feed('<p>Texto</p><script>1000 euros</script><p>Sin cifras</p>')
        self.assertEqual(len(parser.segments), 2)

if __name__ == "__main__":
    unittest.main()
