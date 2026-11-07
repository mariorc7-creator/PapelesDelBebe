#!/usr/bin/env python3
"""Extract candidate legal facts from HTML for editorial comparison.

This script does NOT infer that an amount, deadline or requirement is correct.
Its output is a review queue, not an automatic factual update.
"""
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "amount": re.compile(r"(?<!\w)(?:\d{1,3}(?:[.\s]\d{3})*|\d+)(?:,\d{1,2})?\s*(?:€|euros?)", re.I),
    "deadline": re.compile(r"\b(?:\d{1,3}\s+(?:d[ií]as?|mes(?:es)?|semanas?|a[nñ]os?))\b", re.I),
    "year": re.compile(r"\b20(?:2[5-9]|3\d)\b"),
}
def visible_text(source):
    source = re.sub(r"(?is)<(script|style|noscript)\b[^>]*>.*?</\1>", " ", source)
    source = re.sub(r"(?s)<!--.*?-->", " ", source)
    source = re.sub(r"(?s)<[^>]*>", " ", source)
    return re.sub(r"\s+", " ", html.unescape(source)).strip()

urls = sorted({n.text.strip() for n in ET.parse(ROOT / "sitemap.xml").getroot().findall(".//{*}loc") if n.text})
results = []
for url in urls:
    path = urlparse(url).path
    if not any(term in path for term in ("ayuda", "deduccion", "bono", "permiso", "prestacion")):
        continue
    file = ROOT / path.lstrip("/") / "index.html"
    if not file.is_file():
        continue
    text = visible_text(file.read_text(encoding="utf-8", errors="replace"))
    facts = []
    for kind, pattern in PATTERNS.items():
        for match in list(pattern.finditer(text))[:25]:
            facts.append({"type": kind, "value": match.group(), "context": text[max(0, match.start()-100):match.end()+120]})
    results.append({"url": url, "file": str(file.relative_to(ROOT)), "facts_to_verify": facts,
                    "status": "requires_official_comparison"})
out = ROOT / "superagente/fact-candidates.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"warning": "Candidates are unverified and may include unrelated amounts/dates.", "pages": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Extracted unverified candidates from {len(results)} aid/benefit pages")
