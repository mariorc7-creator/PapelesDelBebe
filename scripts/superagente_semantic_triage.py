#!/usr/bin/env python3
"""Prepare deterministic editorial triage from explicitly paired claims.

This is NOT legal or semantic verification. No site files are edited.
Inputs must be independently sourced and reviewed.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

KINDS = {"amount", "deadline", "requirement", "document", "procedure", "eligibility"}
def normalize(value):
    return re.sub(r"\s+", " ", str(value).strip()).casefold()

def assess(record, today=None):
    today = today or date.today()
    errors = []
    if not isinstance(record, dict):
        return {"status": "blocked", "errors": ["invalid:record"]}
    required = ("page", "claim_id", "kind", "published_value", "official_value",
                "source_url", "source_excerpt", "consulted_on", "effective_on",
                "jurisdiction", "reviewer")
    errors += ["missing:" + key for key in required
               if not isinstance(record.get(key), str) or not record[key].strip()]
    if record.get("kind") not in KINDS:
        errors.append("invalid:kind")
    try:
        url = urlsplit(record.get("source_url", ""))
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.port not in (None, 443):
            errors.append("invalid:source_url")
    except (TypeError, ValueError):
        errors.append("invalid:source_url")
    try:
        checked = date.fromisoformat(record["consulted_on"])
        effective = date.fromisoformat(record["effective_on"])
        if checked > today:
            errors.append("future:consulted_on")
        if effective > today:
            errors.append("future:effective_on")
    except (KeyError, TypeError, ValueError):
        errors.append("invalid:dates")
    if errors:
        return {"status": "blocked", "errors": errors}
    status = "text_matches_needs_review" if normalize(record["published_value"]) == normalize(record["official_value"]) else "difference_needs_review"
    return {"status": status, "errors": [], "page": record["page"],
            "claim_id": record["claim_id"], "kind": record["kind"],
            "source_url": record["source_url"], "consulted_on": record["consulted_on"],
            "effective_on": record["effective_on"],
            "proposed_value": record["official_value"] if status == "difference_needs_review" else None,
            "requires_human_or_verified_semantic_review": True,
            "publishable": False}

def evaluate(payload, today=None):
    records = payload.get("claims") if isinstance(payload, dict) else None
    if not isinstance(records, list) or not records:
        raise ValueError("nonempty claims list required")
    results = [assess(record, today=today) for record in records]
    counts = {status: sum(x["status"] == status for x in results)
              for status in ("blocked", "difference_needs_review", "text_matches_needs_review")}
    return {"schema_version": 1, "warning": "String comparison is not legal verification. All outcomes require substantive review; nothing may publish automatically.",
            "counts": counts, "results": results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("superagente/semantic-triage-report.json"))
    args = parser.parse_args()
    report = evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"]))
    raise SystemExit(1 if report["counts"]["blocked"] else 0)

if __name__ == "__main__":
    main()
