#!/usr/bin/env python3
"""Read-only Amazon affiliate link audit for Papeles del Bebé.

No HTTP requests, publishing, HTML rewrites, pricing, or dates of review.
Outputs findings for an editorial queue instead of mutating indexed content.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qs

SEARCH_URL = re.compile(r"https?://(?:www\.)?amazon\.es/[^\s'\"<>]+", re.I)
JS_AFFILIATE = re.compile(r"\baffiliate\s*:\s*(['\"])(https?://[^'\"<>]+)\1", re.I)
ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "venv", "node_modules", "dist", "coverage", ".next"}

class AnchorReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attributes = dict(attrs)
            self.links.append(attributes)

def check_amazon_url(url, *, affiliate_id=None):
    findings = []
    try:
        parsed = urlsplit(url)
    except ValueError:
        return ["invalid_url"]
    if parsed.scheme != "https":
        findings.append("non_https")
    if parsed.hostname not in ("amazon.es", "www.amazon.es"):
        findings.append("unapproved_destination")
    tags = parse_qs(parsed.query).get("tag", [])
    if len(tags) != 1 or not tags[0].strip():
        findings.append("missing_affiliate_tag")
    elif affiliate_id and tags[0] != affiliate_id:
        findings.append("unexpected_affiliate_tag")
    return findings

def audit_html(page, relative_path):
    html = page.read_text(encoding="utf-8")
    parser = AnchorReader()
    parser.feed(html)
    records = []
    links = [(a.get("href", ""), a.get("rel", ""), "html_anchor") for a in parser.links]
    links.extend((m.group(2), "", "js_affiliate") for m in JS_AFFILIATE.finditer(html))
    amazon = [(url, rel, source) for url, rel, source in links if "amazon." in url.lower()]
    tags = []
    for url, _rel, _source in amazon:
        try:
            tags.extend(parse_qs(urlsplit(url).query).get("tag", []))
        except ValueError:
            pass
    canonical_tag = max(set(tags), key=lambda t:(tags.count(t), t)) if tags else None
    disclosure_present = bool(re.search(r"(afiliad[oa]|enlace publicitario|enlaces? de afiliaci[oó]n)", html, re.I))
    for url, rel, source in amazon:
        issues = check_amazon_url(url, affiliate_id=canonical_tag)
        if source == "html_anchor":
            flags = set(rel.lower().split()) if isinstance(rel, str) else set(rel)
            if not {"sponsored", "nofollow"} & flags:
                issues.append("missing_sponsored_or_nofollow")
        if not disclosure_present:
            issues.append("no_affiliate_disclosure_found")
        records.append({"url": url, "source": source, "issues": sorted(set(issues))})
    return {"page": relative_path, "link_count": len(amazon), "tag_values": sorted(set(tags)), "disclosure_found": disclosure_present, "links": records}

def scan(root):
    pages = []
    for page in sorted(root.rglob("*.html")):
        if any(part in EXCLUDED for part in page.relative_to(root).parts):
            continue
        result = audit_html(page, page.relative_to(root).as_posix())
        if result["link_count"]:
            pages.append(result)
    issues = [
        {"page": page["page"], "url": link["url"], "source": link["source"], "issues": link["issues"]}
        for page in pages for link in page["links"] if link["issues"]
    ]
    return {"schema_version": 1, "mode": "read_only", "pages_with_amazon_links": len(pages),
            "total_amazon_links": sum(page["link_count"] for page in pages),
            "issue_count": len(issues), "issues": issues, "pages": pages,
            "publication_allowed": False, "automatic_rewrites": False,
            "note": "Static checks only: does not confirm Amazon approval, sales, program rules or live destinations."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-issues", action="store_true")
    args = parser.parse_args()
    report = scan(args.root)
    serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized)
    if args.fail_on_issues and report["issue_count"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
