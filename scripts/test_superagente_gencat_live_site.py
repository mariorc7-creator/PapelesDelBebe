"""Full factual batch smoke test against CURRENT production HTML copies.

Simulation only: 700/800 EUR values are intentionally synthetic and NEVER
written into the real repository. Source conditions are a controlled fixture.
"""
import importlib.util
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=Path(__file__).with_name("superagente_gencat_amount_sync.py")
spec=importlib.util.spec_from_file_location("sync_gencat",P)
sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)

class LiveSiteSmokeTests(unittest.TestCase):
    def test_three_real_guides_change_atomically_and_preserve_structure(self):
        policy=json.loads((ROOT/"superagente/gencat-amount-policy.json").read_text(encoding="utf-8"))
        # Only a test scenario. The legal amounts in the real official
        # source stay at 650/750 EUR until a verified future change.
        old=policy["current_amounts"]
        if old!=[650,750]:
            self.skipTest("The canonical amounts have already changed; simulation fixture must be updated")
        official=(f"El importe de la prestación es de 700 euros por niño. "
                  f"Para las familias que tienen reconocido el título de familia numerosa o monoparental, "
                  f"en relación con el hijo que da lugar a solicitar la prestación, el importe es de 800 euros. "
                  +" ".join(sync.REQUIRED_SCOPE))
        h=sha256(official.encode()).hexdigest()
        report={"results":[{"url":sync.SOURCE_URL,"status":"changed_needs_review","sha256":h}]}
        snapshot={"snapshots":[{"url":sync.SOURCE_URL,"text":official,"sha256":h,
                                "captured_on":date.today().isoformat()}]}
        with TemporaryDirectory() as td:
            root=Path(td)
            (root/"superagente").mkdir()
            for path in sync.PAGES:
                target=root/path
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/path,target)
            result=sync.propose(root,policy,report,snapshot,date.today())
            self.assertEqual(len(result["changes"]),3)
            written=sync.apply(root,result,True)
            self.assertEqual(written["changed_pages"],3)
            self.assertEqual(json.loads((root/"superagente/gencat-amount-policy.json").read_text())["current_amounts"],[700,800])
            for file in sync.PAGES:
                page=(root/file).read_text(encoding="utf-8")
                self.assertIn("700",page)
                self.assertIn("800",page)
                sync.guard_factual_page((ROOT/file).read_text(encoding="utf-8"),page,file)
            self.assertEqual(policy["current_amounts"],[650,750])
            self.assertEqual(json.loads((ROOT/"superagente/gencat-amount-policy.json").read_text())["current_amounts"],[650,750])
if __name__=="__main__":unittest.main()
