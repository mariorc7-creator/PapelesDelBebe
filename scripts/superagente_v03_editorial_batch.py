#!/usr/bin/env python3
"""V0.3 read-only editorial batch: join workplan and review receipts.

Receipts only indicate whether a supplied record is structurally complete.
Neither a candidate reference nor a validated receipt is official approval.
Never changes website HTML, review dates, or publication permissions.
"""
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from superagente_review_receipts import evaluate

def compile_batch(workplan, receipt_report, limit=12):
    if not isinstance(workplan, dict) or not isinstance(workplan.get("items"), list):
        raise ValueError("invalid workplan")
    if not isinstance(receipt_report, dict) or not isinstance(receipt_report.get("results"), list):
        raise ValueError("invalid receipt report")
    if not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("limit must be 1..50")
    by_page = {}
    for item in receipt_report["results"]:
        page = item.get("page")
        if not isinstance(page, str) or page in by_page:
            raise ValueError("invalid or duplicate receipt report page")
        by_page[page] = item
    tasks = []
    seen = set()
    for item in workplan["items"]:
        page = item.get("url")
        if not isinstance(page, str) or page in seen:
            raise ValueError("invalid or duplicate workplan page")
        seen.add(page)
        receipt = by_page.get(page)
        if receipt is None:
            state, action = "no_receipt", item.get("action", "inventory_and_evaluate")
        elif receipt.get("status") == "blocked":
            issues = receipt.get("errors", [])
            state = "stale_snapshot" if "stale:page_hash" in issues else "receipt_invalid"
            action = "refresh_receipt_snapshot_and_sources" if state == "stale_snapshot" else "repair_receipt_evidence"
        elif receipt.get("status") == "ready_for_editorial_signoff":
            state, action = "awaiting_independent_signoff", "verify_receipt_against_primary_sources"
        else:
            raise ValueError("unknown receipt report status")
        # Keep the original editorial priority as the main sort dimension.
        # Within a priority, stale / blocked evidence should surface first.
        weight = {"stale_snapshot": 0, "receipt_invalid": 1,
                  "awaiting_independent_signoff": 2, "no_receipt": 3}[state]
        tasks.append({"page": page, "priority": item["priority"],
                      "topic": item.get("category", "otras"), "state": state,
                      "next_action": action, "last_documented_review": item.get("last_documented_review"),
                      "independently_verified": False, "changes_review_date": False,
                      "publishable": False, "_sort_weight": weight})
    unknown = set(by_page) - seen
    if unknown:
        raise ValueError("receipt refers to page outside workplan")
    tasks.sort(key=lambda t: (t["priority"], t["_sort_weight"], t["last_documented_review"] or "", t["page"]))
    for task in tasks:
        task.pop("_sort_weight")
    chosen = tasks[:limit]
    return {
        "schema_version": 1, "workplan_date": workplan.get("as_of"),
        "total_backlog": len(tasks), "batch_size": len(chosen),
        "counts": {state: sum(t["state"] == state for t in tasks) for state in
                   ("no_receipt", "receipt_invalid", "stale_snapshot", "awaiting_independent_signoff")},
        "batch": chosen, "publication_allowed": False,
        "warning": "A structurally valid receipt is not official verification or editorial approval."
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--limit", type=int, default=12)
    p.add_argument("--output", type=Path, default=Path("superagente/v03-editorial-batch.json"))
    args = p.parse_args()
    root = args.root.resolve()
    workplan = json.loads((root/"superagente/v03-review-workplan.json").read_text(encoding="utf-8"))
    receipt_file = root/"superagente/review-receipts.json"
    receipts = json.loads(receipt_file.read_text(encoding="utf-8")) if receipt_file.exists() else {
        "schema_version": 1, "receipts": []}
    urls = {e.text.strip() for e in ET.parse(root/"sitemap.xml").getroot().findall(".//{*}loc") if e.text}
    receipt_report = evaluate(receipts, urls, root)
    batch = compile_batch(workplan, receipt_report, args.limit)
    output = args.output if args.output.is_absolute() else root/args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(batch, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"V0.3 editorial batch: {batch['batch_size']} tasks, {batch['total_backlog']} in queue; no publishing")

if __name__ == "__main__":
    main()
