#!/usr/bin/env python3
"""Read-only exact-URL HTML capture with pinned public IP and TLS hostname check.

No proxies, redirects, DNS re-resolution during dialing or autonomous publishing.
A successful fetch is NOT proof of legal applicability or semantic correctness.
"""
import argparse
import hashlib
from html.parser import HTMLParser
from http.client import HTTPSConnection
import ipaddress
import json
import socket
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES = 750_000
TIMEOUT_SECONDS = 15

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

def validated_target(entry, resolver=socket.getaddrinfo):
    if not isinstance(entry, dict):
        raise ValueError("malformed_entry")
    url = entry.get("url")
    host = entry.get("approved_host")
    if not isinstance(url, str) or not isinstance(host, str):
        raise ValueError("invalid_url_or_host")
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname != host or parsed.hostname is None
                or parsed.username or parsed.password or parsed.port not in (None, 443)
                or parsed.fragment or parsed.path in ("", "/") and entry.get("require_document_path", False)):
            raise ValueError("url_not_allowlisted")
    except ValueError as exc:
        raise ValueError("url_not_allowlisted") from exc
    answers = resolver(host, 443, type=socket.SOCK_STREAM)
    if not answers:
        raise ValueError("empty_dns")
    ips = []
    for address in answers:
        try:
            ip = ipaddress.ip_address(address[4][0])
        except (IndexError, ValueError, TypeError):
            raise ValueError("invalid_dns_answer") from None
        if not ip.is_global:
            raise ValueError("non_public_dns")
        ips.append(str(ip))
    # Selecting a validated IP and dialing that literal IP avoids DNS TOCTOU.
    return url, host, ips[0], parsed.path or "/", parsed.query

def validate_url(entry, resolver=socket.getaddrinfo):
    return validated_target(entry, resolver)[0]

class PinnedHTTPSConnection(HTTPSConnection):
    def __init__(self, hostname, pinned_ip, timeout=TIMEOUT_SECONDS, context=None):
        super().__init__(hostname, port=443, timeout=timeout,
                         context=context or ssl.create_default_context())
        self.pinned_ip = pinned_ip
    def connect(self):
        raw = socket.create_connection((self.pinned_ip, 443), self.timeout)
        try:
            # Certificate authentication + SNI MUST use the official DNS name.
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise

def read_pinned(entry, resolver=socket.getaddrinfo, connection_factory=PinnedHTTPSConnection):
    url, host, ip, path, query = validated_target(entry, resolver)
    conn = connection_factory(host, ip, timeout=TIMEOUT_SECONDS)
    try:
        target = path + (("?" + query) if query else "")
        conn.request("GET", target, headers={
            "Host": host,
            "User-Agent": "PapelesDelBebe-SourceCapture/0.3 (editorial research)",
            "Accept": "text/html",
            "Accept-Encoding": "identity",
            "Connection": "close",
        })
        response = conn.getresponse()
        status = response.status
        if status != 200:  # 3xx is deliberately blocked, never followed.
            raise ValueError(f"unexpected_http_status_{status}")
        content_type = response.getheader("Content-Type", "").lower()
        if not (content_type.startswith("text/html") and
                (len(content_type) == 9 or content_type[9] in (";", " "))):
            raise ValueError("invalid_content_type")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("oversize")
        from email.message import Message
        headers = Message()
        headers["Content-Type"] = content_type
        charset = headers.get_content_charset() or "utf-8"
        return raw, charset, ip
    finally:
        conn.close()

def capture(entry, opener=None, resolver=socket.getaddrinfo, now=None, connection_factory=PinnedHTTPSConnection):
    # 'opener' is retained ONLY for existing hermetic unit tests. Production
    # always uses a pinned TCP dialer + TLS certificate check.
    if opener is None:
        raw, charset, _ip = read_pinned(entry, resolver, connection_factory)
        url = entry["url"]
    else:
        from urllib.request import Request
        url = validate_url(entry, resolver)
        request = Request(url, method="GET", headers={"Accept": "text/html"})
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
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
    parser = TextOnly()
    parser.feed(raw.decode(charset, errors="replace"))
    text = " ".join(" ".join(parser.parts).split())
    if not text:
        raise ValueError("empty_document")
    stamp = now or datetime.now(timezone.utc)
    return {"source_url": url, "text": text,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "captured_on": stamp.date().isoformat(),
            "captured_at_utc": stamp.isoformat(),
            "fetch_method": "https_pinned_public_ip_tls_hostname_no_redirect",
            "source_provenance_verified": False}

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
                             "error": type(exc).__name__,
                             "reason": str(exc) if isinstance(exc, ValueError) and (
                                 str(exc).startswith("unexpected_http_status_") or
                                 str(exc) in {"invalid_content_type", "oversize", "empty_document",
                                              "non_public_dns", "url_not_allowlisted", "empty_dns"}
                             ) else "capture_failure"})
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
