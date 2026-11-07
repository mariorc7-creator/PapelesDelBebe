"""Regional 2026 content/SEO guard, read-only and fail-closed."""
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ("cataluna", "andalucia", "extremadura", "pais-vasco", "islas-baleares", "navarra", "asturias")
BASE = "842d106411a1ed69adda65080177dc4ac1589767"
class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.tags = []
        self.anchors = []
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags.append(tag)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a":
            self.anchors.append(attrs.get("href", ""))

class RegionalContentSafety(unittest.TestCase):
    def page(self, slug):
        return (ROOT / "comunidades" / slug / "index.html").read_text(encoding="utf-8")
    def original(self, slug):
        return subprocess.check_output(["git", "show", f"{BASE}:comunidades/{slug}/index.html"],cwd=ROOT,text=True)
    def test_existing_global_structure_intact(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                before, now = self.original(slug), self.page(slug)
                for fragment in ('<header>', '<main>', '</main>', '<footer>', '</footer>'):
                    self.assertEqual(before.count(fragment), now.count(fragment))
                self.assertEqual(re.search(r'<link rel="canonical"[^>]*>',before).group(),
                                 re.search(r'<link rel="canonical"[^>]*>',now).group())
                self.assertEqual(re.search(r'<h1[^>]*>.*?</h1>',before).group(),
                                 re.search(r'<h1[^>]*>.*?</h1>',now).group())
                self.assertEqual(re.search(r'<meta name="robots"[^>]*>',before).group(),
                                 re.search(r'<meta name="robots"[^>]*>',now).group())
    def test_seven_pages_updated_and_have_official_links(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                now=self.page(slug)
                self.assertIn('id="actualizacion-regional-2026"',now)
                self.assertIn('Información revisada: 7 de noviembre de 2026',now)
                self.assertIn('Última revisión: 7 de noviembre de 2026',now)
                self.assertIn('"dateModified":"2026-11-07"',now)
                self.assertIn('href="https://',now)
                self.assertIn('contrasta',now.lower().replace('contrastada','contrasta'))
    def test_internal_anchors_and_metadata(self):
        titles=set()
        for slug in SLUGS:
            html=self.page(slug)
            page=PageParser()
            page.feed(html)
            self.assertEqual(len(page.ids),len(set(page.ids)),slug)
            self.assertEqual(len(re.findall(r"<h1(?:\s|>)",html)),1,slug)
            title=re.search(r"<title>(.*?)</title>",html,re.S).group(1)
            self.assertNotIn(title,titles)
            titles.add(title)
            self.assertNotIn('rel="canonical" href="http://',html)
            for url in page.anchors:
                if url.startswith("http"):
                    self.assertEqual(urlsplit(url).scheme,"https",url)
    def test_mobile_viewport_remains_unchanged(self):
        for slug in SLUGS:
            before=self.original(slug)
            after=self.page(slug)
            self.assertEqual(
                re.findall(r'<meta name="viewport"[^>]*>',before),
                re.findall(r'<meta name="viewport"[^>]*>',after))
    def test_navarra_closed_deadline_not_called_open(self):
        html=self.page("navarra")
        self.assertNotIn("convocatoria 2026, abierta hasta el 2 de noviembre",html)
    def test_no_automatic_deploy(self):
        receipt=json.loads((ROOT/"release/regional-v25-v31-readiness.json").read_text(encoding="utf-8"))
        self.assertTrue(all(v["editorial_approval"] is False for v in receipt.values()))
        self.assertTrue(all(v["rollback_remotely_verified"] is False for v in receipt.values()))

if __name__ == "__main__":
    unittest.main()
