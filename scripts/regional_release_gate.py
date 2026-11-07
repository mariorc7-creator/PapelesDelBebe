#!/usr/bin/env python3
"""Fail-closed regional release gate for v2.5-v3.1.

Compares the 7 regional HTML pages against a pinned production baseline,
requiring actual changes, verified official-source receipts, SEO/mobility
and remote-rollback checks *before* any merge into main.
Never deploys, rewrites HTML, or accesses production.
"""
import argparse
from pathlib import Path
import json
import re
import subprocess

REGIONS = {
    "v2.5": "comunidades/cataluna/index.html",
    "v2.6": "comunidades/andalucia/index.html",
    "v2.7": "comunidades/extremadura/index.html",
    "v2.8": "comunidades/pais-vasco/index.html",
    "v2.9": "comunidades/islas-baleares/index.html",
    "v3.0": "comunidades/navarra/index.html",
    "v3.1": "comunidades/asturias/index.html",
}
NEEDED = ("verified_official_sources", "legal_status_verified", "seo_qa_passed",
          "mobile_qa_passed", "rollback_remotely_verified", "editorial_approval")

def release_readiness(changed_paths, evidence, pages_exist):
    if not isinstance(evidence, dict):
        raise ValueError("Missing evidence manifest")
    items = []
    for version, path in REGIONS.items():
        receipt = evidence.get(version, {})
        checks = {key: receipt.get(key) is True for key in NEEDED}
        items.append({
            "version": version, "path": path, "exists": path in pages_exist,
            "changed_since_base": path in changed_paths,
            "checks": checks,
            "ready": path in pages_exist and path in changed_paths and all(checks.values())
        })
    return {
        "schema_version": 1, "release": "regional-v2.5-v3.1",
        "production_deploy_allowed": all(x["ready"] for x in items),
        "versions": items, "changed_count": sum(x["changed_since_base"] for x in items),
        "ready_count": sum(x["ready"] for x in items),
        "note": "Requires independent verification of every receipt. True booleans alone do not prove the underlying evidence.",
    }

def run(base, root, manifest):
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("Pinned full base SHA required")
    changed = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", base, "HEAD", "--"],
        capture_output=True, text=True, check=True
    ).stdout.splitlines()
    pages = {p for p in REGIONS.values() if (root / p).is_file()}
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    return release_readiness(set(changed), data, pages)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = run(args.base, args.root, args.manifest)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded)
    if not result["production_deploy_allowed"]:
        raise SystemExit("BLOCKED: regional release has unverified content, QA, or rollback")

if __name__ == "__main__":
    main()
