#!/usr/bin/env python3
"""SuperAgente: evidence-gated automatic content updates in a batch branch.

Applies explicit, independently reviewed factual edits to HTML, preserving
canonical, title, navigation, viewport, CSS, script and existing anchors.
A verified 'no change' may only update the review date, never dateModified.
Does not research facts, interpret legal documents, commit, merge or deploy.
"""
import argparse
from datetime import date
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ALLOWED = {"change", "review_only"}
REVIEW_TEXT = re.compile(r'(Información revisada: |Última revisión: )(?:\d{1,2} de [a-záéíóú]+ de \d{4})',re.I)
REVIEW_TIME = re.compile(r'(Última revisión:\s*<time datetime=")(\d{4}-\d{2}-\d{2})(">)([^<]+)(</time>)',re.I)
MONTHS = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]

def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

class Tags(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.tags={}
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        self.tags[tag]=self.tags.get(tag,0)+1
        if d.get("id"): self.ids.append(d["id"])

def guard(before, after, path):
    # Structural invariants can neither be waived by a reviewer nor bypassed.
    checks = [
        r'<title\b[^>]*>.*?</title>',
        r'<meta\b(?=[^>]*name=["\x27]robots["\x27])[^>]*>',
        r'<meta\b(?=[^>]*name=["\x27]viewport["\x27])[^>]*>',
        r'<link\b(?=[^>]*rel=["\x27]canonical["\x27])[^>]*>',
        r'<link\b[^>]*rel=["\x27]stylesheet["\x27][^>]*>',
    ]
    for pattern in checks:
        old=re.findall(pattern,before,re.I|re.S); new=re.findall(pattern,after,re.I|re.S)
        if old!=new or (not old and "canonical" in pattern):
            raise ValueError(f"{path}: changed protected SEO metadata")
    for marker in (r'<header\b',r'</header>',r'<nav\b',r'</nav>',r'<main\b',r'</main>',r'<footer\b',r'</footer>',r'<script\b',r'</script>'):
        if len(re.findall(marker,before,re.I))!=len(re.findall(marker,after,re.I)):
            raise ValueError(f"{path}: changed site structure")
    old=Tags();old.feed(before);new=Tags();new.feed(after)
    if (old.ids!=new.ids or len(new.ids)!=len(set(new.ids)) or
        old.tags.get("h1")!=new.tags.get("h1") or new.tags.get("h1")!=1):
        raise ValueError(f"{path}: changed anchors or H1")
    for tag in ("a","button","form","input","select","textarea","style"):
        if old.tags.get(tag,0)!=new.tags.get(tag,0):
            raise ValueError(f"{path}: changed interactive structure")

def check_manifest(root, manifest):
    if not isinstance(manifest,dict) or manifest.get("schema_version")!=1:
        raise ValueError("Invalid manifest")
    if manifest.get("status")!="editorially_verified_for_branch_only":
        raise ValueError("Independent editorial verification is required")
    if manifest.get("publication_allowed") is not False:
        raise ValueError("This step must not authorize publication")
    changes=manifest.get("changes")
    if not isinstance(changes,list) or not changes or len(changes)>100:
        raise ValueError("Requires 1..100 reviewed actions")
    staged={}
    for item in changes:
        if not isinstance(item,dict) or item.get("action") not in ALLOWED:
            raise ValueError("Invalid change action")
        path=item.get("path")
        if not isinstance(path,str):
            raise ValueError("Missing page path")
        rel=Path(path)
        target=(root/rel).resolve()
        if (rel.is_absolute() or ".." in rel.parts or root not in target.parents or
            not path.endswith("/index.html") or not target.is_file() or target.is_symlink()):
            raise ValueError("Unsafe page path")
        if path in staged:
            raise ValueError("Duplicate page")
        original=target.read_text(encoding="utf-8")
        if item.get("original_sha256")!=digest(original):
            raise ValueError(f"{path}: stale snapshot; review again")
        source=item.get("official_source_url")
        parts=urlsplit(source) if isinstance(source,str) else None
        if not parts or parts.scheme!="https" or not parts.hostname or parts.username or parts.password:
            raise ValueError("Verified official HTTPS source required")
        if (item.get("independent_source_verification") is not True or
                item.get("editorial_approval") is not True or
                not isinstance(item.get("reviewer"),str) or not item["reviewer"].strip() or
                not isinstance(item.get("evidence_ref"),str) or not item["evidence_ref"].strip()):
            raise ValueError("Missing independent evidence and editorial approval")
        stamp=item.get("review_date")
        try: day=date.fromisoformat(stamp)
        except (ValueError,TypeError): raise ValueError("Bad review date") from None
        if day.isoformat()!=stamp or day>date.today():
            raise ValueError("Review date must be valid and not in future")
        display=f"{day.day} de {MONTHS[day.month-1]} de {day.year}"
        changed=original
        if item["action"]=="change":
            search=item.get("search");replacement=item.get("replacement")
            if not isinstance(search,str) or not search.strip() or not isinstance(replacement,str) or not replacement.strip():
                raise ValueError("Missing exact edit")
            if original.count(search)!=1 or search==replacement:
                raise ValueError("Stale or nonunique content anchor")
            if any(char in text for text in (search,replacement) for char in "<>"):
                raise ValueError("Only plain-text edits are allowed; HTML changes need separate review")
            changed=changed.replace(search,replacement,1)
            changed=re.sub(r'("dateModified"\s*:\s*")\d{4}-\d{2}-\d{2}(")',lambda m:m.group(1)+stamp+m.group(2),changed)
        else:
            if "search" in item or "replacement" in item:
                raise ValueError("Review-only cannot edit content")
            if item.get("unchanged_confirmed") is not True:
                raise ValueError("Review-only requires confirmed unchanged facts")
        # Preserve the existing markup and only modify review-date tokens.
        changed=REVIEW_TEXT.sub(lambda m:m.group(1)+display,changed)
        changed=REVIEW_TIME.sub(lambda m:m.group(1)+stamp+m.group(3)+display+m.group(5),changed)
        guard(original,changed,path)
        if changed==original:
            raise ValueError("No review date field or content changed; do not claim update")
        staged[path]={"old_sha256":digest(original),"new_sha256":digest(changed),
                      "action":item["action"],"official_source_url":source,
                      "review_date":stamp,"evidence_ref":item["evidence_ref"],
                      "content":changed}
    return staged

def run(root, manifest, apply=False):
    root=Path(root).resolve()
    staged=check_manifest(root,manifest)
    # All checks have passed before ANY file mutation.
    if apply:
        for path,item in staged.items():
            target=root/path
            # Protect against modifications between validation and writing.
            if digest(target.read_text(encoding="utf-8"))!=item["old_sha256"]:
                raise ValueError("Concurrent change; retry with fresh manifest")
        for path,item in staged.items():
            (root/path).write_text(item["content"],encoding="utf-8")
    return {"schema_version":1,"mode":"branch_content_changes" if apply else "dry_run",
            "count":len(staged),"files":[{"path":k,**{x:y for x,y in v.items() if x!="content"}} for k,v in staged.items()],
            "production_changed":False,"publishing_authorized":False,
            "notice":"Official factual verification is a separately attested editorial prerequisite; not machine-proven."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--apply",action="store_true")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    data=json.loads(args.manifest.read_text(encoding="utf-8"))
    result=run(args.root,data,args.apply)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{result['mode']}: {result['count']} reviewed pages; no publication")
if __name__=="__main__":
    main()
