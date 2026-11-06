#!/usr/bin/env python3
"""Attach only exact, integrity-checked manual captures to editorial dossiers.

Generates a read-only research manifest. Does not transform captures into
editorial receipts, legal verification, dated reviews, or publishable changes.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

def link(dossiers, watchlist, capture_report):
    pages = dossiers.get("dossiers") if isinstance(dossiers, dict) else None
    sources = watchlist.get("sources") if isinstance(watchlist, dict) else None
    captures = capture_report.get("captures") if isinstance(capture_report, dict) else None
    failures = capture_report.get("failures") if isinstance(capture_report, dict) else None
    if not isinstance(pages, list) or not isinstance(sources, list) or not isinstance(captures, list) or not isinstance(failures, list):
        raise ValueError("invalid capture handoff input")
    known = {}
    for item in sources:
        if not isinstance(item, dict) or not isinstance(item.get("url"), str) or item["url"] in known:
            raise ValueError("invalid or duplicate allowlisted source")
        u = urlsplit(item["url"])
        if (u.scheme != "https" or u.hostname != item.get("approved_host") or
                u.username or u.password or u.fragment or u.port not in (None, 443)
                or u.path in ("", "/")):
            raise ValueError("unsafe source allowlist")
        known[item["url"]] = item
    indexed = {}
    for capture in captures:
        if not isinstance(capture, dict) or not isinstance(capture.get("source_url"), str):
            raise ValueError("invalid capture")
        url = capture["source_url"]
        if url in indexed or url not in known:
            raise ValueError("duplicate or unapproved capture URL")
        text = capture.get("text")
        if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > 1000000:
            raise ValueError("invalid capture text")
        if capture.get("sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
            raise ValueError("invalid capture digest")
        if capture.get("source_provenance_verified") is not False:
            raise ValueError("capture must be explicitly unverified")
        if capture.get("fetch_method") != "https_pinned_public_ip_tls_hostname_no_redirect":
            raise ValueError("capture must use pinned HTTPS mechanism")
        indexed[url] = capture
    if any(not isinstance(f, dict) or f.get("url") not in known for f in failures):
        raise ValueError("unrecognized capture failure")
    output, seen = [], set()
    for dossier in pages:
        if not isinstance(dossier, dict) or not isinstance(dossier.get("page"), str):
            raise ValueError("invalid dossier")
        page = dossier["page"]
        if page in seen:
            raise ValueError("duplicate dossier page")
        seen.add(page)
        url = next((item["url"] for item in sources if item.get("page") == page), None)
        if url is not None and dossier.get("candidate_source_url") not in (None, url):
            # A research candidate might be a landing page rather than the exact application page.
            # It is still never silently re-approved or treated as an exact match.
            status = "candidate_url_differs_from_capture"
        elif url is None:
            status = "no_exact_source_selected"
        elif url in indexed:
            status = "capture_integrity_checked_needs_review"
        elif any(f["url"] == url for f in failures):
            status = "capture_failed"
        else:
            status = "capture_not_executed"
        output.append({
            "page": page, "page_sha256": dossier.get("page_sha256"), "exact_capture_url": url,
            "capture_status": status,
            "capture_text_sha256": indexed[url]["sha256"] if url in indexed else None,
            "captured_at_utc": indexed[url].get("captured_at_utc") if url in indexed else None,
            "verified_facts": 0, "editorial_approval": False, "review_date_update": False,
            "publication_allowed": False
        })
    return {
        "schema_version": 1, "total": len(output),
        "integrity_checked": sum(x["capture_status"]=="capture_integrity_checked_needs_review" for x in output),
        "results": output, "publication_allowed": False,
        "warning": "Raw captures and exact URLs require independent source, legal, and applicability review."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dossiers",type=Path,default=Path("superagente/v03-evidence-dossiers.json"))
    p.add_argument("--watchlist",type=Path,default=Path("superagente/official-watchlist.json"))
    p.add_argument("--captured",type=Path,default=Path("superagente/source-capture-report.json"))
    p.add_argument("--output",type=Path,default=Path("superagente/v03-capture-handoff.json"))
    args=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8"))
    raw=read(args.captured) if args.captured.is_file() else {"captures":[],"failures":[]}
    result=link(read(args.dossiers),read(args.watchlist),raw)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Source handoff: %s dossiers, %s integrity-checked captures (no legal verification)"%
          (result["total"],result["integrity_checked"]))
if __name__=="__main__":
    main()
