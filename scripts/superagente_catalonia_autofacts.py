#!/usr/bin/env python3
"""Source-bound, coordinated updates of Catalonia family benefit amounts.

This is deliberately NOT a general legislative interpreter. Only an explicitly
registered, fixed-identity scheme and two monetary facts may be changed.
Amounts must be unambiguous in a fresh official HTTPS capture (SHA bound),
in the correct beneficiary clauses. Every occurrence across all registered
pages, including actual factual SEO descriptions and FAQ schema, is updated
as one transaction; unrelated metadata and layout are preserved.

Stop on unknown scheme, inconsistent pages, unregistered references, missing
source, missing consent for factual changes, out-of-scope years, or ambiguity.
"""
import argparse
from datetime import date
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from superagente_cross_page_impact import textual,seo_claims

ROOT=Path(__file__).resolve().parents[1]
SOURCE="https://tramits.gencat.cat/es/tramits/tramits-temes/Prestacio-per-a-families-amb-infants?moda=1"
PAGES=("comunidades/cataluna/index.html","ayuda-nacimiento-cataluna/index.html",
       "ca/ajut-naixement-catalunya-2026/index.html",
       "ayuda-nacimiento-cataluna-2026/index.html",
       "ayudas-nacimiento-cataluna-2026/index.html",
       "compatibilidad-ayudas-nacimiento/index.html",
       "observatorio/index.html")
AMOUNT_GENERAL=re.compile(r"El importe de la prestaci[oó]n es de ([0-9][0-9.]*) euros por ni[nñ]o",re.I)
AMOUNT_SPECIAL=re.compile(r"familias que tienen reconocido el t[ií]tulo de familia numerosa o monoparental.{0,250}?el importe es de ([0-9][0-9.]*) euros",re.I|re.S)
HEX=re.compile(r"^[0-9a-f]{64}$")
SAFE_NUMBER=re.compile(r"^[0-9]{3,5}$")
SEO_FIELDS=("canonical","robots","viewport","stylesheet")
OLD_VAL=re.compile(r"(?<!\d)([0-9]{3,5})(?!\d)")

def hash_text(text):return sha256(text.encode("utf-8")).hexdigest()
def extract(text):
    if not isinstance(text,str) or not 50<len(text)<1_000_000:
        raise ValueError("Source capture missing")
    if "Prestación para familias" not in text and "Prestación para familias con hijos" not in text:
        raise ValueError("Wrong official scheme")
    a=AMOUNT_GENERAL.findall(text);b=AMOUNT_SPECIAL.findall(text)
    if len(a)!=1 or len(b)!=1:
        raise ValueError("Official amounts missing or ambiguous")
    amounts=[]
    for matches in (a,b):
        token=matches[0].replace(".","")
        if not SAFE_NUMBER.fullmatch(token):
            raise ValueError("Implausible or malformed amount")
        amounts.append(int(token))
    if not (100<=amounts[0]<amounts[1]<=5000):
        raise ValueError("New amounts outside reviewed boundaries")
    return amounts

def protected(html):
    def first(pattern):
        matches=re.findall(pattern,html,re.I|re.S)
        return matches
    return {
        "canonical":first(r'<link\b(?=[^>]*rel=["\x27]canonical["\x27])[^>]*>'),
        "robots":first(r'<meta\b(?=[^>]*name=["\x27]robots["\x27])[^>]*>'),
        "viewport":first(r'<meta\b(?=[^>]*name=["\x27]viewport["\x27])[^>]*>'),
        "stylesheet":first(r'<link\b(?=[^>]*rel=["\x27]stylesheet["\x27])[^>]*>'),
        "hrefs":first(r'\bhref=["\x27]([^"\x27]+)["\x27]'),
        "scripts":len(first(r"<script\b")),
        "h1":len(first(r"<h1\b")),
        "main":len(first(r"<main\b")),
        "head":len(first(r"<head\b")),
        "footer":len(first(r"<footer\b")),
    }

def amounts_on_related_pages(root,old):
    """Conservatively block unknown pages mentioning both the scheme and old values."""
    others=[]
    for path in root.rglob("index.html"):
        if path.is_symlink() or path.stat().st_size>1_200_000:continue
        rel=path.relative_to(root).as_posix()
        if rel.startswith(("node_modules/","dist/")):continue
        doc=path.read_text(encoding="utf-8")
        txt=(textual(doc)+" "+seo_claims(doc)).casefold()
        if not ("catalu" in txt or "catalunya" in txt):continue
        if not ("nacimiento" in txt or "naixement" in txt or "prestaci" in txt):continue
        if all(re.search(rf"(?<!\d){n}(?!\d)",txt) for n in old):
            if rel not in PAGES:others.append(rel)
    return sorted(others)

def build(policy,watch_report,snapshots,root,as_of=None):
    root=Path(root).resolve()
    as_of=as_of or date.today()
    if (not isinstance(policy,dict) or policy.get("schema_version")!=1 or
        policy.get("publication_allowed") is not False or
        policy.get("source_url")!=SOURCE or policy.get("pages")!=list(PAGES) or
        policy.get("scheme")!="cataluna-family-benefit" or policy.get("year")!=2026):
        raise ValueError("Unapproved or unfamiliar source-to-site contract")
    if as_of.year!=2026:raise ValueError("New fiscal year requires renewed legal policy")
    old=policy.get("last_published_amounts")
    if (not isinstance(old,list) or len(old)!=2 or
        not all(type(x) is int and 100<=x<=5000 for x in old) or old[0]>=old[1]):
        raise ValueError("Incorrect or missing previous amount baseline")
    records=watch_report.get("results",[])
    captured=snapshots.get("snapshots",[])
    if (len([r for r in records if r.get("url")==SOURCE])!=1 or
        len([r for r in captured if r.get("url")==SOURCE])!=1):
        raise ValueError("Source not uniquely identified")
    result=next(r for r in records if r.get("url")==SOURCE)
    item=next(r for r in captured if r.get("url")==SOURCE)
    digest=result.get("sha256")
    if (result.get("status") not in ("changed_needs_review","unchanged") or
        not isinstance(digest,str) or not HEX.fullmatch(digest) or
        item.get("sha256")!=digest or hash_text(item.get("text",""))!=digest):
        raise ValueError("Official snapshot not valid")
    new=extract(item["text"])
    if new==old:
        return {"changed":False,"changes":[],"old":old,"new":new,"source_sha256":digest,"seo_optimizations":False}
    if amounts_on_related_pages(root,old):
        raise ValueError("Unregistered pages still contain scheme amounts: "+
                         ",".join(amounts_on_related_pages(root,old)))
    # Required anchors in all three current production pages; reject stale site.
    changes=[]
    for rel in PAGES:
        target=(root/rel).resolve()
        if root not in target.parents or not target.is_file() or target.is_symlink():
            raise ValueError("Missing allowlisted page")
        original=target.read_text(encoding="utf-8")
        if len(original)>1_200_000:raise ValueError("Oversized page")
        for val in old:
            if not re.search(rf"(?<!\d){val}(?!\d)",original):
                raise ValueError("Page already diverges from approved baseline: "+rel)
        # Use literal numbers only. May affect text, meta descriptions, factual
        # title and structured FAQ; this is factual consistency, not SEO tuning.
        modified=original
        for index,prev in enumerate(old):
            modified=re.sub(rf"(?<!\d){prev}(?!\d)",str(new[index]),modified)
        modified=re.sub(r'("dateModified"\s*:\s*")[0-9]{4}-[0-9]{2}-[0-9]{2}(")',
                        lambda match:match.group(1)+as_of.isoformat()+match.group(2),modified)
        if protected(original)!=protected(modified):
            raise ValueError("Navigation, canonical or mobile layout changed")
        # No hidden structural changes: every difference is a registered amount.
        replay=original
        for index,prev in enumerate(old):
            replay=re.sub(rf"(?<!\d){prev}(?!\d)",str(new[index]),replay)
        replay=re.sub(r'("dateModified"\s*:\s*")[0-9]{4}-[0-9]{2}-[0-9]{2}(")',
                      lambda match:match.group(1)+as_of.isoformat()+match.group(2),replay)
        if replay!=modified or modified==original:
            raise ValueError("Unsupported page transformation")
        if any(re.search(rf"(?<!\d){prev}(?!\d)",textual(modified)+" "+seo_claims(modified)) for prev in old):
            raise ValueError("Old facts remain in rendered text or schema")
        changes.append({"path":rel,"before_sha256":hash_text(original),"after":modified})
    updated=dict(policy)
    updated["last_published_amounts"]=new
    updated["last_source_sha256"]=digest
    return {"changed":True,"changes":changes,"updated_policy":updated,
            "old":old,"new":new,"source_sha256":digest,
            "seo_optimizations":False,"factual_metadata_consistency":True}

def apply(root,decision,policy_path,write=False):
    if not write or not decision["changed"]:return 0
    root=Path(root).resolve()
    targets=[]
    for edit in decision["changes"]:
        target=(root/edit["path"]).resolve()
        if root not in target.parents or hash_text(target.read_text(encoding="utf-8"))!=edit["before_sha256"]:
            raise ValueError("Target changed since verification: batch cancelled")
        targets.append((target,edit["after"]))
    for target,content in targets:target.write_text(content,encoding="utf-8")
    Path(policy_path).write_text(json.dumps(decision["updated_policy"],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return len(targets)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--policy",type=Path,required=True)
    p.add_argument("--watch-report",type=Path,required=True)
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    data=lambda x:json.loads(x.read_text(encoding="utf-8"))
    result=build(data(a.policy),data(a.watch_report),data(a.snapshots),a.root)
    n=apply(a.root,result,a.policy,a.apply)
    output={k:v for k,v in result.items() if k not in ("changes","updated_policy")}
    output["pages_written"]=n
    output["updated_pages"]=[x["path"] for x in result["changes"]]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Source-verified Catalonia amounts: "+str(output))
if __name__=="__main__":main()
