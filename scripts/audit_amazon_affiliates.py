#!/usr/bin/env python3
"""Auditoría read-only de enlaces de afiliación. No modifica archivos."""
import argparse
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, parse_qs

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        data = dict(attrs)
        href = data.get("href", "")
        host = (urlparse(href).hostname or "").lower()
        if host == "amazon.es" or host == "www.amazon.es":
            self.links.append(data)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected-tag", default="mariorc7-21")
    ap.add_argument("--out", default="reports/amazon-affiliates-audit.json")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.run(["git", "ls-files", "*.html"], cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
    findings, total = [], 0
    for filename in tracked:
        file = root / filename
        if not file.is_file():
            continue
        html = file.read_text(encoding="utf-8", errors="replace")
        parser = Links()
        parser.feed(html)
        for attrs in parser.links:
            total += 1
            href = attrs["href"]
            params = parse_qs(urlparse(href).query)
            tag = params.get("tag", [""])[0]
            rel = set(attrs.get("rel", "").lower().split())
            if tag != args.expected_tag:
                findings.append({"file": filename, "type": "wrong_or_missing_tag", "url": href, "tag": tag})
            if "sponsored" not in rel or "nofollow" not in rel:
                findings.append({"file": filename, "type": "missing_affiliate_rel", "url": href})
            if attrs.get("target") == "_blank" and "noopener" not in rel:
                findings.append({"file": filename, "type": "missing_noopener", "url": href})
        # JS-generated links with literal Amazon URLs need manual review.
        js_urls = set(re.findall(r'https?://(?:www[.])?amazon[.]es/[^\s<>]+', html))
        for candidate in sorted(js_urls):
            url = candidate.split(chr(39))[0].split(chr(34))[0]
            total += 1
            tag = parse_qs(urlparse(url.replace("&amp;", "&")).query).get("tag", [""])[0]
            if tag != args.expected_tag:
                findings.append({"file": filename, "type": "js_url_missing_tag", "url": url})
    result = {"expected_tag": args.expected_tag, "html_files_scanned": len(tracked), "amazon_links_or_literals_found": total, "findings": findings, "note": "Static audit only; JS-generated rel attributes and URLs require runtime tests. No product availability or commission verification."}
    destination = root / args.out
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(tracked), "links": total, "findings": len(findings), "report": str(destination.relative_to(root))}, ensure_ascii=False))
    return 1 if findings else 0

if __name__ == "__main__":
    raise SystemExit(main())
