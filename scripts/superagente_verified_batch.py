#!/usr/bin/env python3
"""Verified editorial batch entrypoint: no direct ungrounded edits.

Source snapshots and exact document quotations MUST pass the legal evidence
gate before the editorial loop can write to a batch/* branch. Never commits,
merges, deploys, schedules or automatically grants legal truth.
"""
import argparse
import json
from pathlib import Path
import subprocess

from superagente_legal_evidence_gate import verify,to_branch_manifest
from superagente_editorial_loop import orchestrate

def execute(root,watchlist,watch_report,snapshots,claims,review_date,apply=False,branch=None):
    evidence=verify(claims,watchlist,watch_report,snapshots,root)
    approved=to_branch_manifest(evidence,review_date)
    if apply and (not branch or not branch.startswith("batch/")):
        raise ValueError("Only batch/* branches can be edited")
    result=orchestrate(watchlist,watch_report,root,approved=approved,apply=apply,branch=branch)
    return {
        "schema_version":1,
        "mode":"verified_editorial_batch",
        "documentary_evidence_count":evidence["validated_count"],
        "pages_updated":result["website_updates"],
        "branch":branch if apply else None,
        "production_deployment_allowed":False,
        "automatic_legal_truth_established":False,
        "evidence_summary":[{"source_url":i["source_url"],"source_sha256":i["source_sha256"],
                             "path":i["path"],"page_sha256":i["page_sha256"],
                             "evidence_ref":i["evidence_ref"]} for i in evidence["records"]],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--watchlist",type=Path,required=True)
    p.add_argument("--watch-report",type=Path,required=True)
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--claims",type=Path,required=True)
    p.add_argument("--review-date",required=True)
    p.add_argument("--apply",action="store_true")
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    v=lambda f:json.loads(f.read_text(encoding="utf-8"))
    branch=(subprocess.check_output(["git","-C",str(a.root),"branch","--show-current"],text=True).strip()
            if a.apply else None)
    result=execute(a.root,v(a.watchlist),v(a.watch_report),v(a.snapshots),v(a.claims),
                   a.review_date,apply=a.apply,branch=branch)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Verified editorial batch: {result['documentary_evidence_count']} approved records; "
          f"{result['pages_updated']} pages changed on a branch; no deployment")
if __name__=="__main__":main()
