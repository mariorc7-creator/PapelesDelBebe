#!/usr/bin/env python3
"""Validate a proposed release manifest. This does NOT deploy or rollback."""
import json
import sys
from pathlib import Path
from datetime import date

manifest = Path(sys.argv[1] if len(sys.argv) > 1 else "superagente/release-candidate.json")
if not manifest.is_file():
    print("BLOCKED: release candidate manifest missing")
    sys.exit(1)
data = json.loads(manifest.read_text(encoding="utf-8"))
required = ["version", "base_commit", "candidate_commit", "changes", "qa", "rollback"]
missing = [k for k in required if not data.get(k)]
if missing:
    print("BLOCKED: missing " + ", ".join(missing))
    sys.exit(1)
qa = data["qa"]
checks = ["sitemap", "mobile", "functional", "seo", "official_sources", "visual_review"]
failed = [c for c in checks if qa.get(c) != "passed"]
if failed:
    print("BLOCKED: incomplete quality checks: " + ", ".join(failed))
    sys.exit(1)
rollback = data["rollback"]
if not rollback.get("previous_stable_deployment") or rollback.get("tested") is not True:
    print("BLOCKED: rollback not tested or stable deployment missing")
    sys.exit(1)
if data.get("risk") == "high" and not data.get("human_approval"):
    print("BLOCKED: high-risk release requires approval")
    sys.exit(1)
print("Manifest policy passed; deployment still requires separate authorized action.")
