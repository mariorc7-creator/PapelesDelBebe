#!/usr/bin/env python3
"""Read-only editorial decision plan from monthly affiliate reports.

Not a sales attribution model. Makes *review tasks*, never writes to the site.
Missing or unverified source data never triggers revenue-optimisation claims.
"""
import argparse
import json
from pathlib import Path

def _integer_or_none(value):
    return value is None or (type(value) is int and value >= 0)

def _validate(report):
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ValueError("Unsupported monthly report")
    if report.get("mode") != "offline_review_only":
        raise ValueError("Monthly report is not review-only")
    if report.get("publication_allowed") is not False:
        raise ValueError("Monthly report cannot authorize publishing")
    if report.get("automatic_website_changes") is not False:
        raise ValueError("Monthly report cannot authorize website changes")
    month = report.get("month")
    if not isinstance(month, str) or len(month) != 7 or month[4] != "-":
        raise ValueError("Month must be YYYY-MM")
    for key in ("clicks", "amazon_ordered_items", "amazon_shipped_items", "clicks_coverage_days", "amazon_coverage_days"):
        if not _integer_or_none(report.get(key)):
            raise ValueError(f"Bad numeric field: {key}")
    if report.get("conversion_rate") is not None or report.get("customer_attribution") is not None:
        raise ValueError("Refuse unsupported affiliate attribution")
    categories = report.get("clicks_by_category")
    if categories is not None:
        if not isinstance(categories, dict) or any(not isinstance(k, str) or not k or not _integer_or_none(v) or v is None for k, v in categories.items()):
            raise ValueError("Invalid category click totals")
        if report.get("clicks") is None or sum(categories.values()) != report["clicks"]:
            raise ValueError("Category clicks must sum to overall clicks")
    elif report.get("clicks") is not None:
        raise ValueError("Missing category detail")
    if report.get("source_files_independently_verified") not in (True, False):
        raise ValueError("Missing provenance status")
    return report

def build_decisions(report):
    report = _validate(report)
    tasks = []
    def add(id_, priority, title, rationale, evidence, gate):
        tasks.append({
            "id": id_, "priority": priority, "title": title,
            "reason": rationale, "evidence": evidence,
            "approval_gate": gate,
            "status": "proposal_only", "website_changes_allowed": False
        })

    clicks = report.get("clicks")
    commissions = report.get("amazon_commissions_eur")
    confirmed = report["source_files_independently_verified"] is True
    if not confirmed:
        add("verify-source-exports", 0, "Verificar procedencia y cobertura de los CSV",
            "Los archivos normalizados no certifican por sí solos su origen, periodo ni integridad.",
            {"source_files_independently_verified": False},
            "Confirmación manual de procedencia, columnas y periodo")
    if clicks is None:
        add("obtain-clicks", 1, "Obtener clics reales del periodo",
            "No hay datos de clics; no se deben inferir de visitas ni impresiones.",
            {"clicks": None}, "Export válido de eventos de afiliación")
    if commissions is None:
        add("obtain-amazon-report", 1, "Obtener comisiones de Amazon",
            "No se dispone de cifras de ventas/comisiones del periodo.",
            {"commissions_eur": None}, "Informe oficial validado")
    if clicks is not None and clicks > 0:
        categories = sorted(report["clicks_by_category"].items(), key=lambda item: (-item[1], item[0]))
        for name, value in categories[:3]:
            if value <= 0:
                continue
            add("review-category-" + name, 2, f"Revisar la experiencia de compra: {name}",
                "La categoría registra clics, pero eso no demuestra ventas ni rentabilidad.",
                {"category": name, "observed_clicks": value, "data_verified": confirmed},
                "Revisión editorial, usabilidad móvil y pruebas SEO antes de editar")
    if clicks == 0 and confirmed:
        add("inspect-zero-clicks", 2, "Revisar medición y visibilidad de enlaces",
            "El export validado declara cero clics: confirmar implementación y cobertura antes de interpretar.",
            {"observed_clicks": 0},
            "Comprobar instrumentación y rango temporal")
    if commissions is not None:
        add("reconcile-amazon", 2, "Conciliar comisiones y devoluciones",
            "La comisión agregada no demuestra qué página o recomendación produjo el pedido.",
            {"net_commissions_eur_from_supplied_export": commissions, "data_verified": confirmed},
            "Revisión humana del informe original y devoluciones")
    tasks.sort(key=lambda t:(t["priority"], -(t["evidence"].get("observed_clicks", 0)), t["id"]))
    return {
        "schema_version": 1,
        "month": report["month"],
        "mode": "review_only",
        "data_status": "verified_by_editor" if confirmed else "unverified_export",
        "tasks": tasks,
        "task_count": len(tasks),
        "monetization_claims_allowed": False,
        "affiliate_attribution_available": False,
        "publication_allowed": False,
        "automatic_website_changes": False,
        "seo_ux_protection": {
            "modify_indexed_content": False,
            "modify_canonical_or_sitemap": False,
            "modify_review_dates": False,
            "require_mobile_seo_regression_tests": True
        }
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--monthly-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = build_decisions(json.loads(args.monthly_json.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {plan['task_count']} proposed editorial tasks, no website changes")

if __name__ == "__main__":
    main()
