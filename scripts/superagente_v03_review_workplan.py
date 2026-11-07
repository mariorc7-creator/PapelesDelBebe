#!/usr/bin/env python3
"""Generate a review-first V0.3 editorial workplan from real sitemap and registry.

No network or write-side effects on pages, review dates or approved releases.
Source candidates do NOT count as official verification.
"""
import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

CATEGORIES = {"ayudas": 2, "tramites": 3, "herramientas": 4, "otras": 5}
LEGAL_TERMS = ("ayuda", "deduccion", "bono", "prestacion", "permiso", "familia", "natalidad")
PROCEDURE_TERMS = ("tramite", "seguridad-social", "registro-civil", "empadronar", "tarjeta-sanitaria")
CREDIBLE_RESULTS = {"unchanged", "changed"}

def category(url):
    path = urlsplit(url).path.lower()
    if any(t in path for t in LEGAL_TERMS):
        return "ayudas"
    if any(t in path for t in PROCEDURE_TERMS):
        return "tramites"
    if "herramientas" in path:
        return "herramientas"
    return "otras"

def review_status(entry, today):
    """Only explicit evidence-backed registry reviews can create a review date."""
    history = entry.get("history", []) if isinstance(entry, dict) else []
    if not isinstance(history, list):
        return None, "invalid_history"
    valid = []
    for record in history:
        if not isinstance(record, dict) or record.get("result") not in CREDIBLE_RESULTS:
            continue
        if not isinstance(record.get("reviewer"), str) or not record["reviewer"].strip():
            continue
        if not isinstance(record.get("evidence"), str) or len(record["evidence"].strip()) < 15:
            continue
        src = record.get("sources")
        if not isinstance(src, list) or not src or not all(
            isinstance(url, str) and urlsplit(url).scheme == "https"
            and urlsplit(url).hostname and not urlsplit(url).username
            and not urlsplit(url).password for url in src
        ):
            continue
        try:
            checked = date.fromisoformat(record["date"])
        except (ValueError, TypeError, KeyError):
            continue
        if checked <= today:
            valid.append((checked, record["result"]))
    if not valid:
        return None, "no_documented_review"
    latest, result = max(valid, key=lambda x: x[0])
    return latest.isoformat(), "review_recorded_" + result

def plan(urls, registry, routing, candidates, today=None):
    today = today or date.today()
    if not isinstance(urls, list) or not urls:
        raise ValueError("sitemap must contain URLs")
    if len(urls) != len(set(urls)):
        raise ValueError("duplicate sitemap URLs")
    if not isinstance(registry, dict) or not isinstance(registry.get("pages", {}), dict):
        raise ValueError("invalid review registry")
    route_items = routing.get("routes") if isinstance(routing, dict) else None
    candidate_items = candidates.get("references") if isinstance(candidates, dict) else None
    if not isinstance(route_items, list) or not isinstance(candidate_items, list):
        raise ValueError("missing routing or reference arrays")
    route_index = {r["page"]: r for r in route_items if isinstance(r, dict) and isinstance(r.get("page"), str)}
    refs = {r["page"]: r for r in candidate_items if isinstance(r, dict) and isinstance(r.get("page"), str)}
    items = []
    for url in urls:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "www.papelesdelbebe.es":
            raise ValueError("unsupported sitemap URL")
        cat = category(url)
        record = registry.get("pages", {}).get(url, {})
        reviewed, review_state = review_status(record, today)
        route = route_index.get(url)
        ref = refs.get(url)
        has_candidate = bool(ref and ref.get("status") == "candidate_needs_document_review")
        # A candidate is never an authenticated source or legal verification.
        if route and not has_candidate:
            action = "locate_specific_official_document"
        elif route:
            action = "retrieve_and_verify_official_evidence"
        elif cat in ("ayudas", "tramites"):
            action = "map_administration_and_document"
        elif reviewed:
            action = "schedule_next_audit"
        else:
            action = "inventory_and_evaluate"
        priority = 0 if route and route.get("priority") == "P0" else (
            1 if route and route.get("priority") == "P1" else CATEGORIES[cat]
        )
        items.append({
            "url": url, "category": cat, "priority": priority, "action": action,
            "review_state": review_state, "last_documented_review": reviewed,
            "days_since_review": (today - date.fromisoformat(reviewed)).days if reviewed else None,
            "official_reference_status": "candidate_unverified" if has_candidate else "none",
            "page_verified_by_this_plan": False, "update_review_date": False,
            "modify_content": False, "publishable": False
        })
    items.sort(key=lambda item: (item["priority"], item["last_documented_review"] or "", item["url"]))
    return {
        "schema_version": 1, "as_of": today.isoformat(), "pages": len(items),
        "no_documented_review": sum(i["last_documented_review"] is None for i in items),
        "candidate_references": sum(i["official_reference_status"] == "candidate_unverified" for i in items),
        "items": items, "warning": "Priority is not legal verification. Only independently corroborated audits can update review dates."
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("superagente/v03-review-workplan.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    urls = [n.text.strip() for n in ET.parse(root / "sitemap.xml").getroot().findall(".//{*}loc") if n.text]
    def load(p, default):
        f = root / p
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default
    report = plan(urls, load("superagente/reviews.json", {"pages": {}}),
                  load("superagente/source-routing.json", {"routes": []}),
                  load("superagente/official-document-candidates.json", {"references": []}))
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"V0.3 plan: {report['pages']} URLs, {report['no_documented_review']} without documented reviews")
if __name__ == "__main__":
    main()
