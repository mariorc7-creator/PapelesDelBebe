#!/usr/bin/env python3
"""Fail closed on unapproved official-source hosts in comparison submissions.

This checks source provenance policy, NOT source content or legal validity.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

def approved_hosts(watchlist):
    if not isinstance(watchlist, dict) or not isinstance(watchlist.get("sources"), list):
        raise ValueError("missing or malformed official-source watchlist")
    hosts = set()
    for item in watchlist["sources"]:
        if not isinstance(item, dict):
            raise ValueError("malformed watchlist item")
        url = item.get("url")
        approved = item.get("approved_host")
        if not isinstance(url, str) or not isinstance(approved, str):
            raise ValueError("source URL and approved host required")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname != approved
                or parsed.username or parsed.password or parsed.port not in (None, 443)):
            raise ValueError("watchlist host mismatch")
        hosts.add(approved)
    if not hosts:
        raise ValueError("empty approved host set")
    return hosts

def validate(comparisons, hosts):
    claims = comparisons.get("claims") if isinstance(comparisons, dict) else None
    if not isinstance(claims, list) or not claims:
        raise ValueError("nonempty comparisons claims required")
    results = []
    for i, claim in enumerate(claims):
        errors = []
        if not isinstance(claim, dict):
            errors.append("invalid:claim")
            source_url = None
        else:
            source_url = claim.get("source_url")
            if not isinstance(source_url, str):
                errors.append("missing:source_url")
            else:
                try:
                    source = urlsplit(source_url)
                    if (source.scheme != "https" or source.hostname not in hosts or source.username
                            or source.password or source.port not in (None, 443)):
                        errors.append("unapproved:source_host")
                except ValueError:
                    errors.append("invalid:source_url")
        results.append({"index": i, "status": "blocked" if errors else "source_host_allowed",
                        "errors": errors, "publishable": False})
    return {"schema_version": 1, "results": results, "blocked": sum(r["status"] == "blocked" for r in results),
            "warning": "Host allowlisting is NOT documentary or legal verification; publication remains blocked."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--comparisons", type=Path, required=True)
    p.add_argument("--watchlist", type=Path, default=Path("superagente/official-watchlist.json"))
    p.add_argument("--output", type=Path, default=Path("superagente/source-provenance-report.json"))
    args = p.parse_args()
    hosts = approved_hosts(json.loads(args.watchlist.read_text(encoding="utf-8")))
    result = validate(json.loads(args.comparisons.read_text(encoding="utf-8")), hosts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Source provenance: {len(result['results'])} checked; {result['blocked']} blocked")
    raise SystemExit(1 if result["blocked"] else 0)

if __name__ == "__main__":
    main()
