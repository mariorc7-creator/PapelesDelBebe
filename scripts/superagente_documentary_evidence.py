#!/usr/bin/env python3
"""Check documentary excerpts against supplied, integrity-checked text captures.

No network access. A matching excerpt proves inclusion in the supplied text only.
It does NOT prove independent retrieval, legal validity or applicability.
"""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

def norm(value):
    return re.sub(r"\s+", " ", value).strip()

def check(comparisons, captures):
    claims = comparisons.get("claims") if isinstance(comparisons, dict) else None
    records = captures.get("captures") if isinstance(captures, dict) else None
    if not isinstance(claims, list) or not claims or not isinstance(records, list):
        raise ValueError("nonempty claims and captures required")
    indexed, duplicated = {}, set()
    for capture in records:
        if not isinstance(capture, dict):
            continue
        key = capture.get("source_url")
        if not isinstance(key, str):
            continue
        if key in indexed:
            duplicated.add(key)
        indexed[key] = capture
    results = []
    for i, claim in enumerate(claims):
        errors = []
        if not isinstance(claim, dict):
            results.append({"index": i, "status": "blocked", "errors": ["invalid:claim"], "publishable": False})
            continue
        source_url = claim.get("source_url")
        capture = indexed.get(source_url)
        if source_url in duplicated:
            errors.append("duplicate:capture")
        if capture is None:
            errors.append("missing:capture")
        else:
            content = capture.get("text")
            digest = capture.get("sha256")
            excerpt = claim.get("source_excerpt")
            if not isinstance(content, str) or not content.strip() or len(content) > 1_000_000:
                errors.append("invalid:capture_text")
            else:
                expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
                if not isinstance(digest, str) or digest != expected:
                    errors.append("mismatch:capture_hash")
                if not isinstance(excerpt, str) or not excerpt.strip() or norm(excerpt) not in norm(content):
                    errors.append("missing:excerpt_in_capture")
            try:
                captured_on = date.fromisoformat(capture["captured_on"])
                consulted_on = date.fromisoformat(claim["consulted_on"])
                if captured_on > date.today() or consulted_on > date.today():
                    errors.append("future:capture_or_consultation")
                if consulted_on < captured_on:
                    errors.append("stale:consultation_before_capture")
            except (KeyError, ValueError, TypeError):
                errors.append("invalid:capture_dates")
        results.append({"index": i, "source_url": source_url,
                        "status": "blocked" if errors else "excerpt_present_in_supplied_capture",
                        "errors": sorted(set(errors)), "publishable": False})
    return {"schema_version": 1, "blocked": sum(x["status"] == "blocked" for x in results),
            "results": results,
            "warning": "Capture provenance not independently attested. Do not infer legal validity or authorize publication."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--comparisons", required=True, type=Path)
    p.add_argument("--captures", required=True, type=Path)
    p.add_argument("--output", type=Path, default=Path("superagente/documentary-evidence-report.json"))
    args = p.parse_args()
    result = check(json.loads(args.comparisons.read_text(encoding="utf-8")),
                   json.loads(args.captures.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Documentary excerpts: {len(result['results'])} checked, {result['blocked']} blocked")
    raise SystemExit(1 if result["blocked"] else 0)

if __name__ == "__main__":
    main()
