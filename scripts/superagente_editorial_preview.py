#!/usr/bin/env python3
"""Generate text-only proposal diffs, never mutate source HTML or authorize release."""
import argparse
import difflib
import json
from pathlib import Path

REQUIRED = ("path", "url", "search", "replacement", "finding", "source_urls")

def build(root, manifest):
    if not isinstance(manifest, dict) or manifest.get("status") != "proposal_not_approved" or manifest.get("publication_allowed") is not False:
        raise ValueError("manifest must remain unapproved and non-publishable")
    changes = manifest.get("changes")
    if not isinstance(changes, list) or not changes:
        raise ValueError("nonempty changes required")
    root = Path(root).resolve()
    reports, paths = [], set()
    for item in changes:
        if not isinstance(item, dict) or any(not item.get(k) for k in REQUIRED):
            raise ValueError("missing fields in proposed change")
        rel = Path(item["path"])
        target = (root / rel).resolve()
        if (rel.is_absolute() or ".." in rel.parts or root not in target.parents
                or target.suffix.lower() != ".html" or not target.is_file()):
            raise ValueError("invalid page path")
        if item["path"] in paths:
            raise ValueError("duplicate page proposal")
        paths.add(item["path"])
        if (not isinstance(item["source_urls"], list) or not item["source_urls"]
                or not all(isinstance(url, str) and url.startswith("https://") for url in item["source_urls"])):
            raise ValueError("official source URLs required")
        if not isinstance(item["search"], str) or not isinstance(item["replacement"], str):
            raise ValueError("invalid replacement")
        if item["search"] == item["replacement"]:
            raise ValueError("no change")
        original = target.read_text(encoding="utf-8")
        if original.count(item["search"]) != 1:
            raise ValueError(f"anchor not unique or stale: {item['path']}")
        changed = original.replace(item["search"], item["replacement"], 1)
        diff = "".join(difflib.unified_diff(
            original.splitlines(keepends=True), changed.splitlines(keepends=True),
            fromfile="a/" + item["path"], tofile="b/" + item["path"]))
        reports.append({"path": item["path"], "finding": item["finding"],
                        "unified_diff": diff, "original_bytes": len(original.encode("utf-8")),
                        "proposed_bytes": len(changed.encode("utf-8")), "publishable": False})
    return {"status": "review_required", "publication_allowed": False, "diffs": reports,
            "warning": "Proposed text-only edits; HTML files, dateModified and review dates remain unchanged."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--manifest", type=Path, default=Path("superagente/proposals/editorial-2026-11-06-first-five.json"))
    p.add_argument("--output", type=Path, default=Path("superagente/proposals/preview-diffs.json"))
    args = p.parse_args()
    root = args.root.resolve()
    source = args.manifest if args.manifest.is_absolute() else root / args.manifest
    report = build(root, json.loads(source.read_text(encoding="utf-8")))
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(report['diffs'])} review-only diffs; live HTML unchanged")

if __name__ == "__main__":
    main()
