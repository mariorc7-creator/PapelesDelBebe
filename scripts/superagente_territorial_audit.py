#!/usr/bin/env python3
"""Read-only editorial link checks. Not a legal or ranking validator."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

class MainLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.position = 0
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.active = True
        if self.active and tag == "a":
            href = dict(attrs).get("href", "")
            parts = urlsplit(href)
            if not parts.netloc and parts.path.startswith("/"):
                self.links.append((parts.path.rstrip("/") + "/", self.position))
    def handle_endtag(self, tag):
        if tag == "main":
            self.active = False
    def handle_data(self, data):
        if self.active:
            self.position += len(data.split())

def page(root, slug):
    if not re.fullmatch(r"[a-z0-9-]+(?:/[a-z0-9-]+)*", slug):
        raise ValueError("Invalid route")
    parser = MainLinks()
    parser.feed((root / slug / "index.html").read_text(encoding="utf-8"))
    return parser

def audit(root, policy):
    if policy.get("schema_version") != 1 or policy.get("publication_allowed") is not False:
        raise ValueError("Read-only policy required")
    if not (root / policy["editorial_standard"]).is_file():
        raise ValueError("Editorial standard missing")
    rows = []
    aliases = policy.get("public_aliases", {})
    for territory, spokes in policy["territories"].items():
        hub = "comunidades/" + territory
        h = page(root, hub)
        for spoke in spokes:
            target = "/" + aliases.get(spoke, spoke) + "/"
            forward = any(link == target for link, _ in h.links)
            try:
                s = page(root, spoke)
                positions = [pos for link, pos in s.links if link == "/" + hub + "/"]
                back = bool(positions)
                early = back and min(positions) <= s.position / 3
                error = None
            except FileNotFoundError:
                back = early = False
                error = "missing_source"
            rows.append(dict(hub=hub, spoke=spoke, public_target=target,
                             forward=forward, return_link=back, early_return=early, error=error))
    return dict(mode="read_only", publication_allowed=False, legal_verified=False,
                checked=len(rows), issues=[r for r in rows if not all(
                    (r["forward"], r["return_link"], r["early_return"]))], pairs=rows)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--strict", action="store_true")
    a = p.parse_args()
    policy = json.loads((a.root / "superagente/territorial-editorial-policy.json").read_text(encoding="utf-8"))
    report = audit(a.root, policy)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Territorial audit: {report['checked']} pairs, {len(report['issues'])} issues; read only")
    if a.strict and report["issues"]:
        raise SystemExit(1)
if __name__ == "__main__":
    main()
