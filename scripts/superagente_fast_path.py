#!/usr/bin/env python3
"""SuperAgente fast path: only expensive semantic checks on changed sources.

Inputs are the result of a fresh official HTTPS watch. This tool does NOT
cache or skip official network checks; it skips downstream semantic work for
unchanged, missing-baseline, or failed sources. All such states remain visible.
No editing, auto approval, publication or date changes.
"""
import argparse
import json
from pathlib import Path
from time import perf_counter

STATES={"changed_needs_review","unchanged","baseline_missing","fetch_failed","blocked_invalid_host"}
def plan(watchlist,watch_report,snapshots):
    sources=watchlist.get("sources") if isinstance(watchlist,dict) else None
    results=watch_report.get("results") if isinstance(watch_report,dict) else None
    captures=snapshots.get("snapshots") if isinstance(snapshots,dict) else None
    if not isinstance(sources,list) or not sources or not isinstance(results,list) or not isinstance(captures,list):
        raise ValueError("Source list, report and captures required")
    def mapping(rows,key):
        out={}
        for item in rows:
            if not isinstance(item,dict) or not isinstance(item.get(key),str) or not item[key] or item[key] in out:
                raise ValueError("Duplicate/missing source identity")
            out[item[key]]=item
        return out
    src=mapping(sources,"url")
    rep=mapping(results,"url")
    snap=mapping(captures,"url")
    if set(src)!=set(rep) or not set(snap).issubset(src):
        raise ValueError("Watchlist / report / snapshot identities disagree")
    for url,item in rep.items():
        status=item.get("status")
        if status not in STATES:
            raise ValueError("Unknown official source status")
        if status in ("changed_needs_review","unchanged","baseline_missing"):
            if status=="baseline_missing" and url not in snap:
                raise ValueError("Fresh baseline has no captured source")
            if status in ("changed_needs_review","unchanged") and url not in snap:
                raise ValueError("Comparable source requires a fresh capture")
            if item.get("sha256")!=snap[url].get("sha256"):
                raise ValueError("Captured source hash and watch report disagree")
    changed=[u for u in src if rep[u]["status"]=="changed_needs_review"]
    selected=set(changed)
    filtered_sources=[item for item in sources if item["url"] in selected]
    filtered_report=[item for item in results if item["url"] in selected]
    filtered_snapshots=[item for item in captures if item["url"] in selected]
    states={state:sum(1 for item in results if item["status"]==state) for state in sorted(STATES)}
    return {
        "schema_version":1,
        "mode":"changed_sources_only",
        "source_count":len(sources),
        "changed_count":len(changed),
        "expensive_review_skipped":len(changed)==0,
        "states":states,
        "changed_urls":changed,
        "followup_required":[{"url":url,"status":rep[url]["status"]} for url in src
            if rep[url]["status"] in ("baseline_missing","fetch_failed","blocked_invalid_host")],
        "filtered":{
            "watchlist":{"sources":filtered_sources},
            "report":{"results":filtered_report},
            "snapshots":{"snapshots":filtered_snapshots}
        },
        "website_edited":False,
        "auto_publish_allowed":False,
        "warning":"Skipping an unchanged fingerprint does not certify legal currency, change review dates, or justify publication."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--watchlist",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    p.add_argument("--github-output",type=Path)
    a=p.parse_args()
    start=perf_counter()
    def read(path):return json.loads(path.read_text(encoding="utf-8"))
    result=plan(read(a.watchlist),read(a.report),read(a.snapshots))
    a.out_dir.mkdir(parents=True,exist_ok=True)
    for name,data in (
        ("fast-path-summary.json",{k:v for k,v in result.items() if k!="filtered"}),
        ("changed-watchlist.json",result["filtered"]["watchlist"]),
        ("changed-watch-report.json",result["filtered"]["report"]),
        ("changed-snapshots.json",result["filtered"]["snapshots"])
    ):
        (a.out_dir/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if a.github_output:
        with a.github_output.open("a",encoding="utf-8") as out:
            out.write(f"has_changes={'true' if result['changed_count'] else 'false'}\n")
    print(f"Fast path: {result['source_count']} watched, {result['changed_count']} changed, "
          f"{len(result['followup_required'])} fetch/baseline exceptions; "
          f"{'semantic check skipped' if result['expensive_review_skipped'] else 'semantic check required'}; "
          f"router {perf_counter()-start:.3f}s; no deploy")
if __name__=="__main__":main()
