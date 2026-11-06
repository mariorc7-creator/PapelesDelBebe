#!/usr/bin/env python3
"""Serve an editorial candidate on ephemeral localhost, then roll it back.

Safety properties: only a temporary directory is modified; no git operations,
cloud deploys, credentials, production writes or review-date modifications.
This is a *local CI staging simulation*, not a remote staging deployment.
"""
import argparse
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import tempfile
import threading
from urllib.request import urlopen

from superagente_cataluna_package import build

def digest(data):
    return hashlib.sha256(data).hexdigest()

def stage_and_rollback(root, manifest):
    root=Path(root).resolve()
    report=build(root,manifest)
    rel=Path(manifest["path"])
    original_path=(root/rel).resolve()
    original=original_path.read_bytes()
    expected=original
    for change in manifest["changes"]:
        a,b=change["search"].encode("utf-8"),change["replacement"].encode("utf-8")
        if expected.count(a)!=1:
            raise ValueError("stale patch anchor")
        expected=expected.replace(a,b,1)
    checks=[]
    with tempfile.TemporaryDirectory(prefix="superagente-staging-http-") as temp:
        site=Path(temp)/"site"
        page=site/rel
        page.parent.mkdir(parents=True)
        page.write_bytes(original)
        # Test a real HTTP server against the very same sandbox file before,
        # during, and after the candidate deployment.
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,directory=str(site),**kwargs)
            def log_message(self,format,*args):
                pass
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        target="http://127.0.0.1:%d/%s"%(server.server_port,rel.parent.as_posix()+"/")
        def probe(phase,data):
            with urlopen(target,timeout=3) as response:
                body=response.read()
                status=response.status
            if status!=200 or body!=data:
                raise RuntimeError("staging HTTP verification failed: "+phase)
            checks.append({"phase":phase,"http_status":status,
                           "content_sha256":digest(body)})
        try:
            probe("baseline",original)
            try:
                page.write_bytes(expected)
                probe("candidate",expected)
                if any(x["replacement"].encode("utf-8") not in expected for x in manifest["changes"]):
                    raise RuntimeError("candidate did not contain both amendments")
            finally:
                # Even on a failed candidate HTTP check, restore baseline.
                page.write_bytes(original)
                probe("rollback",original)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        if page.read_bytes()!=original:
            raise RuntimeError("staging rollback digest mismatch")
    if original_path.read_bytes()!=original:
        raise RuntimeError("source checkout unexpectedly changed")
    if (report["original_sha256"]!=checks[0]["content_sha256"] or
            report["proposed_sha256"]!=checks[1]["content_sha256"] or
            checks[0]["content_sha256"]!=checks[2]["content_sha256"]):
        raise RuntimeError("hash mismatch across local staging lifecycle")
    return {"schema_version":1,"package_id":manifest["package_id"],
            "scope":"ephemeral_localhost_ci_staging_simulation",
            "http_probes":checks,"candidate_changes":len(manifest["changes"]),
            "same_served_directory_rollback_passed":True,
            "source_checkout_modified":False,
            "remote_staging_deployment_tested":False,
            "production_rollback_tested":False,
            "editorial_approval":False,"publication_allowed":False,
            "warning":"HTTP staging simulation is isolated to CI and does not validate a remote hosting provider's deploy/rollback."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest",type=Path,default=Path("superagente/proposals/cataluna-2026-11-06-batch.json"))
    parser.add_argument("--output",type=Path,default=Path("superagente/proposals/cataluna-local-staging-rollback.json"))
    args=parser.parse_args()
    root=args.root.resolve()
    path=args.manifest if args.manifest.is_absolute() else root/args.manifest
    result=stage_and_rollback(root,json.loads(path.read_text(encoding="utf-8")))
    out=args.output if args.output.is_absolute() else root/args.output
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Ephemeral HTTP staging: baseline/candidate/rollback all 200, original unchanged")
if __name__=="__main__":main()
