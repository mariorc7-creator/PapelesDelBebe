#!/usr/bin/env python3
"""Validate source-backed editorial evidence without altering site content."""
import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED = ("page", "claim", "jurisdiction", "source_url", "source_title",
            "consulted_on", "effective_on", "evidence_excerpt", "verdict", "reviewer")
VERDICTS = {"coincide", "difiere", "no_verificable"}

def validate(record):
    if not isinstance(record, dict):
        return ["invalid:record"]
    errors = []
    for field in REQUIRED:
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"missing:{field}")
    if record.get("verdict") not in VERDICTS:
        errors.append("invalid:verdict")
    try:
        url = urlsplit(record.get("source_url", ""))
        if (url.scheme != "https" or not url.hostname or url.username
                or url.password or url.port not in (None, 443)
                or url.hostname in ("localhost", "127.0.0.1")):
            errors.append("invalid:source_url")
    except (ValueError, TypeError):
        errors.append("invalid:source_url")
    for field in ("consulted_on", "effective_on"):
        try:
            value = date.fromisoformat(record[field])
            if field == "consulted_on" and value > date.today():
                errors.append("future:consulted_on")
        except (KeyError, ValueError, TypeError):
            errors.append(f"invalid:{field}")
    if record.get("verdict") == "difiere" and not str(record.get("proposed_correction", "")).strip():
        errors.append("missing:proposed_correction")
    if record.get("approved_for_publication") is True:
        # Evidence approval alone is never a deployment authorization.
        errors.append("blocked:publication_approval_not_supported")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path, help="JSON containing records array")
    args = parser.parse_args()
    payload = json.loads(args.evidence.read_text(encoding="utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list) or not records:
        parser.error("nonempty records array required")
    problems = []
    for i, record in enumerate(records):
        errors = validate(record)
        if errors:
            problems.append({"index": i, "errors": errors})
    print(json.dumps({"checked": len(records), "problems": problems}, ensure_ascii=False))
    raise SystemExit(1 if problems else 0)

if __name__ == "__main__":
    main()
