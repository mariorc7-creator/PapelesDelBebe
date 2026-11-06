#!/usr/bin/env python3
"""Manage review evidence without inventing reviews or touching article dateModified."""
import argparse
import datetime as dt
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "superagente" / "reviews.json"
SITEMAP = ROOT / "sitemap.xml"

def urls():
    return sorted({n.text.strip() for n in ET.parse(SITEMAP).getroot().findall(".//{*}loc") if n.text})

def load():
    return json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {"schema_version": 1, "pages": {}}

def save(data):
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory")
    verify = sub.add_parser("verify")
    verify.add_argument("--url", required=True)
    verify.add_argument("--source", action="append", required=True, help="Official URL checked manually")
    verify.add_argument("--result", choices=["unchanged", "changed", "unverifiable"], required=True)
    verify.add_argument("--evidence", required=True, help="Specific finding, checked by a human or verified process")
    verify.add_argument("--reviewer", required=True)
    verify.add_argument("--date", help="ISO date; defaults to today")
    args = p.parse_args()
    data = load()
    if args.command == "inventory":
        current = urls()
        for url in current:
            data["pages"].setdefault(url, {"status": "not_verified", "last_reviewed": None, "history": []})
        data["inactive_urls"] = sorted(set(data["pages"]) - set(current))
        save(data)
        print(f"Inventory: {len(current)} sitemap URLs; {len(data['inactive_urls'])} removed from sitemap")
        return
    if args.url not in urls():
        p.error("URL not present in sitemap")
    if not args.evidence.strip() or not args.reviewer.strip():
        p.error("Evidence and reviewer are required")
    from urllib.parse import urlparse
    for source in args.source:
        u = urlparse(source)
        if u.scheme != "https" or not u.netloc:
            p.error("Sources must be HTTPS URLs")
    date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    if date > dt.date.today():
        p.error("Future review dates are forbidden")
    entry = data["pages"].setdefault(args.url, {"status": "not_verified", "last_reviewed": None, "history": []})
    record = {"date": date.isoformat(), "result": args.result, "sources": args.source, "evidence": args.evidence.strip(), "reviewer": args.reviewer.strip()}
    entry["history"].append(record)
    entry["status"] = args.result
    entry["last_reviewed"] = date.isoformat() if args.result != "unverifiable" else entry.get("last_reviewed")
    save(data)
    print(f"Evidence recorded for {args.url}; no page HTML or sitemap lastmod modified")

if __name__ == "__main__":
    main()
