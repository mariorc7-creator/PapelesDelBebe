#!/usr/bin/env python3
"""Turn static Amazon link-audit evidence into a non-publishable review queue.

This module only consumes audit JSON. It never changes website HTML, guesses
traffic/conversions, requests Amazon APIs, or deploys. Every recommendation is
traceable to an actual source finding or explicitly marked as data-unavailable.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

SEVERITY = {
    "unapproved_destination": (0, "critical", "Revisar dominio: podría no ser Amazon España"),
    "invalid_url": (0, "critical", "Comprobar URL inválida"),
    "missing_affiliate_tag": (1, "high", "Comprobar identificador de afiliación"),
    "unexpected_affiliate_tag": (1, "high", "Comprobar identificador de afiliación diferente"),
    "non_https": (1, "high", "Usar conexión segura si el enlace es válido"),
    "no_affiliate_disclosure_found": (2, "medium", "Verificar aviso publicitario visible"),
    "missing_sponsored_or_nofollow": (2, "medium", "Comprobar atributo rel del enlace de afiliado"),
}

def make_queue(audit):
    if audit.get("schema_version") != 1 or audit.get("mode") != "read_only":
        raise ValueError("Se requiere un informe de auditoría de solo lectura v1")
    if audit.get("publication_allowed") is not False:
        raise ValueError("La auditoría no puede autorizar publicaciones")
    findings = audit.get("issues")
    if not isinstance(findings, list):
        raise ValueError("Lista de incidencias ausente o inválida")
    grouped = {}
    for item in findings:
        if not isinstance(item, dict):
            raise ValueError("Incidencia inválida")
        page = item.get("page")
        url = item.get("url")
        issues = item.get("issues")
        if not isinstance(page, str) or not page or not isinstance(url, str) or not url:
            raise ValueError("Incidencia sin página o URL")
        if not isinstance(issues, list) or not issues:
            raise ValueError("Incidencia sin códigos")
        for code in issues:
            if code not in SEVERITY:
                raise ValueError(f"Código no reconocido: {code}")
        key = (page, url)
        grouped.setdefault(key, set()).update(issues)
    queue = []
    for (page, url), codes in grouped.items():
        ordered = sorted(codes, key=lambda code: (SEVERITY[code][0], code))
        severity_rank, priority, _ = SEVERITY[ordered[0]]
        queue.append({
            "page": page,
            "url": url,
            "priority": priority,
            "priority_rank": severity_rank,
            "finding_codes": ordered,
            "editorial_actions": [SEVERITY[code][2] for code in ordered],
            "status": "pending_human_review",
            "automated_fix_allowed": False
        })
    queue.sort(key=lambda item: (item["priority_rank"], item["page"], item["url"]))
    counts = Counter(item["priority"] for item in queue)
    return {
        "schema_version": 1,
        "mode": "proposal_only",
        "source": "static_amazon_affiliate_audit",
        "publication_allowed": False,
        "automatic_rewrites": False,
        "requires_human_approval": True,
        "total_review_items": len(queue),
        "priority_counts": {key: counts.get(key, 0) for key in ("critical", "high", "medium")},
        "queue": queue,
        "growth_opportunities": {
            "status": "not_assessed_without_verified_analytics",
            "amazon_clicks": None,
            "attributed_orders": None,
            "conversion_rate": None,
            "commission_revenue": None,
            "next_step": "Conectar únicamente datos autorizados de clics y reportes oficiales de Amazon; nunca inventar ventas ni ingresos."
        },
        "seo_safety": {
            "rewrite_indexed_html": False,
            "change_urls_canonicals_or_sitemaps": False,
            "change_review_dates": False,
            "require_mobile_and_seo_checks_before_release": True
        }
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    plan = make_queue(audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Amazon review queue: {plan['total_review_items']} items; no publishing or rewrites")

if __name__ == "__main__":
    main()
