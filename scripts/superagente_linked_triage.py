#!/usr/bin/env python3
"""Match source-attested claims to a fresh page inventory; never edit HTML.

The input is a list of candidate comparisons, not independent legal verification.
"""
import argparse
import json
from pathlib import Path
from superagente_semantic_triage import assess

def reconcile(inventory, comparisons, today=None):
    pages = inventory.get("pages", []) if isinstance(inventory, dict) else []
    claims = comparisons.get("claims", []) if isinstance(comparisons, dict) else []
    if not isinstance(pages, list) or not isinstance(claims, list) or not claims:
        raise ValueError("invalid or empty inventory/comparisons")
    indexed = {}
    ambiguous = set()
    for page in pages:
        if not isinstance(page, dict):
            continue
        for item in page.get("claims", []):
            if not isinstance(item, dict):
                continue
            key = (page.get("url"), item.get("claim_id"))
            if key in indexed:
                ambiguous.add(key)
            indexed[key] = item
    seen = set()
    results = []
    for record in claims:
        if not isinstance(record, dict):
            results.append({"status": "blocked", "errors": ["invalid:record"], "publishable": False})
            continue
        key = (record.get("page"), record.get("claim_id"))
        errors = []
        if key in seen:
            errors.append("duplicate:comparison")
        seen.add(key)
        if key in ambiguous:
            errors.append("ambiguous:claim")
        current = indexed.get(key)
        if current is None:
            errors.append("missing:inventory_claim")
        else:
            if record.get("paragraph_sha256") != current.get("paragraph_sha256"):
                errors.append("stale:paragraph")
            if record.get("published_value") != current.get("published_value"):
                errors.append("stale:published_value")
            if record.get("kind") != current.get("kind"):
                errors.append("mismatch:kind")
        evaluated = assess(record, today=today)
        errors.extend(evaluated.get("errors", []))
        if errors:
            results.append({"page": record.get("page"), "claim_id": record.get("claim_id"),
                            "status": "blocked", "errors": sorted(set(errors)), "publishable": False})
        else:
            results.append({**evaluated, "paragraph_sha256": current["paragraph_sha256"],
                            "selector_hint": current.get("selector_hint"),
                            "warning": "Unverified editorial triage; requires substantive review."})
    counts = {status: sum(r["status"] == status for r in results)
              for status in ("blocked", "difference_needs_review", "text_matches_needs_review")}
    return {"schema_version": 1, "counts": counts, "results": results,
            "warning": "No legal validity inferred; all results non-publishable."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--comparisons", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("superagente/linked-triage-report.json"))
    args = parser.parse_args()
    result = reconcile(json.loads(args.inventory.read_text(encoding="utf-8")),
                       json.loads(args.comparisons.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"]))
    raise SystemExit(1 if result["counts"]["blocked"] else 0)

if __name__ == "__main__":
    main()
