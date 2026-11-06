#!/usr/bin/env python3
"""Fetch and fingerprint explicitly allowlisted official source pages.

Changes in fingerprints are alerts, NOT evidence that a legal requirement changed.
No automatic editorial update, review date change or deployment.
"""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import ipaddress
import json
import socket
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "superagente/official-watchlist.json"
OUT = ROOT / "superagente/official-watch-report.json"
class Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"): self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.skip: self.skip -= 1
    def handle_data(self, data):
        if not self.skip: self.text.append(data)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect blocked")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=ROOT / "superagente/official-baseline.json")
    args = parser.parse_args()
    watchlist = json.loads(SOURCES.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline.exists() else {}
    entries = []
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
    for item in watchlist.get("sources", []):
        url = item["url"]
        parsed = urlparse(url)
        host = parsed.hostname or ""
        allowed = item.get("approved_host")
        if parsed.scheme != "https" or host != allowed or parsed.username or parsed.password or parsed.port not in (None, 443):
            entries.append({"url": url, "status": "blocked_invalid_host"})
            continue
        try:
            ips = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            if not ips or not all(ipaddress.ip_address(a[4][0]).is_global for a in ips):
                raise ValueError("non-public host")
            req = urllib.request.Request(url, headers={"User-Agent": "PapelesDelBebe-EditorialWatch/1.0", "Accept": "text/html"}, method="GET")
            with opener.open(req, timeout=15) as response:
                if "text/html" not in response.headers.get("Content-Type", ""):
                    raise ValueError("non-html content")
                raw = response.read(1_000_001)
                if len(raw) > 1_000_000: raise ValueError("page too large")
                charset = response.headers.get_content_charset() or "utf-8"
            extractor = Extractor()
            extractor.feed(raw.decode(charset, errors="replace"))
            text = " ".join(" ".join(extractor.text).split())
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            previous = baseline.get(url)
            status = "baseline_missing" if previous is None else ("changed_needs_review" if previous != digest else "unchanged")
            entries.append({"url": url, "status": status, "sha256": digest, "characters": len(text), "topics": item.get("topics", [])})
        except Exception as exc:
            entries.append({"url": url, "status": "fetch_failed", "error": type(exc).__name__})
    OUT.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "warning": "Source HTML fingerprints are not legal verification. Changes require manual/semantic review.", "results": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Official source watch:", {status: sum(x["status"] == status for x in entries) for status in sorted({x["status"] for x in entries})})
if __name__ == "__main__": main()
