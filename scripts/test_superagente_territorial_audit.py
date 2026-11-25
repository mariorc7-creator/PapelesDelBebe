import tempfile
import unittest
from pathlib import Path
from superagente_territorial_audit import audit

class TerritorialAuditTest(unittest.TestCase):
    def test_bidirectional_and_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "standard.md").write_text("standard")
            for slug, html in [("comunidades/test", '<main><a href="/guide/">Guide</a></main>'),
                               ("guide-source", '<main><a href="/comunidades/test/">Hub</a> example text</main>')]:
                folder = root / slug
                folder.mkdir(parents=True)
                (folder / "index.html").write_text(html)
            policy = {"schema_version": 1, "publication_allowed": False,
                      "editorial_standard": "standard.md",
                      "territories": {"test": ["guide-source"]},
                      "public_aliases": {"guide-source": "guide"}}
            report = audit(root, policy)
            self.assertEqual(report["checked"], 1)
            self.assertFalse(report["issues"])
            self.assertFalse(report["publication_allowed"])
            (root / "guide-source/index.html").write_text("<main>No return</main>")
            self.assertEqual(len(audit(root, policy)["issues"]), 1)
            policy["publication_allowed"] = True
            with self.assertRaises(ValueError):
                audit(root, policy)

if __name__ == "__main__":
    unittest.main()
