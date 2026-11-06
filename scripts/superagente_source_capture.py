#!/usr/bin/env python3
"""Read-only HTML capture for exact, approved URLs.

Never accepts URLs supplied via an editorial claim. Host checks are a defense
in depth; DNS rebinding cannot be fully prevented with urllib's default dialer.
Captures are untrusted until the independent review confirms source provenance.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import ipaddress
import json
import socket
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPSHandler, HTTPRedirectHandler, Request

MAX_BYTES = 750_000

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect_denied")

class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skipped = []
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "template", "svg"):
            self.skipped.append(tag)
    def handle_endtag(self, tag):
        if self.skipped and tag == self.skipped[-1]:
            self.skipped.pop()
    def handle_data(self, data):
        if not self.skipped:
            self.parts.append(data)

def validate_url(entry, resolver=socket.getaddrinfo):
    if not isinstance(entry, dict):
        raise ValueError("malformed_entry")
    url = entry.get("url")
    host = entry.get("approved_host")
    if not isinstance(url, str) or not isinstance(host, str):
        raise ValueError("invalid_url_or_host")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != host
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or parsed.fragment):
        raise ValueError("url_not_allowlisted")
    addrs = resolver(host, 443, type=socket.SOCK_STREAM)
    if not addrs or not all(ipaddress.ip_address(addr[4][0]).is_global for addr in addrs):
        raise ValueError("non_public_dns")
    return url

def capture(entry, opener=None, resolver=socket.getaddrinfo, now=None):
    url = validate_url(entry, resolver)
    opener = opener or build_opener(HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
    request = Request(url, method="GET", headers={
        "User-Agent": "PapelesDelBebe-SourceCapture/0.2 (editorial research)",
        "Accept": "text/html"})
    with opener.open(request, timeout=15) as response:
        if response.geturl() != url:
            raise ValueError("unexpected_final_url")
        content_type = response.headers.get("Content-Type", "").lower()
        if not (content_type.startswith("text/html") and
                (len(content_type) == 9 or content_type[9] in (";", " "))):
            raise ValueError("invalid_content_type")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("oversize")
        charset = response.headers.get_content_charset() or "utf-8"
    text_parser = TextOnly()
    text_parser.feed(raw.decode(charset, errors="replace"))
    text = " ".join(" ".join(text_parser.parts).split())
    if not text:
        raise ValueError("empty_document")
    stamp = now or datetime.now(timezone.utc)
    return {"source_url": url, "text": text, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "captured_on": stamp.date().isoformat(), "captured_at_utc": stamp.isoformat(),
            "fetch_method": "https_html_allowlist_no_redirect", "source_provenance_verified": False}

def run(watchlist, fetch=capture):
    entries = watchlist.get("sources") if isinstance(watchlist, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ValueError("nonempty watchlist required")
    captures, failures = [], []
    for item in entries:
        try:
            captures.append(fetch(item))
        except Exception as exc:
            failures.append({"url": item.get("url") if isinstance(item, dict) else None,
                             "error": type(exc).__name__})
    return {"captures": captures, "failures": failures,
            "warning": "Downloaded HTML is not proof of legal applicability or content accuracy."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--watchlist", type=Path, default=Path("superagente/official-watchlist.json"))
    parser.add_argument("--output", type=Path, default=Path("superagente/source-capture-report.json"))
    args = parser.parse_args()
    report = run(json.loads(args.watchlist.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Captured {len(report['captures'])} sources, {len(report['failures'])} failures; no site files edited")
    raise SystemExit(1 if report["failures"] else 0)

if __name__ == "__main__":
    main()
