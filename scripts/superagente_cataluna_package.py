#!/usr/bin/env python3
"""Atomic multi-edit editorial package preview plus byte-exact local rollback.

No writes to tracked HTML, review dates, git branch, deployment or production.
A successful local reversal is not a staging/production rollback guarantee.
"""
import argparse
import difflib
import hashlib
import json
import tempfile
from pathlib import Path

def sha(data):
    return hashlib.sha256(data).hexdigest()

def build(root, package):
    root=Path(root).resolve()
    if not isinstance(package, dict) or package.get("status") != "proposal_not_approved" or package.get("publication_allowed") is not False or package.get("merge_allowed") is not False:
        raise ValueError("must remain explicitly unapproved/non-publishable")
    rel=Path(package.get("path",""))
    target=(root/rel).resolve()
    if rel.is_absolute() or ".." in rel.parts or root not in target.parents or target.suffix != ".html" or not target.is_file():
        raise ValueError("invalid HTML path")
    src=package.get("source_url")
    if not isinstance(src,str) or not src.startswith("https://tramits.gencat.cat/"):
        raise ValueError("exact institutional source required")
    evidence_path=(root/str(package.get("evidence_report",""))).resolve()
    if root not in evidence_path.parents or not evidence_path.is_file():
        raise ValueError("missing evidence report")
    evidence=json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence.get("page_source_path") != str(rel) or evidence.get("source_url") != src or evidence.get("editorial_approval") is not False:
        raise ValueError("evidence page/source mismatch or approval mislabeled")
    verified_topics={x["topic"] for x in evidence.get("checks",[]) if isinstance(x,dict) and x.get("source_excerpt") and x.get("recommended_action")}
    changes=package.get("changes")
    if not isinstance(changes,list) or len(changes)<2 or len(changes)>12:
        raise ValueError("expected grouped editorial edits")
    before=target.read_bytes()
    changed=before
    anchors=set()
    for item in changes:
        if not isinstance(item,dict) or not item.get("id") or item.get("evidence_topic") not in verified_topics:
            raise ValueError("missing specific documented finding")
        old=item.get("search")
        new=item.get("replacement")
        if not isinstance(old,str) or not isinstance(new,str) or not old or not new or old==new:
            raise ValueError("invalid edit")
        if old in anchors or before.count(old.encode("utf-8")) != 1 or changed.count(old.encode("utf-8")) != 1:
            raise ValueError("stale or duplicate original anchor")
        if before.count(new.encode("utf-8")):
            raise ValueError("replacement already present")
        changed=changed.replace(old.encode("utf-8"),new.encode("utf-8"),1)
        anchors.add(old)
    if changed==before:
        raise ValueError("no change")
    if any(changed.count(x["replacement"].encode("utf-8"))!=1 for x in changes):
        raise ValueError("nonunique final replacement")
    # The source file is never modified; rollback is proven in an isolated temp file.
    with tempfile.TemporaryDirectory(prefix="superagente-cataluna-") as tmp:
        staged=Path(tmp)/"index.html"
        staged.write_bytes(before)
        staged.write_bytes(changed)
        if staged.read_bytes()!=changed:
            raise RuntimeError("staged write changed unexpectedly")
        reverse=staged.read_bytes()
        for item in reversed(changes):
            reverse=reverse.replace(item["replacement"].encode("utf-8"),item["search"].encode("utf-8"),1)
        staged.write_bytes(reverse)
        if staged.read_bytes()!=before:
            raise RuntimeError("grouped rollback failed")
    if target.read_bytes()!=before:
        raise RuntimeError("source checkout HTML mutated")
    diff="".join(difflib.unified_diff(before.decode("utf-8").splitlines(True),
        changed.decode("utf-8").splitlines(True),fromfile="a/"+str(rel),tofile="b/"+str(rel)))
    return {"package_id":package["package_id"],"path":str(rel),"edit_ids":[x["id"] for x in changes],
            "original_sha256":sha(before),"proposed_sha256":sha(changed),
            "restored_sha256":sha(before),"byte_exact_local_rollback":True,
            "production_rollback_tested":False,"modified_html_files":0,
            "editorial_approval":False,"publication_allowed":False,
            "unified_diff":diff,"warning":"Evidence supports proposals; independent editorial approval and staging rollback remain pending."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--manifest",type=Path,default=Path("superagente/proposals/cataluna-2026-11-06-batch.json"))
    p.add_argument("--output",type=Path,default=Path("superagente/proposals/cataluna-2026-11-06-preview.json"))
    args=p.parse_args()
    root=args.root.resolve()
    src=args.manifest if args.manifest.is_absolute() else root/args.manifest
    result=build(root,json.loads(src.read_text(encoding="utf-8")))
    out=args.output if args.output.is_absolute() else root/args.output
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Catalonia grouped preview: %d edits; local rollback exact; no HTML written"%len(result["edit_ids"]))
if __name__=="__main__":main()
