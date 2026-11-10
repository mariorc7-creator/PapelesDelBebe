#!/usr/bin/env python3
"""Atomic update of *only* two known Gencat 2026 birth-grant amounts.

A strict program-specific extractor verifies the literal amount statement,
eligibility wording, the 2026 income table, and deadline rules in a recent
official snapshot bound to the watch report SHA256. Edits only the three
preapproved ES/CA guide files, including factual numbers in metadata.
Never infers a new grant, year, new eligibility rule, or performs SEO rewrites.
All changes are applied together; ambiguous facts fail closed.
"""
import argparse
from datetime import date,timedelta
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re

SOURCE_URL="https://tramits.gencat.cat/es/tramits/tramits-temes/Prestacio-per-a-families-amb-infants?moda=1"
PAGES=(
    "ayuda-nacimiento-cataluna/index.html",
    "ca/ajut-naixement-catalunya-2026/index.html",
    "comunidades/cataluna/index.html",
)
AMOUNTS=re.compile(
    r"El importe de la prestación es de (?P<general>\d{2,5}) euros por niño\. "
    r"Para las familias que tienen reconocido el título de familia numerosa o monoparental, "
    r"en relación con el hijo que da lugar a solicitar la prestación, el importe es de "
    r"(?P<special>\d{2,5}) euros\.",re.I)
REQUIRED_SCOPE=(
    "A familias que han tenido un hijo, ya sea por nacimiento, adopción, tutela o acogida, "
    "siempre que no superen un límite de ingresos.",
    "Si has tenido un hijo a partir del 14 de julio de 2026",
    "Puedes presentar la solicitud durante 3 meses",
    "Para el año 2026 el límite es:",
    "27.904,32", "36.275,62", "44.646,91", "53.018,21",
    "61.389,50", "69.760,80", "78.132,10", "86.503,39",
)
# Strictly numeric token, not a URL, attribute, percentage or larger number.
TOKEN=r"(?<![\d.,])(?P<number>{values})(?![\d.,])(?=\s*(?:€|euros?\b|/|\s+o\s+\d{{2,5}}\s*€))"
DATE_MODIFIED=re.compile(r'("dateModified"\s*:\s*")(\d{4}-\d{2}-\d{2})(")')
SOURCE_MAX_AGE=timedelta(hours=36)
def digest(s):return sha256(s.encode("utf-8")).hexdigest()

def money_from_official(source):
    if not isinstance(source,str) or len(source)>1_000_000:
        raise ValueError("Official text is absent or too large")
    # Normalize whitespace in the captured official text, not legal wording.
    normalized=re.sub(r"\s+", " ", source).strip()
    matches=list(AMOUNTS.finditer(normalized))
    if len(matches)!=1:
        raise ValueError("Missing or duplicated exact Gencat grant paragraph")
    if any(re.sub(r"\s+", " ", text).strip() not in normalized for text in REQUIRED_SCOPE):
        raise ValueError("A legal scope, income-limit or deadline clause differs from the approved 2026 snapshot")
    amounts=[int(matches[0].group("general")),int(matches[0].group("special"))]
    if not 400<=amounts[0]<amounts[1]<=2000:
        raise ValueError("Unexpected or unbounded grant values")
    return amounts

def choose_source(report,snapshots,as_of):
    rows=report.get("results",[])
    captures=snapshots.get("snapshots",[])
    if not isinstance(rows,list) or not isinstance(captures,list):
        raise ValueError("Untrusted official results")
    sr=[x for x in rows if x.get("url")==SOURCE_URL]
    ss=[x for x in captures if x.get("url")==SOURCE_URL]
    if len(sr)!=1 or len(ss)!=1 or sr[0].get("status") not in ("unchanged","changed_needs_review"):
        raise ValueError("Gencat source unavailable or ambiguous")
    payload=ss[0].get("text")
    h=ss[0].get("sha256")
    if not isinstance(payload,str) or h!=digest(payload) or h!=sr[0].get("sha256"):
        raise ValueError("Gencat official text digest mismatch")
    captured=ss[0].get("captured_on")
    if not isinstance(captured,str):
        raise ValueError("Missing captured_on")
    capture_date=date.fromisoformat(captured)
    if capture_date>as_of or as_of-capture_date>timedelta(days=1):
        raise ValueError("Old or future official evidence cannot authorize a publish")
    return payload,h

class StructuralTokens(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags=[]
        self.urls=[]
    def handle_starttag(self,tag,attrs):
        self.tags.append(("open",tag,tuple(k for k,v in attrs)))
        for k,v in attrs:
            if k in ("href","src","action","srcset"):
                self.urls.append((tag,k,v))
    def handle_endtag(self,tag):
        self.tags.append(("close",tag))
    def handle_startendtag(self,tag,attrs):
        self.tags.append(("single",tag,tuple(k for k,v in attrs)))
        for k,v in attrs:
            if k in ("href","src","action","srcset"):
                self.urls.append((tag,k,v))

def guard_factual_page(original,updated,rel):
    if original==updated:
        raise ValueError("No real fact change for "+rel)
    a=StructuralTokens();b=StructuralTokens()
    a.feed(original);b.feed(updated)
    if a.tags!=b.tags or a.urls!=b.urls:
        raise ValueError("Factual amount update changed HTML structure or links: "+rel)
    if original.count('<link rel="canonical"')!=updated.count('<link rel="canonical"'):
        raise ValueError("Canonical changed: "+rel)
    for token in ("<h1","<main","<header","<footer","<nav","<script","<style"):
        if original.count(token)!=updated.count(token):
            raise ValueError("Protected HTML altered: "+rel)

def token_pattern(old):
    vals="|".join(re.escape(str(i)) for i in old)
    return re.compile(TOKEN.format(values=vals),re.I)

def propose(root,policy,report,snapshots,as_of=None):
    as_of=as_of or date.today()
    root=Path(root).resolve()
    if (policy.get("schema_version")!=1 or policy.get("mode")!="gencat-2026-two-amounts"
        or policy.get("publication_allowed") is not False
        or policy.get("official_url")!=SOURCE_URL or
        policy.get("pages")!=list(PAGES)):
        raise ValueError("Unauthorized grant sync policy")
    old=policy.get("current_amounts")
    if not isinstance(old,list) or len(old)!=2 or any(type(v)!=int or not 400<=v<=2000 for v in old) or old[0]>=old[1]:
        raise ValueError("Invalid policy current grant amounts")
    official,h=choose_source(report,snapshots,as_of)
    new=money_from_official(official)
    if new==old:
        return {"changes":[],"policy":policy,"source_sha256":h,"verified_unchanged":True}
    if len(set(old+new))!=4 and new[0]!=old[0] and new[1]!=old[1]:
        # Crossing grant tiers may be legitimate but cannot be guessed from
        # two unlabelled numeric tokens.
        raise ValueError("Overlapping grant values need specialist review")
    pattern=token_pattern(old)
    changed=[]
    for rel in PAGES:
        target=(root/rel).resolve()
        if root not in target.parents or not target.is_file() or target.is_symlink():
            raise ValueError("Missing/unsafe approved ES/CA page")
        html=target.read_text(encoding="utf-8")
        expected_official_link=(SOURCE_URL.replace("/es/tramits/","/ca/tramits/")
                                if rel.startswith("ca/") else SOURCE_URL)
        if not (("Cataluña" in html or "Catalunya" in html) and expected_official_link in html):
            raise ValueError("Missing Catalonia grant identity and official link: "+rel)
        match_counts={old[0]:0,old[1]:0}
        def replace(m):
            value=int(m.group("number"))
            match_counts[value]+=1
            return str(new[old.index(value)])
        updated=pattern.sub(replace,html)
        if any(count<1 for count in match_counts.values()):
            raise ValueError("Each approved page must reference both original grant amounts: "+rel)
        # If any old token is still present after replacement, a visible title,
        # FAQ or metadata fact was missed. Never leave mixed amounts.
        changed_old=[old[i] for i in range(2) if old[i]!=new[i]]
        if changed_old and token_pattern(changed_old).search(updated):
            raise ValueError("Residual original grant amounts: "+rel)
        # Preserve every character except approved numeric values and JSON-LD
        # dateModified, which must represent the real content edit date.
        updated,dates=DATE_MODIFIED.subn(lambda m:m.group(1)+as_of.isoformat()+m.group(3),updated)
        if dates==0:
            raise ValueError("Missing dateModified in approved guide: "+rel)
        guard_factual_page(html,updated,rel)
        changed.append({"path":rel,"before_sha256":digest(html),
                        "content":updated,"old_token_counts":match_counts})
    next_policy={**policy,"current_amounts":new,
                 "last_verified_source_sha256":h,"last_content_update":as_of.isoformat()}
    return {"changes":changed,"policy":next_policy,"source_sha256":h,
            "verified_unchanged":False,"amounts_before":old,"amounts_after":new,
            "legal_scope_changed":False,"non_amount_seo_changes_allowed":False}

def apply(root,decision,enabled=False):
    root=Path(root).resolve()
    if not enabled:
        return {"changed_pages":0,"dry_run":True}
    # Preflight ALL targets and policy before writing any file.
    for item in decision["changes"]:
        target=(root/item["path"]).resolve()
        if root not in target.parents or not target.is_file() or digest(target.read_text(encoding="utf-8"))!=item["before_sha256"]:
            raise ValueError("Stale content, abort entire Gencat batch")
    for item in decision["changes"]:
        (root/item["path"]).write_text(item["content"],encoding="utf-8")
    if decision["changes"]:
        (root/"superagente/gencat-amount-policy.json").write_text(
            json.dumps(decision["policy"],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"changed_pages":len(decision["changes"]),"requires_github_publish":bool(decision["changes"])}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--policy",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    read=lambda f:json.loads(f.read_text(encoding="utf-8"))
    d=propose(a.root,read(a.policy),read(a.report),read(a.snapshots))
    result=apply(a.root,d,a.apply)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({"result":result,"source_sha256":d["source_sha256"],
        "verified_unchanged":d["verified_unchanged"],
        "amounts_before":d.get("amounts_before"),"amounts_after":d.get("amounts_after"),
        "changed_files":[x["path"] for x in d["changes"]],
        "seo_optimization_performed":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Gencat factual amounts: {result['changed_pages']} synchronized ES/CA pages; no routine SEO changes")
if __name__=="__main__":main()
