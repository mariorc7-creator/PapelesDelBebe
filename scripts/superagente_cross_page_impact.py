#!/usr/bin/env python3
"""Site-wide legal change impact analyzer for official benefits.

The same benefit is commonly mentioned in multiple guides and FAQ pages.
A change must not publish if *any* affected page has an unedited, conflicting
fact. Scan existing local HTML only; do not use fuzzy claims as an excuse to
modify files. All findings are read-only and need an exact-source fact record.

Supports generic policy-defined scope and multiple affected pages. Does not
pretend to decide legal applicability; never edits or deploys.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

IGNORED={"script","style","template","noscript","header","footer","nav"}
MAX_FILES=15000
MAX_FILE_BYTES=1_200_000

class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in IGNORED:self.skip+=1
    def handle_endtag(self,tag):
        if tag in IGNORED and self.skip:self.skip-=1
    def handle_data(self,text):
        if not self.skip:self.parts.append(text)

def textual(html):
    p=Visible();p.feed(html)
    return " ".join(" ".join(p.parts).split())

class SEOFacts(HTMLParser):
    """Collect searchable claims in descriptions and JSON-LD, without edits."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.jsonld=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="meta" and (a.get("name","").lower()=="description" or
                            a.get("property","").lower() in ("og:description","twitter:description")):
            self.parts.append(a.get("content",""))
        if tag=="script" and a.get("type","").lower()=="application/ld+json":
            self.jsonld=True
    def handle_endtag(self,tag):
        if tag=="script":self.jsonld=False
    def handle_data(self,text):
        if self.jsonld:self.parts.append(text)

def seo_claims(html):
    reader=SEOFacts();reader.feed(html)
    return " ".join(" ".join(reader.parts).split())


def strict_terms(values,name):
    if not isinstance(values,list) or not 1<=len(values)<=12:
        raise ValueError("Missing "+name)
    if any(not isinstance(x,str) or not 3<=len(x.strip())<=120 or any(c in x for c in "<>{}") for x in values):
        raise ValueError("Unsafe "+name)
    return values

def impacted(root,policy,changed_files=()):
    """Find every local site page with an allowlisted benefit's old legal claim.

    A page can be safely ignored only if it contains neither the explicit
    benefit+territory identity nor a direct official link and old claim.
    This is deliberately conservative; false positive review is safer.
    """
    root=Path(root).resolve()
    if policy.get("schema_version")!=1 or policy.get("publication_allowed") is not False:
        raise ValueError("Unreviewed impact scope")
    rules=policy.get("benefits")
    if not isinstance(rules,list) or not 1<=len(rules)<=30:
        raise ValueError("Invalid benefit mapping")
    candidates=list(root.rglob("index.html"))
    if len(candidates)>MAX_FILES:
        raise ValueError("Too many pages, use batching")
    changed=set(changed_files)
    findings=[]
    for rule in rules:
        code=rule.get("id")
        if not isinstance(code,str) or not re.fullmatch(r"[a-z0-9-]{4,80}",code):
            raise ValueError("Invalid benefit key")
        source=rule.get("official_source_url")
        if not isinstance(source,str) or urlsplit(source).scheme!="https" or not urlsplit(source).hostname:
            raise ValueError("Invalid official source")
        territory=strict_terms(rule.get("territory_tokens"),"territory tokens")
        benefit=strict_terms(rule.get("benefit_tokens"),"benefit tokens")
        prior=strict_terms(rule.get("old_claim_tokens"),"old claim tokens")
        affected=[]
        for path in candidates:
            if path.is_symlink() or path.stat().st_size>MAX_FILE_BYTES:
                continue
            rel=path.relative_to(root).as_posix()
            if rel.startswith((".git/","dist/","node_modules/","vendor/")):
                continue
            html=path.read_text(encoding="utf-8")
            content=textual(html).casefold()
            # Official source mentions alone can occur in global references.
            # Require territory and benefit, then a claim token or official link.
            is_topic=(any(x.casefold() in content for x in territory) and
                      any(x.casefold() in content for x in benefit))
            metadata=seo_claims(html).casefold()
            is_claim=any(x.casefold() in content for x in prior)
            metadata_claim=any(x.casefold() in metadata for x in prior)
            if not (is_topic and (is_claim or metadata_claim or source in html)):
                continue
            context=[]
            for token in prior:
                offset=content.find(token.casefold())
                if offset>=0:
                    context.append(content[max(0,offset-80):offset+len(token)+110])
            affected.append({"path":rel,"contains_old_claim":is_claim,
                             "direct_official_link":source in html,
                             "seo_metadata_contains_old_claim":metadata_claim,
                             "sample_context":context[:3],
                             "covered_by_batch":rel in changed})
        missing=[x["path"] for x in affected if x["contains_old_claim"] or x["seo_metadata_contains_old_claim"]]
        # Even a changed page is unsafe if any old claim remains elsewhere
        # within that page (FAQ, second paragraph, callout, etc.).
        findings.append({"benefit_id":code,"official_source_url":source,
                         "references":affected,"uncovered_old_claims":missing,
                         "ready_for_auto_publication":not missing and bool(affected) and bool(changed)})
    return {"schema_version":1,"mode":"sitewide_legal_impact",
            "findings":findings,
            "ready_for_auto_publication":all(x["ready_for_auto_publication"] for x in findings),
            "automatic_legal_truth_established":False,
            "seo_modified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--policy",type=Path,required=True)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--changed-file",action="append",default=[])
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=impacted(a.root,json.loads(a.policy.read_text(encoding="utf-8")),a.changed_file)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Impact audit: {sum(len(x['references']) for x in result['findings'])} pages referenced; "
          f"{sum(len(x['uncovered_old_claims']) for x in result['findings'])} uncovered old-claim pages; "
          f"auto publish: {result['ready_for_auto_publication']}")
if __name__=="__main__":main()
