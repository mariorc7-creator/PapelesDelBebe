#!/usr/bin/env python3
"""Fetch and fingerprint explicitly allowlisted official source pages.

Changes in fingerprints are alerts, NOT evidence that a legal requirement changed.
No automatic editorial update, review date change or deployment.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
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

def capture_official(item, baseline):
    """Independent bounded TLS request, safe to execute in a small worker pool."""
    url=item["url"]
    parsed=urlparse(url)
    host=parsed.hostname or ""
    allowed=item.get("approved_host")
    if (parsed.scheme!="https" or host!=allowed or parsed.username or parsed.password
            or parsed.port not in (None,443) or parsed.fragment):
        return {"url":url,"status":"blocked_invalid_host"},None
    try:
        ips=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        if not ips or not all(ipaddress.ip_address(a[4][0]).is_global for a in ips):
            raise ValueError("non-public host")
        # A separate opener per request prevents shared mutable handler state.
        opener=urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),NoRedirect())
        req=urllib.request.Request(url,headers={
            "User-Agent":"PapelesDelBebe-EditorialWatch/1.0",
            "Accept":"text/html"},method="GET")
        with opener.open(req,timeout=15) as response:
            if response.geturl()!=url:raise ValueError("unexpected final URL")
            if "text/html" not in response.headers.get("Content-Type",""):
                raise ValueError("non-html content")
            raw=response.read(1_000_001)
            if len(raw)>1_000_000:raise ValueError("page too large")
            charset=response.headers.get_content_charset() or "utf-8"
        extractor=Extractor()
        extractor.feed(raw.decode(charset,errors="replace"))
        rendered=" ".join(" ".join(extractor.text).split())
        if not rendered:raise ValueError("empty source")
        digest=hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        previous=baseline.get(url)
        status=("baseline_missing" if previous is None else
                "changed_needs_review" if previous!=digest else "unchanged")
        result={"url":url,"status":status,"sha256":digest,
                "characters":len(rendered),"topics":item.get("topics",[])}
        snapshot={"url":url,"sha256":digest,"text":rendered,
                  "captured_on":datetime.now(timezone.utc).date().isoformat(),
                  "verified_legal_facts":False}
        return result,snapshot
    except Exception as exc:
        return {"url":url,"status":"fetch_failed","error":type(exc).__name__},None

def run(watchlist,baseline,fetch=capture_official,max_workers=4):
    sources=watchlist.get("sources") if isinstance(watchlist,dict) else None
    if not isinstance(sources,list) or not sources:
        raise ValueError("Nonempty official source list required")
    urls=[entry.get("url") for entry in sources if isinstance(entry,dict)]
    if len(urls)!=len(sources) or len(set(urls))!=len(urls):
        raise ValueError("Invalid or duplicated official URLs")
    if not isinstance(baseline,dict):
        raise ValueError("Invalid baseline")
    if not isinstance(max_workers,int) or not 1<=max_workers<=4:
        raise ValueError("Workers must be between 1 and 4")
    # map preserves the watchlist's published ordering even if responses race.
    with ThreadPoolExecutor(max_workers=min(max_workers,len(sources))) as pool:
        checked=list(pool.map(lambda item:fetch(item,baseline),sources))
    entries=[result for result,_ in checked]
    snapshots=[snapshot for _,snapshot in checked if snapshot is not None]
    return entries,snapshots

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--baseline",type=Path,default=ROOT/"superagente/official-baseline.json")
    parser.add_argument("--workers",type=int,default=4)
    args=parser.parse_args()
    watchlist=json.loads(SOURCES.read_text(encoding="utf-8"))
    baseline=json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline.exists() else {}
    start=perf_counter()
    entries,snapshots=run(watchlist,baseline,max_workers=args.workers)
    OUT.write_text(json.dumps({
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "warning":"Source fingerprints are not legal verification. Changed pages require independent review.",
        "results":entries
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"superagente/official-text-snapshots.json").write_text(
        json.dumps({"schema_version":1,"snapshots":snapshots,
                    "warning":"Public official HTML text, not legal proof."},
                   ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Official source watch:",
          {state:sum(x["status"]==state for x in entries) for state in sorted({x["status"] for x in entries})},
          f"elapsed={perf_counter()-start:.2f}s; workers={min(args.workers,len(entries))}")
if __name__=="__main__":main()
