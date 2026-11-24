#!/usr/bin/env python3
"""Auditoría estática de todas las páginas HTML de Papeles del Bebé (stdlib)."""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {"papelesdelbebe.es", "www.papelesdelbebe.es"}
IGNORE = {".git", "node_modules", ".vercel", "dist", "build"}
CATEGORIES = {
    "ayudas": ("ayuda-", "ayudas-", "deduccion-", "bono-nacimiento-", "familias-", "complemento-ayuda-", "tarxeta-benvida", "parto-multiple-prestacion", "riesgo-embarazo", "riesgo-lactancia", "cume-"),
    "tramites": ("tarjeta-sanitaria-", "registro-civil-", "empadronar-", "alta-bebe-", "permiso-", "titulo-familia-", "documentos-tramites-", "documentacion-prestacion-", "comunicar-nuevo-hijo-", "certificado-", "autonomos-permiso-"),
}
EXEMPT = {"", "index.html", "404.html"}
# Guides in the latest editorial batch. Keep these checks in future batches.
EDITORIAL_GUARDS = {
    "tarjeta-sanitaria-bebe-baleares/index.html",
    "tarjeta-sanitaria-bebe-cantabria/index.html",
    "tarjeta-sanitaria-bebe-castilla-la-mancha/index.html",
    "tarjeta-sanitaria-bebe-extremadura/index.html",
    "tarjeta-sanitaria-bebe-navarra/index.html",
    "tarjeta-sanitaria-bebe-pais-vasco/index.html",
    "titulo-familia-numerosa-cantabria/index.html",
    "titulo-familia-numerosa-ceuta/index.html",
    "titulo-familia-numerosa-melilla/index.html",
    "titulo-familia-numerosa-pais-vasco/index.html",
}
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.canonicals = []
        self.title = []
        self.h1 = []
        self.descriptions = []
        self.robots = []
        self.mains = []
        self.crumbs = []
        self._title = self._h1 = self._crumb = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link", "script", "img"):
            key = "href" if tag in ("a", "link") else "src"
            if a.get(key):
                self.links.append((tag, a[key]))
        if tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a.get("href", ""))
        if tag == "meta" and a.get("name", "").lower() == "description":
            self.descriptions.append(a.get("content", ""))
        if tag == "meta" and a.get("name", "").lower() == "robots":
            self.robots.append(a.get("content", "").lower())
        if tag == "main":
            self.mains.append(a)
        if tag == "title": self._title = True
        if tag == "h1": self._h1 = True; self.h1.append("")
        if tag == "p" and "pb-crumb" in a.get("class", ""): self._crumb = True; self.crumbs.append("")
    def handle_endtag(self, tag):
        if tag == "title": self._title = False
        if tag == "h1": self._h1 = False
        if tag == "p": self._crumb = False
    def handle_data(self, data):
        if self._title: self.title.append(data)
        if self._h1 and self.h1: self.h1[-1] += data
        if self._crumb and self.crumbs: self.crumbs[-1] += data

def category(slug):
    if slug.startswith("comunidades/"): return "comunidades"
    for kind, prefixes in CATEGORIES.items():
        if slug.startswith(prefixes): return kind
    return None

def local_path(link, source):
    u = urlsplit(link.strip())
    if u.scheme in ("mailto", "tel", "javascript", "data") or link.startswith("#"): return None
    if u.scheme and u.scheme not in ("http", "https"): return None
    if u.netloc and u.hostname not in HOSTS: return None
    if u.netloc or link.startswith("/"): rel = unquote(u.path).lstrip("/")
    else: rel = str((Path(source).parent / unquote(u.path)).as_posix())
    if not rel or rel.endswith("/"): rel += "index.html"
    return rel

def audit(root=ROOT):
    """Audit the deployed artifact, not uncompiled sources.

    The build generates evergreen paths and applies redirects, so examining
    source HTML directly would report genuine generated pages as missing.
    """
    root = Path(root).resolve()
    config_path = (root.parent if root.name == "dist" else root) / "vercel.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    redirects = {}
    for rule in config.get("redirects", []):
        source, target = rule.get("source", ""), rule.get("destination", "")
        if source.startswith("/") and ":" not in source and target.startswith("/"):
            redirects[source.rstrip("/") or "/"] = target
    findings = []
    def flag(level, code, path, detail):
        findings.append({"severity":level, "code":code, "file":str(path), "detail":detail})
    pages = sorted(p for p in root.rglob("*.html") if not any(x in IGNORE for x in p.relative_to(root).parts))
    actual = {p.relative_to(root).as_posix(): p for p in pages}
    sitemap = root / "sitemap.xml"
    listed = set()
    if sitemap.exists():
        try:
            xml_root = ElementTree.parse(sitemap).getroot()
            for e in xml_root.iter():
                if e.tag.endswith("loc") and e.text:
                    path = local_path(e.text, "sitemap.xml")
                    if path: listed.add(path)
        except ElementTree.ParseError as exc: flag("error","INVALID_SITEMAP","sitemap.xml",str(exc))
    else: flag("error","MISSING_SITEMAP","sitemap.xml","No existe sitemap")
    for path in sorted(listed - set(actual)):
        flag("error","SITEMAP_404",path,"La URL del sitemap no tiene index.html")
    for path in sorted(set(actual) - listed):
        slug = "/" + path.removesuffix("index.html").rstrip("/")
        html = actual[path].read_text(encoding="utf-8", errors="replace")
        is_noindex = bool(re.search(r'<meta\\b[^>]*content=["\\x27][^"\\x27]*noindex', html, re.I))
        if path not in EXEMPT and not path.startswith("404") and slug not in redirects and not is_noindex:
            flag("warning","NOT_IN_SITEMAP",path,"Página HTML pública ausente del sitemap")
    inbound = Counter()
    for rel, file in actual.items():
        content = file.read_text(encoding="utf-8", errors="replace")
        p = Page()
        try: p.feed(content)
        except Exception as exc: flag("error","HTML_PARSE",rel,str(exc)); continue
        if not p.title or not "".join(p.title).strip(): flag("error","NO_TITLE",rel,"Falta title")
        if len(p.h1) != 1: flag("warning","H1_COUNT",rel,f"{len(p.h1)} encabezados H1")
        if len(p.descriptions) != 1: flag("warning","META_DESCRIPTION",rel,f"{len(p.descriptions)} metadescripciones")
        redirecting = ("/" + rel.removesuffix("index.html").rstrip("/")) in redirects
        indexable = rel in listed and not any("noindex" in rule for rule in p.robots)
        if indexable and len(p.canonicals) != 1: flag("warning","CANONICAL_COUNT",rel,f"{len(p.canonicals)} canonical")
        elif indexable and local_path(p.canonicals[0],rel) != rel: flag("error","CANONICAL_MISMATCH",rel,p.canonicals[0])
        if len(p.crumbs) > 1: flag("warning","MULTIPLE_BREADCRUMBS",rel,str(len(p.crumbs)))
        if content.count("Última revisión") > 1: flag("warning","DUPLICATE_REVIEW",rel,"Fecha de revisión repetida")
        if rel in EDITORIAL_GUARDS:
            main_match = re.search(r"<main\b[^>]*>([\s\S]*?)</main>", content, re.I)
            main_html = main_match.group(1) if main_match else ""
            editorial_dates = re.findall(r'<p\b[^>]*class="[^"]*revision-sitio[^"]*"[^>]*>\s*Última revisión:.*?</p>', main_html, re.I | re.S)
            legacy_labels = re.findall(r"Revisado (?:el|:)\s*\d{1,2}/\d{1,2}/\d{4}", main_html, re.I)
            if len(editorial_dates) != 1 or legacy_labels:
                flag("error", "REVIEW_DATE_DUPLICATE", rel, f"{len(editorial_dates)} revisión editorial; {len(legacy_labels)} fechas antiguas")
            elif not main_html.rstrip().endswith(editorial_dates[0]):
                flag("error", "CONTENT_AFTER_REVIEW_DATE", rel, "La revisión debe ser el último elemento dentro de main")
            if "Resolver incidencias y preparar el trámite" in content:
                flag("error", "EDITORIAL_OUTSIDE_TEMPLATE", rel, "Ampliación separada del cuerpo editorial")
            if len(p.h1) != 1 or len(p.canonicals) != 1 or len(p.descriptions) != 1:
                flag("error", "EDITORIAL_SEO_INTEGRITY", rel, "Debe conservar H1, canonical y meta description únicos")
        slug = rel.removesuffix("index.html")
        kind = category(slug)
        if p.mains and not p.mains[0].get("class"):
            declared = p.mains[0].get("data-page-kind")
            if declared and kind in ("ayudas","tramites") and declared not in (kind, "tramite" if kind == "tramites" else kind):
                flag("error","WRONG_CATEGORY",rel,f"data-page-kind={declared}, esperado {kind}")
            if kind == "ayudas" and p.crumbs and "Guías" in p.crumbs[0]:
                flag("error","WRONG_BREADCRUMB",rel,"Ayuda clasificada como Guías")
            if kind == "tramites" and p.crumbs and "Ayudas" in p.crumbs[0]:
                flag("error","WRONG_BREADCRUMB",rel,"Trámite clasificado como Ayudas")
        for tag, link in p.links:
            target = local_path(link, rel)
            if target is None: continue
            if target.startswith("../") or target.startswith("/"):
                flag("warning","OUTSIDE_ROOT",rel,link); continue
            path_key = "/" + target.removesuffix("index.html").rstrip("/")
            final_target = target
            seen = set()
            while path_key in redirects and path_key not in seen:
                seen.add(path_key)
                redirected = redirects[path_key]
                resolved = local_path(redirected, rel)
                if not resolved: break
                final_target = resolved
                path_key = "/" + final_target.removesuffix("index.html").rstrip("/")
            if final_target in actual:
                if tag == "a" and indexable and final_target != rel: inbound[final_target] += 1
            elif not (root / final_target).is_file():
                flag("error","BROKEN_INTERNAL_LINK",rel,f"{tag}: {link} → {final_target}")
    # Localiza páginas públicas que carecen de enlaces HTML entrantes.
    for rel in sorted(listed & set(actual)):
        if rel != "index.html" and inbound[rel] == 0:
            flag("warning", "ORPHAN_PAGE", rel, "No tiene enlaces internos entrantes; comprobar navegación y hubs temáticos")
    return pages, listed, findings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict",action="store_true",help="Fallará si hay errores")
    ap.add_argument("--root",type=Path,default=ROOT,help="Directorio compilado (dist) a auditar")
    ap.add_argument("--report",default="site-audit-report.json")
    args = ap.parse_args()
    pages,listed,issues = audit(args.root)
    counts = Counter(i["severity"] for i in issues)
    report = {"html_pages":len(pages),"sitemap_urls":len(listed),"counts":dict(counts),"findings":issues}
    (ROOT/args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Auditadas {len(pages)} páginas HTML; sitemap: {len(listed)} URLs; errores: {counts['error']}; avisos: {counts['warning']}")
    for i in issues[:100]: print(f"[{i['severity']}] {i['code']}: {i['file']} — {i['detail']}")
    if len(issues)>100: print(f"... y {len(issues)-100} incidencias adicionales en {args.report}")
    if args.strict and counts["error"]: raise SystemExit(1)
if __name__ == "__main__": main()
