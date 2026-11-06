#!/usr/bin/env python3
"""Check availability of recorded official sources; NEVER claim factual verification."""
import json
import ssl
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
registry = ROOT / "superagente" / "reviews.json"
out = ROOT / "superagente" / "source-health.json"
data = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {"pages": {}}
urls = {}
for page, entry in data.get("pages", {}).items():
    for record in entry.get("history", []):
        for url in record.get("sources", []):
            urls.setdefault(url, []).append(page)
results = []
for url, pages in sorted(urls.items()):
    host = urlparse(url).hostname or ""
    if urlparse(url).scheme != "https" or not host or host in ("localhost",) or host.endswith((".local", ".internal")):
        results.append({"url": url, "status": "blocked_invalid_url"})
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PapelesDelBebe-SourceHealth/1.0"}, method="GET")
        with urllib.request.urlopen(req, timeout=12, context=ssl.create_default_context()) as response:
            status = response.status
            final_url = response.url
        results.append({"url": url, "pages": pages, "http_status": status, "final_url": final_url, "status": "reachable" if status < 400 else "unreachable"})
    except Exception as exc:
        results.append({"url": url, "pages": pages, "status": "unreachable", "error": type(exc).__name__})
out.write_text(json.dumps({"warning": "HTTP availability is NOT official factual verification. Never update reviewed dates from this report.", "sources": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Checked {len(results)} recorded source links; report: {out}")
