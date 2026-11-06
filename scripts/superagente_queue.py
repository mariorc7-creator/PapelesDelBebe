#!/usr/bin/env python3
"""Generate an editorial priority queue; not a legal validation engine."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
urls = sorted({x.text.strip() for x in ET.parse(ROOT / "sitemap.xml").getroot().findall(".//{*}loc") if x.text})
reviews = ROOT / "superagente/reviews.json"
registry = json.loads(reviews.read_text(encoding="utf-8")) if reviews.exists() else {"pages": {}}
items = []
for url in urls:
    path = urlparse(url).path
    entry = registry.get("pages", {}).get(url, {})
    if path == "/":
        category = "home"
    elif "ayuda" in path or "deduccion" in path or "bono" in path:
        category = "ayudas"
    elif "tramite" in path or any(x in path for x in ("registro-civil", "seguridad-social", "empadronar", "tarjeta-sanitaria")):
        category = "tramites"
    elif "herramientas" in path:
        category = "herramientas"
    else:
        category = "otras"
    priority = {"ayudas": 1, "tramites": 2, "herramientas": 3, "otras": 4, "home": 5}[category]
    if entry.get("status") == "changed": priority = 0
    items.append({
        "url": url, "category": category, "priority": priority,
        "review_status": entry.get("status", "not_verified"),
        "last_reviewed": entry.get("last_reviewed"),
        "action": "verify_official_sources" if entry.get("status") not in ("unchanged", "changed") else "review_existing_evidence",
    })
items.sort(key=lambda x: (x["priority"], x["last_reviewed"] or "", x["url"]))
out = ROOT / "superagente/editorial-queue.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"warning": "Priority is heuristic; no legal validity inferred.", "total": len(items), "items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Generated editorial queue with {len(items)} URLs")
