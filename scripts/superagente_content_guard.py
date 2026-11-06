#!/usr/bin/env python3
"""Fail closed if site content changes without evidence/QA in the PR.
Use on content PRs; no write access.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
base = os.environ.get("BASE_REF", "origin/main")
r = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT, capture_output=True, text=True)
if r.returncode:
    print("BLOCKED: cannot calculate changed files:", r.stderr)
    sys.exit(1)
changed = [p for p in r.stdout.splitlines() if p.endswith((".html", ".htm"))]
if not changed:
    print("No HTML changed; content evidence gate not applicable")
    sys.exit(0)
manifest = ROOT / "superagente/content-approval.json"
if not manifest.exists():
    print("BLOCKED: HTML changes require superagente/content-approval.json")
    sys.exit(1)
data = json.loads(manifest.read_text(encoding="utf-8"))
approved = {p["file"] for p in data.get("approved_files", []) if p.get("official_sources") and p.get("evidence") and p.get("reviewer")}
missing = [p for p in changed if p not in approved]
if missing:
    print("BLOCKED: missing documented review for:", ", ".join(missing))
    sys.exit(1)
print("Documented content approvals present; this does not itself verify legal accuracy")
