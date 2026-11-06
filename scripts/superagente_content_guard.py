#!/usr/bin/env python3
"""Require evidence for changed HTML; evidence is not proof of legal accuracy."""
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

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
try:
    data = json.loads(manifest.read_text(encoding="utf-8"))
except (ValueError, OSError) as exc:
    print("BLOCKED: invalid approval manifest:", exc)
    sys.exit(1)
approved = set()
for item in data.get("approved_files", []):
    sources = item.get("official_sources", [])
    if not isinstance(sources, list) or not sources or not all(
        isinstance(u, str) and urlparse(u).scheme == "https" and urlparse(u).hostname
        for u in sources
    ):
        continue
    if not all(isinstance(item.get(k), str) and item[k].strip() for k in ("file", "evidence", "reviewer", "reviewed_at")):
        continue
    if item.get("reviewed_at", "")[:4].isdigit() and len(item["reviewed_at"]) >= 10:
        approved.add(item["file"])
missing = [p for p in changed if p not in approved]
if missing:
    print("BLOCKED: missing documented review for:", ", ".join(missing))
    sys.exit(1)
print("Documented approvals present; independent factual/visual validation still required")
