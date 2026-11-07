#!/usr/bin/env python3
"""Compare a manually verified official fact against a page fact candidate.

Requires explicit evidence; outputs a proposal, never edits production content.
"""
import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--page", required=True)
    p.add_argument("--fact", required=True)
    p.add_argument("--official-value", required=True)
    p.add_argument("--official-source", required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--effective-date", required=True)
    args = p.parse_args()
    source = urlparse(args.official_source)
    if source.scheme != "https" or not source.hostname or source.username or source.password:
        p.error("HTTPS official source required")
    try:
        effective = date.fromisoformat(args.effective_date)
    except ValueError:
        p.error("effective date must be YYYY-MM-DD")
    if effective > date.today():
        p.error("future effective dates need separate scheduled review")
    if not all(x.strip() for x in (args.fact, args.official_value, args.evidence, args.reviewer)):
        p.error("nonempty fact, value, evidence and reviewer required")
    candidates_path = ROOT / "superagente/fact-candidates.json"
    if not candidates_path.is_file():
        p.error("run scripts/superagente_facts.py first")
    pages = json.loads(candidates_path.read_text(encoding="utf-8")).get("pages", [])
    page = next((x for x in pages if x["url"] == args.page), None)
    if page is None:
        p.error("page not in extracted candidates")
    matches = [x for x in page["facts_to_verify"] if x["value"] == args.fact]
    if not matches:
        p.error("fact not found in page candidates")
    status = "matches" if args.fact.strip() == args.official_value.strip() else "requires_editorial_review"
    output = {
        "status": status, "page": args.page, "published_candidate": args.fact,
        "official_value": args.official_value, "official_source": args.official_source,
        "evidence": args.evidence, "reviewer": args.reviewer,
        "effective_date": args.effective_date, "contexts": [m["context"] for m in matches[:3]],
        "warning": "Reviewer-attested comparison, not independent source verification. No site changes made."
    }
    target = ROOT / "superagente/fact-comparison.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(status)
if __name__ == "__main__": main()
