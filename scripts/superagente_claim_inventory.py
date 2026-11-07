#!/usr/bin/env python3
"""Inventory candidate factual assertions with exact HTML locations.

Read-only. A detected number is NOT automatically a legal fact.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

PATTERNS = {
    "amount": re.compile(r"(?<!\w)\d[\d. ]*(?:,\d{1,2})?\s*(?:€|euros?)(?!\w)", re.I),
    "deadline": re.compile(r"\b\d{1,3}\s+(?:d[ií]as?|mes(?:es)?|semanas?|a[nñ]os?)\b", re.I),
}

class Segments(HTMLParser):
    BLOCKS = {"p", "li", "td", "th", "h1", "h2", "h3", "h4"}
    SKIP = {"script", "style", "noscript", "svg", "template"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.segments, self.stack, self.skip = [], [], 0
        self.indices = {}
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if self.skip or tag not in self.BLOCKS:
            return
        index = self.indices.get(tag, 0) + 1
        self.indices[tag] = index
        self.stack.append({"selector": f"{tag}:nth-of-type({index})", "text": []})
    def handle_data(self, data):
        if not self.skip and self.stack:
            self.stack[-1]["text"].append(data)
    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
            return
        if self.skip or tag not in self.BLOCKS or not self.stack:
            return
        # Nested inline text is collected into the current block.
        block = self.stack.pop()
        text = " ".join(" ".join(block["text"]).split())
        if text:
            self.segments.append({**block, "text": text})
        if self.stack:
            self.stack[-1]["text"].append(text)

def extract(root, sitemap):
    root = Path(root).resolve()
    urls = [x.text.strip() for x in ET.parse(sitemap).getroot().findall(".//{*}loc") if x.text]
    pages = []
    for url in sorted(set(urls)):
        path = urlsplit(url).path
        if not any(term in path.lower() for term in ("ayuda", "deduccion", "bono", "permiso", "prestacion", "tramite")):
            continue
        target = (root / path.lstrip("/") / "index.html").resolve()
        if root not in target.parents or not target.is_file():
            continue
        parser = Segments()
        parser.feed(target.read_text(encoding="utf-8", errors="replace"))
        claims = []
        for segment in parser.segments:
            for kind, regex in PATTERNS.items():
                for match in regex.finditer(segment["text"]):
                    key = f"{url}|{segment['selector']}|{kind}|{match.group()}"
                    claims.append({
                        "claim_id": hashlib.sha256(key.encode("utf-8")).hexdigest()[:20],
                        "kind": kind, "published_value": match.group(),
                        "selector_hint": segment["selector"], "paragraph_text": segment["text"],
                        "paragraph_sha256": hashlib.sha256(segment["text"].encode("utf-8")).hexdigest(),
                        "verification": "pending_official_source"
                    })
        pages.append({"url": url, "file": str(target.relative_to(root)), "claims": claims})
    return {"schema_version": 1, "warning": "Heuristic candidates; selector hints are not guaranteed CSS selectors. No official verification or publication.", "pages": pages}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("superagente/claim-inventory.json"))
    args = parser.parse_args()
    report = extract(args.root, args.root / "sitemap.xml")
    out = args.output if args.output.is_absolute() else args.root / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Inventoried {len(report['pages'])} pages and {sum(len(p['claims']) for p in report['pages'])} candidates; no published files edited")

if __name__ == "__main__":
    main()
