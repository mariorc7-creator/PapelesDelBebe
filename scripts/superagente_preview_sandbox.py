#!/usr/bin/env python3
"""Build a throwaway static-site preview for visual QA; never edit checkout HTML."""
import argparse
import json
import shutil
from pathlib import Path
from superagente_editorial_preview import build

IGNORED = shutil.ignore_patterns(".git", "node_modules", "mobile-artifacts*", "__pycache__", "*.pyc")

def stage(root, manifest, sandbox):
    root = Path(root).resolve()
    sandbox = Path(sandbox).resolve()
    if sandbox == root or root in sandbox.parents or sandbox in root.parents:
        raise ValueError("sandbox must be separate from source checkout")
    report = build(root, manifest)
    if sandbox.exists():
        raise ValueError("sandbox exists; refusing overwrite")
    shutil.copytree(root, sandbox, ignore=IGNORED)
    for item in manifest["changes"]:
        target = sandbox / item["path"]
        content = target.read_text(encoding="utf-8")
        if content.count(item["search"]) != 1:
            raise ValueError("stale sandbox anchor")
        target.write_text(content.replace(item["search"], item["replacement"], 1), encoding="utf-8")
    return {"sandbox": str(sandbox), "files": [i["path"] for i in manifest["changes"]],
            "source_unchanged": True, "publishable": False, "report": report}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path, default=Path("superagente/proposals/editorial-2026-11-06-first-five.json"))
    parser.add_argument("--sandbox-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    source = args.manifest if args.manifest.is_absolute() else root / args.manifest
    result = stage(root, json.loads(source.read_text(encoding="utf-8")), args.sandbox_root)
    print(f"Created disposable mobile preview: {len(result['files'])} proposed pages, checkout unchanged")

if __name__ == "__main__":
    main()
