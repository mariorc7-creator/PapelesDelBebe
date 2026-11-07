#!/usr/bin/env python3
"""Local monthly affiliate brief. Uses only supplied normalised exports.

No network, pricing guesses, analytics account access, publishing or source edits.
Input files must be reviewed independently and stay off GitHub Actions.
"""
import argparse
import importlib.util
import json
from calendar import monthrange
from datetime import date
from pathlib import Path

MODULE = Path(__file__).with_name("superagente_affiliate_performance.py")
spec = importlib.util.spec_from_file_location("superagente_affiliate_performance", MODULE)
performance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(performance)

def build_monthly_brief(month, clicks_csv=None, amazon_csv=None):
    try:
        year, month_num = map(int, month.split("-"))
        start = date(year, month_num, 1)
        end = date(year, month_num, monthrange(year, month_num)[1])
    except (ValueError, TypeError) as exc:
        raise ValueError("Month must be YYYY-MM") from exc
    if month != start.strftime("%Y-%m"):
        raise ValueError("Month must be YYYY-MM")
    report = performance.build_report(clicks_csv, amazon_csv, start.isoformat(), end.isoformat())
    clicks = report["clicks"]
    amazon = report["amazon"]
    sources = report["data_sources"]
    next_actions = []
    if sources["clicks"] is None:
        next_actions.append("Obtener y validar el export de clics de afiliación; no inferirlos de las visitas.")
    if sources["amazon"] is None:
        next_actions.append("Obtener y validar el informe de comisiones de Amazon; no estimar ventas.")
    if sources["clicks"] is not None:
        next_actions.append("Revisar la usabilidad de categorías con clics; no atribuirles pedidos sin evidencia.")
    if sources["amazon"] is not None:
        next_actions.append("Contrastar las comisiones netas con el informe original y posibles devoluciones.")
    return {
        "schema_version": 1,
        "month": month,
        "mode": "offline_review_only",
        "status": "source_validation_required",
        "from": start.isoformat(),
        "to": end.isoformat(),
        "clicks": clicks["total"],
        "clicks_by_category": clicks["by_category"],
        "amazon_ordered_items": amazon["ordered_items"],
        "amazon_shipped_items": amazon["shipped_items"],
        "amazon_commissions_eur": amazon["commissions_eur"],
        "conversion_rate": None,
        "customer_attribution": None,
        "clicks_coverage_days": clicks["days_with_report_rows"],
        "amazon_coverage_days": amazon["days_with_report_rows"],
        "full_month_coverage_confirmed": False,
        "source_files_independently_verified": False,
        "recommendations": next_actions,
        "publication_allowed": False,
        "automatic_website_changes": False,
        "seo_or_mobile_changes": False,
    }

def format_markdown(brief):
    def metric(value, suffix=""):
        return "Sin datos" if value is None else f"{value}{suffix}"
    categories = brief["clicks_by_category"]
    lines = [
        f"# Amazon Afiliados — {brief['month']}",
        "",
        "**Informe interno. Datos de archivos suministrados, origen pendiente de verificar.**",
        "",
        f"- Clics registrados: **{metric(brief['clicks'])}**",
        f"- Artículos pedidos según export: **{metric(brief['amazon_ordered_items'])}**",
        f"- Artículos enviados según export: **{metric(brief['amazon_shipped_items'])}**",
        f"- Comisiones netas según export: **{metric(brief['amazon_commissions_eur'], ' €')}**",
        "- Tasa de conversión: **No calculable sin atribución validada**",
        "",
        "## Categorías con clics",
        ""
    ]
    if categories is None:
        lines.append("Sin export de clics.")
    elif not categories:
        lines.append("No hay clics en las filas del periodo suministradas.")
    else:
        for name, count in categories.items():
            lines.append(f"- {name}: {count} clics")
    lines += [
        "",
        "## Cobertura",
        "",
        f"- Días presentes en el export de clics: {metric(brief['clicks_coverage_days'])}",
        f"- Días presentes en el export de Amazon: {metric(brief['amazon_coverage_days'])}",
        "- No se puede confirmar que los archivos cubran todos los días del mes.",
        "",
        "## Próximas comprobaciones",
        ""
    ]
    lines += [f"- {item}" for item in brief["recommendations"]]
    lines += [
        "",
        "**No hay aprobación para publicar, modificar SEO ni actualizar fechas de revisión.**",
        ""
    ]
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="YYYY-MM")
    parser.add_argument("--clicks-csv", type=Path)
    parser.add_argument("--amazon-csv", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    brief = build_monthly_brief(args.month, args.clicks_csv, args.amazon_csv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"affiliate-monthly-{args.month}.json"
    md_path = args.output_dir / f"affiliate-monthly-{args.month}.md"
    json_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(brief), encoding="utf-8")
    print(f"Two private local monthly reports created for {args.month}; no production changes")

if __name__ == "__main__":
    main()
