"""Immutable SEO, design and navigation guard for official status micro-edits."""
import re
from html.parser import HTMLParser

class Fingerprint(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements=[]
    def handle_starttag(self,tag,attrs):
        self.elements.append((tag,tuple(sorted(attrs))))
    def handle_startendtag(self,tag,attrs):
        self.elements.append((tag,tuple(sorted(attrs))))
    def handle_endtag(self,tag):
        self.elements.append(("/"+tag,()))

def guard_html(before,after):
    if before==after:raise ValueError("No meaningful content edit")
    for start,end in (("<head","</head>"),("<header","</header>"),("<footer","</footer>")):
        pattern=re.compile(re.escape(start)+r"\b.*?"+re.escape(end),re.I|re.S)
        if (re.findall(pattern,before)!=re.findall(pattern,after) or
            not re.findall(pattern,before)):
            raise ValueError("SEO, site layout, header or footer altered")
    # Marker controls and class/name attributes must be untouched.
    old=Fingerprint();old.feed(before)
    new=Fingerprint();new.feed(after)
    if old.elements!=new.elements:
        raise ValueError("HTML tags, anchors or CSS hooks altered")
    for protected in ("<title","canonical","robots","viewport","dateModified","<h1","<nav","<script","<style"):
        if before.count(protected)!=after.count(protected):
            raise ValueError("Protected SEO structure altered")
    # Preserve exact content outside the single managed span.
    sm="<!-- superagente:extremadura-2026:start -->"
    em="<!-- superagente:extremadura-2026:end -->"
    if before.count(sm)!=1 or after.count(sm)!=1 or before.count(em)!=1 or after.count(em)!=1:
        raise ValueError("Missing or duplicated managed area")
    bp,bs=before.split(sm,1);ap,ass=after.split(sm,1)
    _,bt=bs.split(em,1);_,at=ass.split(em,1)
    if bp!=ap or bt!=at:
        raise ValueError("An unrelated part of the guide changed")
