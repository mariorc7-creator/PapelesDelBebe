#!/usr/bin/env python3
"""Editorial loop: official change -> affected guide -> verified batch edit.

Fail-closed. A changed HTML fingerprint is never treated as a verified legal
change. Unreviewed candidates are templates, never executable modifications.
A reviewed manifest is joined to the EXACT source digest and page SHA before
the existing guarded updater may edit branch-local HTML. No commit, PR, merge,
production deploy or unattended scheduling is performed here.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

from superagente_official_content_tasks import make_tasks
from superagente_content_updater import digest, run as update_pages

ROOT = Path(__file__).resolve().parents[1]
HOST = "www.papelesdelbebe.es"
HEX = re.compile(r"^[0-9a-f]{64}$")

def page_path(page_url):
    url=urlsplit(page_url)
    if url.scheme!="https" or url.netloc!=HOST or url.query or url.fragment:
        raise ValueError("Invalid mapped page URL")
    path=unquote(url.path)
    if not path.startswith("/") or not path.endswith("/") or ".." in path.split("/") or "\\" in path:
        raise ValueError("Invalid mapped page path")
    rel=path.lstrip("/")+"index.html"
    if not rel.startswith(("comunidades/","ayuda-","ayudas-","deduccion-")):
        raise ValueError("Page out of editorial scope")
    return rel

def plan(watchlist, report, root):
    """Generate *non-authorized* per-page fact-check templates."""
    triage=make_tasks(watchlist, report)
    sources={x["url"]:x for x in watchlist["sources"]}
    states={x["url"]:x for x in report["results"]}
    templates=[]
    for url,item in states.items():
        if item["status"] not in ("changed_needs_review", "unchanged"):
            continue
        rel=page_path(sources[url]["page"])
        target=(root/rel).resolve()
        if root not in target.parents or not target.is_file() or target.is_symlink():
            raise ValueError("Mapped HTML page missing or unsafe: "+rel)
        sha=item.get("sha256")
        if not isinstance(sha,str) or not HEX.fullmatch(sha):
            raise ValueError("Verified source fingerprint not available")
        original=target.read_text(encoding="utf-8")
        templates.append({
            "source_url":url, "source_sha256":sha, "source_status":item["status"],
            "path":rel, "original_sha256":digest(original),
            "suggested_action": "change" if item["status"]=="changed_needs_review" else "review_only",
            "source_verification_required":True, "independent_factual_review_required":True,
            "evidence_ref_required":True,
            "ready_to_apply":False,
            "finding": "Compare official claims, deadlines, amounts and eligibility against the exact guide. Fingerprint alone is not factual evidence." if item["status"]=="changed_needs_review" else
                "Source fingerprint unchanged; independent legal check required before marking guide reviewed."
        })
    templates.sort(key=lambda x:(x["path"],x["source_url"]))
    return {"schema_version":1,"mode":"editorial_review_queue",
        "triage":triage,"templates":templates,
        "website_updates":0,"production_publication_allowed":False}

def validate_approvals(approved, planned):
    if not isinstance(approved,dict) or approved.get("status")!="editorially_verified_for_branch_only" or approved.get("publication_allowed") is not False:
        raise ValueError("Only reviewed non-publishable manifests accepted")
    rows=approved.get("changes")
    if not isinstance(rows,list) or not rows or len(rows)>100:
        raise ValueError("Expected 1..100 approved actions")
    eligible={(x["path"],x["source_url"]):x for x in planned["templates"]}
    found=set()
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("Malformed approved action")
        key=(row.get("path"),row.get("official_source_url"))
        if key in found or key not in eligible:
            raise ValueError("Duplicate or unmapped approved source/page")
        found.add(key)
        template=eligible[key]
        if (row.get("original_sha256")!=template["original_sha256"] or
            row.get("source_sha256")!=template["source_sha256"] or
            row.get("source_sha256") is None):
            raise ValueError("Source/page changed since independent review")
        if template["source_status"]=="unchanged" and row.get("action")!="review_only":
            raise ValueError("Unchanged source cannot justify factual replacement")
        if template["source_status"]=="changed_needs_review" and row.get("action")!="change":
            raise ValueError("Changed source requires independent semantic review before date claims")
    return True

def orchestrate(watchlist, report, root, approved=None, apply=False, branch=None):
    root=Path(root).resolve()
    planned=plan(watchlist,report,root)
    if approved is None:
        if apply:
            raise ValueError("Cannot apply unreviewed detected changes")
        return planned
    validate_approvals(approved,planned)
    if apply and (not isinstance(branch,str) or not branch.startswith("batch/")):
        raise ValueError("Writing allowed only on a batch/* branch")
    result=update_pages(root,approved,apply=apply)
    planned["approved_manifest_present"]=True
    planned["batch_result"]=result
    planned["website_updates"]=result["count"] if apply else 0
    return planned

def current_branch(root):
    return subprocess.check_output(
        ["git","-C",str(root),"branch","--show-current"],text=True).strip()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--watchlist",type=Path,default=ROOT/"superagente/official-watchlist.json")
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--approved-manifest",type=Path)
    p.add_argument("--apply",action="store_true")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    approved=json.loads(args.approved_manifest.read_text(encoding="utf-8")) if args.approved_manifest else None
    result=orchestrate(
        json.loads(args.watchlist.read_text(encoding="utf-8")),
        json.loads(args.report.read_text(encoding="utf-8")),
        args.root,approved=approved,apply=args.apply,
        branch=current_branch(args.root) if args.apply else None
    )
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Editorial loop: {len(result['templates'])} review templates, "
          f"{result['website_updates']} edited pages; no deploy")

if __name__=="__main__":
    main()
