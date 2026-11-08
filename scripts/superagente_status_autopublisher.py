#!/usr/bin/env python3
"""Autonomous *narrow* editorial updater for official filing-window status.

Writes only one previously approved, machine-managed status sentence, when:
- a complete, unchanged, public official snapshot is bound by SHA256;
- the same unambiguous application window and explicit status are in the source;
- official status and calendar agree;
- every other status occurrence on the target page is consistent;
- exact old text is unique within <main> and SEO metadata is immutable.
Unknown legal rules, eligibility, amounts, new years and contradictory pages
are escalated. Never certify legal eligibility or invent new 2027 calls.
"""
import argparse
from datetime import date, datetime
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from superagente_autofact_guard import guard_html

HEX=re.compile(r"^[a-f0-9]{64}$")
WINDOW=re.compile(r"Plazo de presentación.{0,400}?Desde:\s*(\d{2}/\d{2}/20\d{2})\s*Hasta:\s*(\d{2}/\d{2}/20\d{2})",re.I|re.S)
STATES={"Fuera de plazo":"closed","En plazo":"open"}
ROOT=Path(__file__).resolve().parents[1]

def hash_text(value):return sha256(value.encode("utf-8")).hexdigest()
def parse_status(text,as_of):
    if not isinstance(text,str) or len(text)>1_000_000:
        raise ValueError("Invalid official text")
    if "Ayudas por natalidad" not in text or "Extremadura" not in text:
        raise ValueError("Official procedure not uniquely recognized")
    found=WINDOW.findall(text)
    if len(found)!=1:
        raise ValueError("Filing window missing or ambiguous")
    start=datetime.strptime(found[0][0],"%d/%m/%Y").date()
    end=datetime.strptime(found[0][1],"%d/%m/%Y").date()
    if start>end:raise ValueError("Invalid application period")
    # Match status only near procedure title, not archived breadcrumbs or FAQ.
    marker=re.search(r"Ayudas por natalidad.{0,400}?(Fuera de plazo|En plazo)",text,re.I|re.S)
    if not marker:raise ValueError("No explicit official application status")
    observed=next((v for k,v in STATES.items() if k.casefold()==marker.group(1).casefold()),None)
    if observed is None:raise ValueError("Unknown source status")
    expected="open" if start<=as_of<=end else "closed"
    if observed!=expected:
        raise ValueError("Official status conflicts with filing window and check date")
    return {"status":observed,"start":start.isoformat(),"end":end.isoformat()}

def plan(policy,report,snapshots,root,as_of=None):
    as_of=as_of or date.today()
    root=Path(root).resolve()
    if policy.get("schema_version")!=1 or policy.get("publication_allowed") is not False:
        raise ValueError("Unapproved automatic-edit policy")
    rules=policy.get("rules")
    if not isinstance(rules,list) or len(rules)!=1:raise ValueError("Exactly one pre-approved regional rule required")
    report_by={x["url"]:x for x in report.get("results",[])}
    snap_by={x["url"]:x for x in snapshots.get("snapshots",[])}
    if len(report_by)!=len(report.get("results",[])) or len(snap_by)!=len(snapshots.get("snapshots",[])):
        raise ValueError("Duplicate official source")
    edits=[]; incidents=[]
    for rule in rules:
        rid=rule.get("id")
        url=rule.get("source_url")
        rel=rule.get("page")
        if (rid!="extremadura-natalidad-2026" or
            url!="https://www.juntaex.es/w/0702824" or
            rule.get("type")!="extremadura_2026_status" or
            rel!="comunidades/extremadura/index.html"):
            raise ValueError("Unsupported automatic legal rule")
        target=(root/rel).resolve()
        if root not in target.parents or not target.is_file() or target.is_symlink():
            raise ValueError("Missing approved site page")
        record=report_by.get(url,{})
        snapshot=snap_by.get(url,{})
        digest=record.get("sha256")
        if (record.get("status") not in ("unchanged","changed_needs_review") or
            not isinstance(digest,str) or not HEX.fullmatch(digest) or
            snapshot.get("sha256")!=digest or not isinstance(snapshot.get("text"),str) or
            hash_text(snapshot["text"])!=digest):
            incidents.append({"id":rid,"reason":"source_unavailable_or_stale"})
            continue
        try:
            current=parse_status(snapshot["text"],as_of)
            if not current["end"].startswith("2026-"):
                raise ValueError("New-year calls need a separate explicit policy")
            html=target.read_text(encoding="utf-8")
            start_marker="<!-- superagente:extremadura-2026:start -->"
            end_marker="<!-- superagente:extremadura-2026:end -->"
            if html.count(start_marker)!=1 or html.count(end_marker)!=1:
                raise ValueError("Approved managed content area missing")
            prefix,tail=html.split(start_marker,1)
            old, suffix=tail.split(end_marker,1)
            status_word="fuera de plazo" if current["status"]=="closed" else "en plazo"
            new=f"<strong>Ayuda rural por natalidad de 500 €: {status_word}.</strong>"
            if old==new:
                continue
            # Historical notes, other body claims or metadata referencing a
            # contradictory status must be revised together, never hidden.
            remaining=prefix+suffix
            other_status=re.search(r"(convocatoria.{0,35}(?:cerrada|abierta)|(?:fuera de plazo|en plazo))",remaining,re.I)
            if other_status:
                raise ValueError("Multiple status statements require full editorial correction")
            changed=prefix+start_marker+new+end_marker+suffix
            guard_html(html,changed)
            edits.append({"id":rid,"path":rel,"old_sha256":hash_text(html),
                          "new_content":changed,"source_sha256":digest,
                          "source_url":url,"change_kind":"application_status_only"})
        except ValueError as error:
            incidents.append({"id":rid,"reason":str(error)})
    return {"schema_version":1,"mode":"bounded_official_auto_update",
        "edits":edits,"incidents":incidents,"seo_fields_changed":False,
        "legal_eligibility_proven":False,"automatic_factual_changes_only":True}

def apply(root,decision,enabled=False):
    root=Path(root).resolve()
    if not enabled: return {"changed_pages":0,"skipped":"dry_run"}
    if decision["incidents"]:
        raise ValueError("Do not publish a partially contradictory batch")
    for edit in decision["edits"]:
        target=(root/edit["path"]).resolve()
        if root not in target.parents or hash_text(target.read_text(encoding="utf-8"))!=edit["old_sha256"]:
            raise ValueError("Stale site page: stop the whole batch")
    for edit in decision["edits"]:
        (root/edit["path"]).write_text(edit["new_content"],encoding="utf-8")
    return {"changed_pages":len(decision["edits"]),"requires_git_publish":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--policy",type=Path,required=True)
    p.add_argument("--watch-report",type=Path,required=True)
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    data=lambda path:json.loads(path.read_text(encoding="utf-8"))
    decision=plan(data(a.policy),data(a.watch_report),data(a.snapshots),a.root)
    result=apply(a.root,decision,enabled=a.apply)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({"decision":{**decision,"edits":[{k:v for k,v in e.items() if k!="new_content"} for e in decision["edits"]]},"result":result},
                 ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Auto status: {result['changed_pages']} pages; {len(decision['incidents'])} blocked; SEO immutable")
if __name__=="__main__":main()
