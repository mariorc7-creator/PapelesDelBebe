#!/usr/bin/env python3
"""Semantic candidate triage of official-source money/date clauses.

Not a legal fact verifier. Produces exact evidence snippets from fetched official
text with source hash and matching page hash. False positives are expected:
numeric overlap and keyword similarity are NOT eligibility or legal validity.
Never rewrites content, review timestamps or production.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urlsplit
from html.parser import HTMLParser

URL_HOST = "www.papelesdelbebe.es"
NUMERIC = re.compile(r'(?<!\w)(?:\d{1,3}(?:[.\s]\d{3})+|\d{1,6})(?:[,.]\d+)?\s*(?:€|euros?|%|meses?|años?|d[ií]as?)(?!\w)',re.I)
KEYWORDS = re.compile(r'\b(?:ayudas?|prestaci[oó]n|nacimiento|deducci[oó]n|solicitud|convocatoria|plazo|renta|requisito|crianza)\b',re.I)
SPACES = re.compile(r'\s+')

def normalize(value):
    value=unicodedata.normalize("NFD",value.lower())
    value="".join(c for c in value if not unicodedata.combining(c))
    return SPACES.sub(" ",value).strip()

class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__();self.skip=0;self.blocks=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","nav","header","footer","noscript"):
            self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","nav","header","footer","noscript") and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.blocks.append(data)

def site_file(page_url, root):
    p=urlsplit(page_url)
    path=unquote(p.path)
    if (p.scheme!="https" or p.netloc!=URL_HOST or p.query or p.fragment
        or not path.startswith("/") or not path.endswith("/") or ".." in path.split("/")
        or "\\" in path or "\0" in path):
        raise ValueError("Invalid site page URL")
    rel=path.lstrip("/")+"index.html"
    if not rel.startswith(("comunidades/","ayuda-","ayudas-","deduccion-")):
        raise ValueError("Page outside supported scope")
    target=(root/rel).resolve()
    if root not in target.parents or not target.is_file() or target.is_symlink():
        raise ValueError("Unmapped page")
    return rel,target

def clauses(text):
    # Bound content; split on sentence boundaries while keeping numerical tokens.
    parts=re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÜÑ0-9])',text)
    result=[]
    for part in parts:
        cleaned=SPACES.sub(" ",part).strip()
        if len(cleaned)<20 or len(cleaned)>1100 or not KEYWORDS.search(cleaned):
            continue
        nums=NUMERIC.findall(cleaned)
        if nums:
            result.append((cleaned,nums))
    return result

def compare(watchlist,watch_report,snapshots,root,limit=30):
    root=Path(root).resolve()
    sources=watchlist.get("sources")
    states=watch_report.get("results")
    captures=snapshots.get("snapshots")
    if not all(isinstance(x,list) for x in (sources,states,captures)):
        raise ValueError("Malformed watch input")
    mapping={}
    for item in sources:
        url=item.get("url")
        if not isinstance(url,str) or url in mapping:raise ValueError("Duplicate source")
        mapping[url]=item
    reported={}
    for item in states:
        url=item.get("url")
        if url not in mapping or url in reported:raise ValueError("Unexpected report source")
        reported[url]=item
    if set(reported)!=set(mapping):raise ValueError("Missing report sources")
    snap_by={}
    for item in captures:
        url=item.get("url")
        if url not in mapping or url in snap_by:raise ValueError("Unexpected capture")
        snap_by[url]=item
    results=[]
    for url,source in mapping.items():
        state=reported[url]
        status=state.get("status")
        if status not in ("changed_needs_review","unchanged","baseline_missing","fetch_failed","blocked_invalid_host"):
            raise ValueError("Invalid status")
        if status not in ("changed_needs_review","unchanged"):
            results.append({"source_url":url,"status":"not_comparable","reason":status,"candidates":[]})
            continue
        snapshot=snap_by.get(url)
        if not snapshot or not isinstance(snapshot.get("text"),str):
            raise ValueError("Missing exact source text")
        text=snapshot["text"]
        sha=hashlib.sha256(text.encode("utf-8")).hexdigest()
        if sha!=state.get("sha256") or sha!=snapshot.get("sha256"):
            raise ValueError("Source snapshot hash mismatch")
        rel,target=site_file(source.get("page"),root)
        html=target.read_text(encoding="utf-8")
        parsed=HTMLText();parsed.feed(html)
        page=normalize(" ".join(parsed.blocks))
        candidates=[]
        if status=="changed_needs_review":
            for sentence,numbers in clauses(text):
                distinct=list(dict.fromkeys(n.strip() for n in numbers))
                # Numeric evidence present in a source but not obviously present on page.
                new=[n for n in distinct if normalize(n) not in page]
                if not new:continue
                # Only cite small slices; no generated replacement or legal interpretation.
                evidence=sentence[:230]
                candidates.append({
                    "source_excerpt":evidence,
                    "candidate_numeric_tokens":new[:8],
                    "classification":"needs_semantic_legal_review",
                    "verified_applicability":False,
                    "auto_replace_allowed":False,
                })
                if len(candidates)>=limit:break
        results.append({"source_url":url,"source_sha256":sha,"page":rel,
            "page_sha256":hashlib.sha256(html.encode("utf-8")).hexdigest(),
            "status":"possible_factual_difference" if candidates else "no_numeric_candidate",
            "candidates":candidates,
            "must_check_dates_scope_and_exceptions":True})
    return {"schema_version":1,"mode":"evidence_tied_semantic_triage",
        "results":results,"candidate_count":sum(len(x["candidates"]) for x in results),
        "verified_legal_changes":0,"automatic_edits":0,
        "auto_publish_allowed":False,
        "warning":"Candidate snippets are NOT proven new laws or verified entitlements. Exact source and page hashes must be rechecked."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--watchlist",type=Path,required=True)
    p.add_argument("--watch-report",type=Path,required=True)
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=compare(*[json.loads(file.read_text(encoding="utf-8")) for file in
        (a.watchlist,a.watch_report,a.snapshots)],a.root)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Semantic candidate triage: {result['candidate_count']} snippets, 0 verified legal changes, no publication")
if __name__=="__main__":main()
