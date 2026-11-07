#!/usr/bin/env python3
"""Map official-source changes to website update tasks, without fabricated facts.

Consumes capture/watch reports and exact watchlist page mappings. A changed
fingerprint signals a RESEARCH TASK only; it does not certify an aid revision.
The output can become a reviewed updater manifest after independent fact check.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

def make_tasks(watchlist, watch_report, site_host="www.papelesdelbebe.es"):
    sources=watchlist.get("sources")
    results=watch_report.get("results")
    if not isinstance(sources,list) or not isinstance(results,list):
        raise ValueError("Sources/results missing")
    mapping={}
    for source in sources:
        url=source.get("url")
        target=source.get("page")
        if not isinstance(url,str) or url in mapping or not isinstance(target,str):
            raise ValueError("Invalid or duplicate watch source")
        p=urlsplit(target)
        if p.scheme!="https" or p.netloc!=site_host or not p.path.startswith("/") or ".." in p.path:
            raise ValueError("Page mapping outside website")
        mapping[url]=source
    seen=set()
    tasks=[]
    for item in results:
        url=item.get("url")
        if url not in mapping or url in seen:
            raise ValueError("Report contains unmapped or duplicate official source")
        seen.add(url)
        source=mapping[url]
        state=item.get("status")
        if state not in ("unchanged","changed_needs_review","baseline_missing","fetch_failed","blocked_invalid_host"):
            raise ValueError("Unknown watch status")
        if state=="unchanged":
            # Fingerprint equality alone is NOT a legal review, so no date change.
            continue
        tasks.append({
            "source_url":url,
            "page":source["page"],
            "topics":source.get("topics",[]),
            "detected_state":state,
            "next_step": "independent_semantic_comparison" if state=="changed_needs_review" else
                ("establish_verified_baseline" if state=="baseline_missing" else "repair_capture"),
            "reviewed_claims":False,
            "may_change_html":False,
            "may_change_review_date":False,
            "automatic_publication":False,
        })
    if seen!=set(mapping):
        raise ValueError("Missing official source report entries")
    tasks.sort(key=lambda t:(0 if t["detected_state"]=="changed_needs_review" else 1,t["page"],t["source_url"]))
    return {"schema_version":1,"mode":"source_change_triage",
            "tasks":tasks,"publication_allowed":False,
            "warning":"A fingerprint change does not establish which legal facts changed. Independent verification required."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--watchlist",type=Path,default=Path("superagente/official-watchlist.json"))
    p.add_argument("--watch-report",type=Path,default=Path("superagente/official-watch-report.json"))
    p.add_argument("--output",type=Path,default=Path("superagente/official-content-tasks.json"))
    a=p.parse_args()
    result=make_tasks(json.loads(a.watchlist.read_text(encoding="utf-8")),json.loads(a.watch_report.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{len(result['tasks'])} official source research tasks; 0 unverified website updates")
if __name__=="__main__":
    main()
