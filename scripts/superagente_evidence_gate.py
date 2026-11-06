#!/usr/bin/env python3
"""Fail-closed validation of editorial evidence. Never modifies published pages."""
import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED = ("page", "claim", "jurisdiction", "source_url", "source_title",
            "consulted_on", "effective_on", "evidence_excerpt", "verdict", "reviewer")
VERDICTS = {"coincide", "difiere", "no_verificable"}
def validate(record):
    errors = []
    for field in REQUIRED:
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"missing:{field}")
    if record.get("verdict") not in VERDICTS:
        errors.append("invalid:verdict")
    url = urlsplit(str(record.get("source_url", "")))
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        errors.append("invalid:source_url")
    for field in ("consulted_on", "effective_on"):
        try:
            date.fromisoformat(record[field])
        except (KeyError, ValueError, TypeError):
            errors.append(f"invalid:{field}")
    if record.get("verdict") == "difiere" and not str(record.get("proposed_correction", "")).strip():
        errors.append("missing:proposed_correction")
    if record.get("verdict") == "no_verificable" and record.get("approved_for_publication"):
        errors.append("blocked:unverified_publication")
    if record.get("approved_for_publication") and record.get("verdict") != "difiere":
        errors.append("blocked:publication_requires_diff")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path, help="JSON file containing a records array")
    args = parser.parse_args()
    payload = json.loads(args.evidence.read_text(encoding="utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list) or not records:
        parser.error("nonempty records array required")
    problems = [{"index": i, "errors": validate(r)} for i, r in enumerate(records) if not isinstance(r, dict) or validate(r)]
    print(json.dumps({"checked": len(records), "problems": problems}, ensure_ascii=False))
    raise SystemExit(1 if problems else 0)

if __name__ == "__main__":
    main()
