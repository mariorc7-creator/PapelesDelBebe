#!/usr/bin/env python3
"""Create immutable-snapshot research dossiers for the selected editorial batch.

Read-only, offline discovery. A cited URL is a candidate, NEVER verified law.
No editorial receipts, legal findings, review dates or website pages are modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from superagente_review_receipts import REQUIRED_TOPICS

def dossiers(batch, references, routes, root):
    if not isinstance(batch, dict) or batch.get("publication_allowed") is not False:
        raise ValueError("non-publishable batch required")
    tasks = batch.get("batch")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("nonempty batch required")
    if not isinstance(references, dict) or not isinstance(references.get("references"), list):
        raise ValueError("candidate references required")
    if not isinstance(routes, dict) or not isinstance(routes.get("routes"), list):
        raise ValueError("source routing required")
    roots = Path(root).resolve()
    route_map, ref_map = {}, {}
    for r in routes["routes"]:
        page = r.get("page") if isinstance(r, dict) else None
        if not isinstance(page, str) or page in route_map:
            raise ValueError("invalid or duplicate routing entry")
        route_map[page] = r
    for r in references["references"]:
        page = r.get("page") if isinstance(r, dict) else None
        if not isinstance(page, str) or page in ref_map:
            raise ValueError("invalid or duplicate reference")
        ref_map[page] = r
    out, seen = [], set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("invalid task")
        url = task.get("page")
        if not isinstance(url, str) or url in seen:
            raise ValueError("invalid or duplicate batch URL")
        seen.add(url)
        u = urlsplit(url)
        if (u.scheme != "https" or u.hostname != "www.papelesdelbebe.es"
            or u.username or u.password or u.query or u.fragment or not u.path.endswith("/")):
            raise ValueError("unsupported page URL")
        target = (roots / u.path.lstrip("/") / "index.html").resolve()
        if roots not in target.parents or not target.is_file():
            raise ValueError("missing or unsafe source page")
        raw = target.read_bytes()
        route = route_map.get(url)
        candidate = ref_map.get(url)
        if candidate and (not route or candidate.get("authority") != route.get("authority")
                          or candidate.get("status") != "candidate_needs_document_review"):
            raise ValueError("reference does not match routed authority")
        proposed = candidate.get("source_url") if candidate else None
        if proposed:
            src = urlsplit(proposed)
            if (src.scheme != "https" or src.hostname != candidate.get("approved_host")
                or src.username or src.password or src.fragment or src.port not in (None, 443)
                or src.path in ("", "/")):
                raise ValueError("invalid candidate source URL")
        out.append({
            "page": url,
            "priority": task.get("priority"),
            "task_state": task.get("state"),
            "page_sha256": hashlib.sha256(raw).hexdigest(),
            "page_bytes": len(raw),
            "authority": route.get("authority") if route else None,
            "jurisdiction": route.get("jurisdiction") if route else None,
            "candidate_source_url": proposed,
            "source_status": "unverified_candidate" if proposed else "source_needed",
            "evidence_slots": {topic: {"state": "not_evaluated", "excerpt": None,
                                       "source_sha256": None, "applicability_checked": False}
                               for topic in REQUIRED_TOPICS},
            "next_action": ("inspect_primary_source_and_collect_excerpts" if proposed
                            else "identify_primary_authority_and_exact_source"),
            "document_reviewed": False, "editorial_signoff": False,
            "review_date_update_allowed": False, "publication_allowed": False
        })
    return {"schema_version": 1, "batch_size": len(out), "dossiers": out,
            "source_claims_verified": 0, "pages_reviewed": 0,
            "warning": "Dossiers are research templates, not official evidence, approvals or verified updates."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--output", type=Path, default=Path("superagente/v03-evidence-dossiers.json"))
    args = p.parse_args()
    root = args.root.resolve()
    def read(name):
        return json.loads((root / "superagente" / name).read_text(encoding="utf-8"))
    report = dossiers(read("v03-editorial-batch.json"), read("official-document-candidates.json"),
                      read("source-routing.json"), root)
    dest = args.output if args.output.is_absolute() else root / args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Evidence dossiers: {len(report['dossiers'])} prepared; 0 verified legal claims; no site writes")
if __name__ == "__main__":
    main()
