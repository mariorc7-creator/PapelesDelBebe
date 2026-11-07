#!/usr/bin/env python3
"""Generate review proposals for human/verified-agent approval; never edit site."""
import argparse
import difflib
import json
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "superagente/reviews.json"
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--proposed-file", required=True, type=Path)
    p.add_argument("--source", action="append", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--output", type=Path, default=ROOT / "superagente/content-proposal.json")
    args = p.parse_args()
    allowed = {x.text.strip() for x in ET.parse(ROOT / "sitemap.xml").getroot().findall(".//{*}loc") if x.text}
    if args.url not in allowed: p.error("URL not listed in sitemap")
    u = urlparse(args.url)
    target = ROOT / u.path.lstrip("/") / "index.html" if u.path != "/" else ROOT / "index.html"
    if not target.is_file(): p.error("Original HTML not found")
    proposed = args.proposed_file.resolve()
    if not proposed.is_file(): p.error("Proposed file missing")
    old = target.read_text(encoding="utf-8")
    new = proposed.read_text(encoding="utf-8")
    if old == new: p.error("No change detected")
    if not args.reason.strip(): p.error("Reason required")
    for source in args.source:
        if urlparse(source).scheme != "https": p.error("HTTPS source required")
    diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile=str(target.relative_to(ROOT)), tofile="proposed", lineterm=""))
    data = {
        "status": "requires_review", "url": args.url, "original_file": str(target.relative_to(ROOT)),
        "sources": args.source, "reason": args.reason, "diff": diff,
        "checks_required": ["official_source_verification", "seo_geo", "mobile_ux", "visual_regression", "editorial_approval"]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Proposal generated with {len(diff)} diff lines; site unchanged.")
if __name__ == "__main__": main()
