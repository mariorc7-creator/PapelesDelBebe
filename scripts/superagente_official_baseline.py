#!/usr/bin/env python3
"""Create or compare a *proposed* immutable fingerprint baseline for official sources.

A first successful capture establishes a candidate baseline; it does not mean
the legal facts on that page were reviewed. Never silently overwrite an
existing fingerprint after a change or use a failed capture as a baseline.
Commit approved baseline separately so subsequent manual watchdog runs can
compare documents. No publication or website content updates.
"""
import argparse
import json
from pathlib import Path
import re

def candidate_baseline(watchlist, report, old=None):
    items=watchlist.get("sources") if isinstance(watchlist,dict) else None
    results=report.get("results") if isinstance(report,dict) else None
    if not isinstance(items,list) or not isinstance(results,list):
        raise ValueError("Invalid inputs")
    old=old if old is not None else {}
    if not isinstance(old,dict):
        raise ValueError("Invalid stored baseline")
    urls=[item.get("url") for item in items]
    if len(set(urls))!=len(urls) or any(not isinstance(x,str) or not x.startswith("https://") for x in urls):
        raise ValueError("Invalid watchlist URL")
    if set(old)-set(urls):
        raise ValueError("Baseline has unmapped official source URLs")
    mapped={x["url"]:x for x in results if isinstance(x,dict) and isinstance(x.get("url"),str)}
    if len(mapped)!=len(results) or set(mapped)!=set(urls):
        raise ValueError("Report must contain every source exactly once")
    proposed=dict(old)
    pending=[]
    for url in urls:
        item=mapped[url]; status=item.get("status"); sha=item.get("sha256")
        if status in ("baseline_missing","unchanged","changed_needs_review"):
            if not isinstance(sha,str) or not re.fullmatch("[0-9a-f]{64}",sha):
                raise ValueError("Invalid content hash")
        if url in old:
            if status=="changed_needs_review" and sha!=old[url]:
                pending.append({"url":url,"state":"change_detected_do_not_rebaseline","previous_sha256":old[url],"new_sha256":sha})
            elif status=="unchanged" and sha!=old[url]:
                raise ValueError("Unchanged status inconsistent with baseline")
            elif status=="baseline_missing":
                raise ValueError("Baseline status inconsistent with old data")
            elif status in ("fetch_failed","blocked_invalid_host"):
                pending.append({"url":url,"state":"capture_failed_preserve_baseline"})
        else:
            if status=="baseline_missing":
                proposed[url]=sha
                pending.append({"url":url,"state":"candidate_initial_fingerprint_no_legal_review"})
            elif status in ("fetch_failed","blocked_invalid_host"):
                pending.append({"url":url,"state":"capture_failed_cannot_bootstrap"})
            else:
                raise ValueError("Unexpected status for new URL")
    return {
        "schema_version":1,"baseline_candidate":proposed,
        "pending":pending,"publication_allowed":False,
        "requires_manual_commit":True,
        "warning":"A source fingerprint is not legal proof. Never automatically replace a changed baseline."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--watchlist",type=Path,default=Path("superagente/official-watchlist.json"))
    p.add_argument("--report",type=Path,default=Path("superagente/official-watch-report.json"))
    p.add_argument("--baseline",type=Path,default=Path("superagente/official-baseline.json"))
    p.add_argument("--output",type=Path,default=Path("superagente/official-baseline-candidate.json"))
    a=p.parse_args()
    old=json.loads(a.baseline.read_text(encoding="utf-8")) if a.baseline.exists() else {}
    result=candidate_baseline(
        json.loads(a.watchlist.read_text(encoding="utf-8")),
        json.loads(a.report.read_text(encoding="utf-8")),old)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Baseline candidate: {len(result['baseline_candidate'])} hashes; {len(result['pending'])} follow-ups; no publication")
if __name__=="__main__":
    main()
