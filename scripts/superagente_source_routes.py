#!/usr/bin/env python3
"""Generate an explicit source-discovery queue for real sitemap pages.

This does not find, approve, or verify official documents. It never edits pages.
"""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

REQUIRED = ("page", "topic", "jurisdiction", "priority", "authority", "source_status")
PRIORITIES = {"P0", "P1", "P2"}
PENDING = "needs_exact_official_document"

def validate_routes(config, sitemap_urls):
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise ValueError("invalid routing schema")
    routes = config.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ValueError("nonempty routing list required")
    seen, problems, queue = set(), [], []
    for index, route in enumerate(routes):
        errors = []
        if not isinstance(route, dict):
            problems.append({"index": index, "errors": ["invalid:route"]})
            continue
        for field in REQUIRED:
            if not isinstance(route.get(field), str) or not route[field].strip():
                errors.append("missing:" + field)
        page = route.get("page")
        if page not in sitemap_urls:
            errors.append("missing:sitemap_page")
        if page in seen:
            errors.append("duplicate:page")
        seen.add(page)
        if route.get("priority") not in PRIORITIES:
            errors.append("invalid:priority")
        if route.get("source_status") != PENDING:
            errors.append("invalid:source_status")
        # Exact URLs are intentionally absent: routing is not evidence.
        if any(field in route for field in ("source_url", "approved", "reviewed_on", "effective_on")):
            errors.append("blocked:unsupported_verification_claim")
        if errors:
            problems.append({"index": index, "errors": sorted(set(errors))})
        else:
            queue.append({**route, "action": "locate_and_review_exact_official_document",
                          "legal_verification": False, "publishable": False})
    return {"schema_version": 1, "total": len(routes),
            "accepted": len(queue), "problems": problems,
            "queue": sorted(queue, key=lambda item: (item["priority"], item["page"])),
            "warning": "Routing does not prove any source is official, current, or applicable."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sitemap", type=Path, default=Path("sitemap.xml"))
    p.add_argument("--routing", type=Path, default=Path("superagente/source-routing.json"))
    p.add_argument("--output", type=Path, default=Path("superagente/source-discovery-queue.json"))
    args = p.parse_args()
    urls = {n.text.strip() for n in ET.parse(args.sitemap).getroot().findall(".//{*}loc") if n.text}
    report = validate_routes(json.loads(args.routing.read_text(encoding="utf-8")), urls)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Source discovery routes: {report['accepted']} accepted; {len(report['problems'])} blocked")
    raise SystemExit(1 if report["problems"] else 0)

if __name__ == "__main__":
    main()
