#!/usr/bin/env python3
"""Fail-closed candidate-reference validation; never asserts legal validity."""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

STATUS = "candidate_needs_document_review"
def validate(candidates, routing, pages):
    routes = {r["page"]:r for r in routing.get("routes",[]) if isinstance(r,dict) and "page" in r}
    refs = candidates.get("references") if isinstance(candidates,dict) else None
    if not isinstance(refs,list) or not refs:
        raise ValueError("nonempty references array required")
    results, seen = [], set()
    for i, ref in enumerate(refs):
        errors = []
        if not isinstance(ref,dict):
            results.append({"index":i,"errors":["invalid:reference"],"status":"blocked"})
            continue
        page = ref.get("page")
        if page not in pages or page not in routes:
            errors.append("unmapped:page")
        if page in seen:
            errors.append("duplicate:page")
        seen.add(page)
        for key in ("source_url","approved_host","authority","document_type"):
            if not isinstance(ref.get(key),str) or not ref[key].strip():
                errors.append("missing:"+key)
        try:
            u=urlsplit(ref.get("source_url",""))
            if (u.scheme!="https" or not u.hostname or u.hostname!=ref.get("approved_host")
                or u.username or u.password or u.port not in (None,443)
                or u.fragment or u.path in ("","/")):
                errors.append("invalid:exact_official_url")
        except (TypeError,ValueError):
            errors.append("invalid:exact_official_url")
        if page in routes and ref.get("authority") != routes[page].get("authority"):
            errors.append("mismatch:authority")
        if ref.get("status") != STATUS:
            errors.append("invalid:verification_claim")
        if any(k in ref for k in ("verified","approved_for_publication","date_reviewed","legal_verified")):
            errors.append("blocked:verification_not_supported")
        results.append({"index":i,"page":page,"status":"blocked" if errors else "reference_needs_review",
                        "errors":sorted(set(errors)),"publishable":False})
    return {"checked":len(refs),"blocked":sum(r["status"]=="blocked" for r in results),
            "results":results,"warning":"Official-looking URLs are not evidence of accuracy, applicability or legal validity."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",type=Path,default=Path("superagente/official-document-candidates.json"))
    p.add_argument("--routing",type=Path,default=Path("superagente/source-routing.json"))
    p.add_argument("--sitemap",type=Path,default=Path("sitemap.xml"))
    p.add_argument("--output",type=Path,default=Path("superagente/document-candidate-report.json"))
    args=p.parse_args()
    pages={n.text.strip() for n in ET.parse(args.sitemap).getroot().findall(".//{*}loc") if n.text}
    report=validate(json.loads(args.candidates.read_text(encoding="utf-8")),
                    json.loads(args.routing.read_text(encoding="utf-8")),pages)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Document references: {report['checked']} checked; {report['blocked']} blocked")
    raise SystemExit(1 if report["blocked"] else 0)
if __name__=="__main__":
    main()
