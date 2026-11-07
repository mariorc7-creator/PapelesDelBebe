#!/usr/bin/env python3
"""Evaluate editorial review receipts without updating web pages or review dates.

A receipt is proof that a reviewer supplied evidence, NOT independent legal
validation. It only becomes 'ready_for_editorial_signoff' when each required
dimension and an exact page snapshot are documented.
"""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

REQUIRED_TOPICS = ("eligibility", "amount", "deadline", "documents", "procedure",
                   "compatibility", "official_link")
RESULTS = {"unchanged", "change_proposed", "unverifiable"}

def https_url(url):
    try:
        parsed = urlsplit(url)
        return (isinstance(url, str) and parsed.scheme == "https"
                and bool(parsed.hostname) and not parsed.username
                and not parsed.password and parsed.port in (None, 443)
                and not parsed.fragment)
    except (TypeError, ValueError):
        return False

def evaluate(receipts, pages, root, today=None):
    today = today or date.today()
    if not isinstance(receipts, dict) or receipts.get("schema_version") != 1:
        raise ValueError("invalid review receipt schema")
    entries = receipts.get("receipts")
    if not isinstance(entries, list):
        raise ValueError("receipts array required")
    results, seen = [], set()
    for i, entry in enumerate(entries):
        errors = []
        if not isinstance(entry, dict):
            results.append({"index": i, "status": "blocked", "errors": ["invalid:receipt"]})
            continue
        page = entry.get("page")
        if not https_url(page) or page not in pages or urlsplit(page).hostname != "www.papelesdelbebe.es":
            errors.append("invalid:page")
        if page in seen:
            errors.append("duplicate:page")
        seen.add(page)
        reviewer = entry.get("reviewer")
        if not isinstance(reviewer, str) or len(reviewer.strip()) < 3:
            errors.append("missing:reviewer")
        try:
            when = date.fromisoformat(entry["reviewed_on"])
            if when > today: errors.append("invalid:future_review")
        except (KeyError, TypeError, ValueError):
            errors.append("invalid:review_date")
        if entry.get("result") not in RESULTS:
            errors.append("invalid:result")
        path = urlsplit(page).path if isinstance(page, str) and https_url(page) else None
        target = (Path(root) / (path or "").lstrip("/") / "index.html").resolve() if path else None
        if target is None or not target.is_file() or Path(root).resolve() not in target.parents:
            errors.append("missing:page_file")
        elif entry.get("page_sha256") != hashlib.sha256(target.read_bytes()).hexdigest():
            errors.append("stale:page_hash")
        checks = entry.get("checks")
        if not isinstance(checks, dict) or set(checks) != set(REQUIRED_TOPICS):
            errors.append("missing:complete_topic_coverage")
        else:
            for topic in REQUIRED_TOPICS:
                check = checks[topic]
                if not isinstance(check, dict):
                    errors.append("invalid:topic_" + topic)
                    continue
                if check.get("finding") not in ("confirmed", "difference", "not_applicable", "unverifiable"):
                    errors.append("invalid:topic_" + topic)
                if not isinstance(check.get("reason"), str) or len(check["reason"].strip()) < 20:
                    errors.append("missing:reason_" + topic)
                if check.get("finding") != "unverifiable" and not https_url(check.get("source_url")):
                    errors.append("missing:source_" + topic)
            findings = [x.get("finding") for x in checks.values() if isinstance(x, dict)]
            if entry.get("result") == "unchanged" and ("difference" in findings or "unverifiable" in findings):
                errors.append("inconsistent:unchanged")
            if entry.get("result") == "change_proposed" and "difference" not in findings:
                errors.append("inconsistent:change_proposed")
            if entry.get("result") != "unverifiable" and "unverifiable" in findings:
                errors.append("inconsistent:unverifiable")
        results.append({"index": i, "page": page, "status": "blocked" if errors else "ready_for_editorial_signoff",
                        "errors": sorted(set(errors)), "modifies_html": False,
                        "changes_review_date": False, "publishable": False})
    return {"schema_version": 1, "total": len(entries), "blocked": sum(r["status"]=="blocked" for r in results),
            "results": results, "warning": "Receipts are reviewer-supplied; no independent legal verification or automatic date changes."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--receipts", type=Path, default=Path("superagente/review-receipts.json"))
    parser.add_argument("--output", type=Path, default=Path("superagente/review-receipt-report.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    source = args.receipts if args.receipts.is_absolute() else root / args.receipts
    urls = {n.text.strip() for n in ET.parse(root / "sitemap.xml").getroot().findall(".//{*}loc") if n.text}
    report = evaluate(json.loads(source.read_text(encoding="utf-8")), urls, root)
    destination = args.output if args.output.is_absolute() else root / args.output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Receipts: {report['total']} submitted, {report['blocked']} blocked; no page changes")
    raise SystemExit(1 if report["blocked"] else 0)

if __name__ == "__main__":
    main()
