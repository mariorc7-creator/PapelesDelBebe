#!/usr/bin/env python3
"""Fail closed: connect submitted claim excerpts to exact approved source URLs.

The approved watchlist must name exact documents. Candidate references alone
are not approvals. Captures must match those exact URLs and their text hashes.
No network, page edits, review dates, or publication authorization.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

def url_is_exact_https(url, host):
    if not isinstance(url, str) or not isinstance(host, str):
        return False
    try:
        u = urlsplit(url)
        return (u.scheme == "https" and u.hostname == host and bool(u.hostname)
                and u.port in (None, 443) and not u.username and not u.password
                and not u.fragment and u.path not in ("", "/"))
    except ValueError:
        return False

def authorized(watchlist):
    sources = watchlist.get("sources") if isinstance(watchlist, dict) else None
    if not isinstance(sources, list) or not sources:
        raise ValueError("nonempty source allowlist required")
    urls = set()
    for entry in sources:
        if not isinstance(entry, dict) or not url_is_exact_https(entry.get("url"), entry.get("approved_host")):
            # Generic homepages cannot validate specific legal assertions.
            continue
        if entry["url"] in urls:
            raise ValueError("duplicate approved document")
        urls.add(entry["url"])
    return urls

def check(comparisons, captures, watchlist):
    claims = comparisons.get("claims") if isinstance(comparisons, dict) else None
    records = captures.get("captures") if isinstance(captures, dict) else None
    if not isinstance(claims, list) or not claims or not isinstance(records, list):
        raise ValueError("claims and captures required")
    allowed = authorized(watchlist)
    index = {}
    for c in records:
        if not isinstance(c, dict) or not isinstance(c.get("source_url"), str):
            raise ValueError("invalid capture")
        key = c["source_url"]
        if key in index:
            raise ValueError("duplicate captured document")
        index[key] = c
    results = []
    for i, claim in enumerate(claims):
        errors = []
        if not isinstance(claim, dict):
            results.append({"index": i, "status": "blocked", "errors": ["invalid:claim"], "publishable": False})
            continue
        url = claim.get("source_url")
        if url not in allowed:
            errors.append("unapproved:exact_document")
        record = index.get(url)
        if not record:
            errors.append("missing:matching_capture")
        else:
            text = record.get("text")
            sha = record.get("sha256")
            excerpt = claim.get("source_excerpt")
            if not isinstance(text, str) or not text.strip() or len(text) > 1_000_000:
                errors.append("invalid:capture_text")
            elif sha != hashlib.sha256(text.encode("utf-8")).hexdigest():
                errors.append("mismatch:capture_digest")
            elif not isinstance(excerpt, str) or not excerpt.strip() or " ".join(excerpt.split()) not in " ".join(text.split()):
                errors.append("missing:document_excerpt")
        results.append({"index": i, "source_url": url,
                        "status": "blocked" if errors else "exact_document_excerpt_present",
                        "errors": errors, "publishable": False, "source_provenance_verified": False})
    return {"schema_version": 1, "blocked": sum(r["status"] == "blocked" for r in results),
            "results": results,
            "warning": "Exact URL + hash + excerpt only prove consistency with supplied capture. Independent provenance and legal applicability remain unverified."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--comparisons", required=True, type=Path)
    p.add_argument("--captures", required=True, type=Path)
    p.add_argument("--watchlist", type=Path, default=Path("superagente/official-watchlist.json"))
    p.add_argument("--output", type=Path, default=Path("superagente/exact-document-report.json"))
    args = p.parse_args()
    result = check(json.loads(args.comparisons.read_text(encoding="utf-8")),
                   json.loads(args.captures.read_text(encoding="utf-8")),
                   json.loads(args.watchlist.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"Exact documentary links: {len(result['results'])} checked, {result['blocked']} blocked")
    raise SystemExit(1 if result["blocked"] else 0)
if __name__ == "__main__":
    main()
