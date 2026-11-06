#!/usr/bin/env python3
"""Check recorded source URL health. Never equate HTTP 200 with factual review.
Only explicitly allowlisted public authority hosts can be requested.
"""
import ipaddress
import json
import socket
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
registry = ROOT / "superagente" / "reviews.json"
out = ROOT / "superagente" / "source-health.json"
# Deliberately narrow. Extend only after security review.
OFFICIAL_HOSTS = {
    "boe.es", "www.boe.es", "seg-social.es", "www.seg-social.es",
    "sede.seg-social.gob.es", "administracion.gob.es",
    "www.administracion.gob.es", "agenciatributaria.gob.es",
    "sede.agenciatributaria.gob.es", "www.agenciatributaria.es",
    "tramits.gencat.cat", "web.gencat.cat", "www.gencat.cat",
    "www.comunidad.madrid", "www.juntadeandalucia.es",
    "www.xunta.gal", "www.navarra.es", "www.euskadi.eus",
}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect_blocked")

def safe_host(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        return False
    host = (parsed.hostname or "").lower()
    if host not in OFFICIAL_HOSTS:
        return False
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        return bool(addresses) and all(ipaddress.ip_address(x[4][0]).is_global for x in addresses)
    except (OSError, ValueError):
        return False

data = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {"pages": {}}
urls = {}
for page, entry in data.get("pages", {}).items():
    for record in entry.get("history", []):
        for url in record.get("sources", []):
            urls.setdefault(url, []).append(page)
results = []
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ssl.create_default_context()), NoRedirect()
)
for url, pages in sorted(urls.items()):
    if not safe_host(url):
        results.append({"url": url, "pages": pages, "status": "blocked_unapproved_or_unsafe_host"})
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PapelesDelBebe-SourceHealth/1.0"}, method="HEAD")
        with opener.open(req, timeout=12) as response:
            status = response.status
        results.append({"url": url, "pages": pages, "http_status": status, "status": "reachable" if status < 400 else "unreachable"})
    except Exception as exc:
        results.append({"url": url, "pages": pages, "status": "unreachable_or_redirected", "error": type(exc).__name__})
out.write_text(json.dumps({
    "warning": "HTTP availability is NOT factual verification; never update review dates from this report.",
    "sources": results,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Checked {len(results)} source URLs")
