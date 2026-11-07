import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

P = Path(__file__).with_name("batch_release_check.py")
spec = importlib.util.spec_from_file_location("batch_release_check", P)
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)
BASE="a"*40
PAGE='''<!doctype html><html><head><title>Andalucía</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.papelesdelbebe.es/comunidades/andalucia/">
</head><body><header></header><main><h1>Andalucía</h1><section id="ayudas"><a href="/ayudas/">Ayudas</a></section></main><footer></footer></body></html>'''
PATH="comunidades/andalucia/index.html"
def inspect(html=PAGE, previous=PAGE, files=None):
    with TemporaryDirectory() as temp:
        root=Path(temp)
        file=root / PATH
        file.parent.mkdir(parents=True)
        file.write_text(html,encoding="utf-8")
        def fake_git(*args, root=None):
            if args[0]=="diff":
                return "\n".join(files if files is not None else [PATH])+"\n"
            if args[0]=="show":
                return previous
            raise AssertionError(args)
        with patch.object(batch,"git",fake_git):
            return batch.inspect_batch(BASE,root)
class BatchCheckTests(unittest.TestCase):
    def test_valid_batch_still_does_not_authorize_publication(self):
        r=inspect(PAGE.replace("Andalucía</h1>","Ayudas Andalucía</h1>"))
        self.assertTrue(r["technical_checks_passed"])
        self.assertFalse(r["production_deploy_authorized"])
        self.assertFalse(r["official_content_verified"])
    def test_canonical_change_blocks(self):
        r=inspect(PAGE.replace("/comunidades/andalucia/","/comunidades/asturias/"))
        self.assertFalse(r["technical_checks_passed"])
    def test_duplicate_h1_blocks(self):
        r=inspect(PAGE.replace("</main>","<h1>Segundo</h1></main>"))
        self.assertFalse(r["technical_checks_passed"])
    def test_duplicate_ids_blocks(self):
        r=inspect(PAGE.replace("</section>","<p id='ayudas'>Duplicado</p></section>"))
        self.assertFalse(r["technical_checks_passed"])
    def test_missing_viewport_blocks(self):
        r=inspect(PAGE.replace('name="viewport"','name="screen"'))
        self.assertFalse(r["technical_checks_passed"])
    def test_insecure_link_blocks(self):
        r=inspect(PAGE.replace('href="/ayudas/"','href="http://example.com"'))
        self.assertFalse(r["technical_checks_passed"])
    def test_vercel_config_change_requires_technical_release(self):
        r=inspect(files=[PATH,"vercel.json"])
        self.assertFalse(r["technical_checks_passed"])
    def test_empty_release_blocked(self):
        r=inspect(files=[])
        self.assertFalse(r["technical_checks_passed"])
    def test_invalid_base_rejected(self):
        with self.assertRaises(ValueError):
            batch.inspect_batch("main")
    def test_structural_change_blocks(self):
        r=inspect(PAGE.replace("<main>","<div>"))
        self.assertFalse(r["technical_checks_passed"])
if __name__=="__main__":
    unittest.main()
