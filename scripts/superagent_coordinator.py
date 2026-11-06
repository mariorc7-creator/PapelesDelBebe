#!/usr/bin/env python3
"""Coordinación no destructiva de módulos del SuperAgente; sin commits ni despliegue."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "superagent-modules.json"

def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if any(config.get(key) is not False for key in
           ("deploy_enabled", "merge_enabled", "scheduled_publication_enabled")):
        raise SystemExit("ERROR: staging_only requiere desactivar deploy, merge y publicación")
    modules = {m["id"]: m for m in config["modules"]}
    if "amazon_affiliates" not in modules or "qa" not in modules:
        raise SystemExit("ERROR: módulos Amazon y QA obligatorios")
    if any(m.get("writes_to_production") is not False for m in config["modules"]):
        raise SystemExit("ERROR: ningún módulo puede escribir en producción")
    cmd = [sys.executable, str(ROOT / modules["amazon_affiliates"]["script"]),
           "--expected-tag", modules["amazon_affiliates"]["expected_tag"]]
    audit = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    source = ROOT / "reports" / "amazon-affiliates-audit.json"
    report = json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}
    status = {
        "agent": config["agent"],
        "environment": config["environment"],
        "production_untouched": True,
        "amazon_audit_exit_code": audit.returncode,
        "amazon_findings": len(report.get("findings", [])),
        "gates": {k: ("pass" if k == "affiliate_link_audit" and audit.returncode == 0
                      else "needs_review" if k != "affiliate_link_audit"
                      else "fail") for k in config["qa_gates"]},
        "eligible_for_merge": False,
        "eligible_for_deploy": False,
        "modules": [{"id": m["id"], "stage": m["stage"]} for m in config["modules"]],
        "notes": "La auditoría no equivale a una revisión visual móvil ni a una validación comercial."
    }
    destination = ROOT / config["coordination"]["report_path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report":str(destination.relative_to(ROOT)), "affiliate_findings":status["amazon_findings"],"deploy":False},ensure_ascii=False))
    return 1 if audit.returncode != 0 else 0

if __name__ == "__main__":
    raise SystemExit(main())
