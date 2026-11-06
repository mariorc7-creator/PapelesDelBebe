#!/usr/bin/env python3
"""Extend an existing disposable mobile preview with grouped Catalonia changes.

Only writes to an isolated sandbox, never to the checkout or production.
"""
import argparse
import json
from pathlib import Path
from superagente_cataluna_package import build

def add_residence(root,sandbox,package):
    root=Path(root).resolve()
    sandbox=Path(sandbox).resolve()
    if sandbox==root or root in sandbox.parents or sandbox in root.parents:
        raise ValueError("sandbox must be outside checkout")
    build(root,package)
    changes=package["changes"]
    if len(changes)!=2 or [c["id"] for c in changes] != [
        "deadline_pre_2026_07_14","residence_requirement_clarification"]:
        raise ValueError("unexpected batch composition")
    rel=Path(package["path"])
    original=(root/rel).read_bytes()
    preview=(sandbox/rel).resolve()
    if sandbox not in preview.parents or not preview.is_file():
        raise ValueError("invalid preview path")
    first,second=changes
    initial_preview=original.replace(first["search"].encode("utf-8"),first["replacement"].encode("utf-8"),1)
    if preview.read_bytes()!=initial_preview:
        raise ValueError("preview does not match previously staged deadline proposal")
    updated=initial_preview.replace(second["search"].encode("utf-8"),
                                    second["replacement"].encode("utf-8"),1)
    if updated==initial_preview:
        raise ValueError("stale residence anchor")
    preview.write_bytes(updated)
    if (root/rel).read_bytes()!=original:
        raise RuntimeError("checkout HTML unexpectedly changed")
    return {"path":str(rel),"source_unchanged":True,"preview_has_both_edits":True,
            "publication_allowed":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--sandbox-root",type=Path,required=True)
    p.add_argument("--manifest",type=Path,default=Path("superagente/proposals/cataluna-2026-11-06-batch.json"))
    args=p.parse_args()
    root=args.root.resolve()
    source=args.manifest if args.manifest.is_absolute() else root/args.manifest
    report=add_residence(root,args.sandbox_root,json.loads(source.read_text(encoding="utf-8")))
    print("Catalonia two-edit responsive preview staged; original HTML untouched")
if __name__=="__main__":main()
