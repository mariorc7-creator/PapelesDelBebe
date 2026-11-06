#!/usr/bin/env python3
"""Read-only quality gate for Papeles del Bebé. No claims of official review."""
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
OUT = ROOT / "superagente" / "audit-report.json"

def main():
    root = ET.parse(SITEMAP).getroot()
    urls = [n.text.strip() for n in root.findall(".//{*}loc") if n.text]
    problems = []
    seen = set()
    pages = []
    for url in urls:
        path = urlparse(url).path
        if url in seen:
            problems.append({"type": "duplicate_sitemap_url", "url": url})
        seen.add(url)
        target = ROOT / path.lstrip("/") / "index.html" if path != "/" else ROOT / "index.html"
        if not target.is_file():
            problems.append({"type": "missing_local_page", "url": url, "expected": str(target.relative_to(ROOT))})
            continue
        html = target.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"<title\b[^>]*>\s*[^<\s]", html, re.I):
            problems.append({"type": "missing_title", "url": url})
        if not re.search(r'<meta\s+[^>]*name=["\']description["\']', html, re.I):
            problems.append({"type": "missing_description", "url": url})
        if not re.search(r'<meta\s+[^>]*name=["\']viewport["\']', html, re.I):
            problems.append({"type": "missing_viewport", "url": url})
        pages.append({"url": url, "file": str(target.relative_to(ROOT)), "review_status": "not_verified"})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"total_sitemap_urls": len(urls), "local_pages_found": len(pages), "pages": pages, "issues": problems}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Checked {len(urls)} URLs; {len(problems)} issues. Report: {OUT.relative_to(ROOT)}")
    for issue in problems[:40]:
        print(f" - {issue['type']}: {issue['url']}")
    return 1 if any(x["type"] in ("missing_local_page", "duplicate_sitemap_url") for x in problems) else 0

if __name__ == "__main__":
    sys.exit(main())
