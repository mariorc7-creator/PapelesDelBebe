#!/usr/bin/env python3
"""SuperAgente V1 integration: offline orchestration, no content mutation.

Inputs: optional Amazon static audit, optional private monthly affiliate report,
optional manually evidenced proposals, local decision history, staging safety report.
Produces a single prioritized *review* queue, an executive summary and gate status.
Never uses remote analytics, publishing APIs, cron, or unauthorised services.
"""
import argparse
from datetime import date
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent

def load_module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

memory = load_module("superagente_decision_memory")
amazon = load_module("superagente_amazon_queue")
affiliate = load_module("superagente_affiliate_decisions")

def read_json(path):
    if path is None:
        return None
    path = Path(path)
    if path.stat().st_size > 3_000_000:
        raise ValueError("Input report too large")
    return json.loads(path.read_text(encoding="utf-8"))

def safe_id(prefix, value):
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (prefix + "-" + normalized[:72]).strip("-") or prefix

def proposal(id_, title, category, evidence, risk="low", urgency="medium",
             impact=None, basis="unknown", hours="1", cost="0"):
    return {
        "id": id_, "title": title, "category": category, "evidence_ref": evidence,
        "seo_risk": risk, "urgency": urgency, "impact_basis": basis,
        "expected_monthly_benefit_eur": impact,
        "cost_eur": cost, "effort_hours": hours
    }

def merge_proposals(explicit, static_audit, monthly, history):
    candidates = []
    if explicit is not None:
        if not isinstance(explicit, list):
            raise ValueError("Proposals must be JSON array")
        candidates += explicit
    if static_audit is not None:
        reviewed = amazon.make_queue(static_audit)
        for item in reviewed["queue"]:
            critical = item["priority"] == "critical"
            candidates.append(proposal(
                safe_id("amazon-audit", item["page"] + "-" + item["url"]),
                "Comprobar enlace de Amazon: " + item["page"],
                "technical", "amazon-static-audit:" + item["page"],
                risk="high" if critical else "low",
                urgency="high" if critical else "medium",
                hours="1"
            ))
    if monthly is not None:
        derived = affiliate.build_decisions(monthly)
        for item in derived["tasks"]:
            name = item["id"]
            risk = "medium" if name.startswith("review-category-") else "low"
            candidates.append(proposal(
                safe_id("affiliate", monthly["month"] + "-" + name),
                item["title"], "affiliate",
                "affiliate-monthly:" + monthly["month"] + ":" + name,
                risk=risk,
                urgency="high" if item["priority"] == 0 else "medium",
                hours="1"
            ))
    # Reject true ID collisions, instead of losing or overwriting a task.
    ids = [c.get("id") for c in candidates if isinstance(c, dict)]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate task id across sources")
    return memory.priority_plan(candidates, history)

def build_integrated_plan(*, proposals=None, amazon_audit=None,
                          affiliate_monthly=None, history=None,
                          staging_report=None, budget_eur=None):
    history = history if history is not None else []
    plan = merge_proposals(proposals, amazon_audit, affiliate_monthly, history)
    budget = memory.estimate(budget_eur) if budget_eur is not None else None
    staging = staging_report or {}
    if staging and (not isinstance(staging, dict) or staging.get("environment") != "vercel_preview_not_production"):
        raise ValueError("Unexpected staging safety report")
    rollback_verified = staging.get("rollback", {}).get("vercel_rollback_verified") if staging else None
    not_ready = staging and rollback_verified is not True
    pending = [x for x in plan["items"] if x["status"] == "proposed_for_editorial_review"]
    held = [x for x in plan["items"] if x["status"] != "proposed_for_editorial_review"]
    estimated_cost = sum((memory.estimate(x["estimated_cost_eur"]) for x in plan["items"]), memory.Decimal("0"))
    budget_exceeded = bool(budget is not None and estimated_cost > budget)
    gates = {
        "automation_enabled": False,
        "publish_to_production_allowed": False,
        "seo_mobile_qa_required": True,
        "editorial_approval_required": True,
        "rollback_verified_in_remote_preview": rollback_verified,
        "staging_requires_reverification": bool(not_ready),
        "budget_provided": budget is not None,
        "estimated_total_work_cost_eur": str(estimated_cost),
        "budget_eur": str(budget) if budget is not None else None,
        "candidate_cost_exceeds_budget": budget_exceeded if budget is not None else None,
        "missing_affiliate_revenue_data": affiliate_monthly is None or affiliate_monthly.get("amazon_commissions_eur") is None,
        "known_blockers": (["Reconfirm remote Vercel staging rollback before any release"] if not_ready else [])
         + (["Estimate exceeds supplied budget"] if budget_exceeded else []),
    }
    if affiliate_monthly:
        gates["affiliate_figures_verified"] = affiliate_monthly["source_files_independently_verified"] is True
    else:
        gates["affiliate_figures_verified"] = False
    return {
        "schema_version": 1, "mode": "offline_integrated_review",
        "summary": {
            "total_tasks": plan["candidate_count"],
            "editorial_review": len(pending),
            "held_for_risk_review": len(held),
            "source_modules": {
                "explicit": proposals is not None,
                "amazon_audit": amazon_audit is not None,
                "affiliate_monthly": affiliate_monthly is not None,
                "decision_memory": True,
                "staging_report": bool(staging),
            }
        },
        "priorities": plan["items"],
        "decision_history_sha256": plan["history_sha256"],
        "gates": gates,
        "no_live_data_or_revenue_inferred": True,
        "production_changed": False,
        "requires_human_review": True,
        "note": "Scores are planning heuristics; no verified revenue growth is claimed."
    }

def format_executive(report):
    summary, gates = report["summary"], report["gates"]
    rows = [
        "# SuperAgente — informe ejecutivo interno", "",
        "**Solo lectura: ninguna publicación ni automatización activada.**", "",
        f"- Propuestas totales: {summary['total_tasks']}",
        f"- Para revisión editorial: {summary['editorial_review']}",
        f"- Bloqueadas para revisión de riesgo: {summary['held_for_risk_review']}",
        f"- Coste estimado para evaluar: {gates['estimated_total_work_cost_eur']} €",
        f"- Presupuesto disponible: {gates['budget_eur'] if gates['budget_eur'] is not None else 'Sin datos'}",
        f"- Comisiones verificadas: {'No' if not gates['affiliate_figures_verified'] else 'Requiere contrastar fuente'}",
        f"- Reversión remota staging verificada: {gates['rollback_verified_in_remote_preview']}",
        "", "## Prioridades a revisar", ""
    ]
    if not report["priorities"]:
        rows.append("No hay propuestas respaldadas por los archivos suministrados.")
    for item in report["priorities"][:20]:
        rows.append(f"- **{item['title']}** ({item['status']}; {item['seo_risk']} SEO; {item['impact_basis']} impacto)")
    rows.extend(["", "## Bloqueos de seguridad", ""])
    rows.extend(["- " + blocker for blocker in gates["known_blockers"]] or ["- Ninguno nuevo en los informes aportados; despliegue igualmente no autorizado."])
    rows.extend(["", "**Esta ejecución no ha modificado la web ni ha aprobado despliegues.**", ""])
    return "\n".join(rows)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--proposals", type=Path)
    p.add_argument("--amazon-audit", type=Path)
    p.add_argument("--affiliate-monthly", type=Path)
    p.add_argument("--history", type=Path)
    p.add_argument("--staging-report", type=Path)
    p.add_argument("--budget-eur")
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    report = build_integrated_plan(
        proposals=read_json(args.proposals), amazon_audit=read_json(args.amazon_audit),
        affiliate_monthly=read_json(args.affiliate_monthly),
        history=memory.read_history(args.history) if args.history else [],
        staging_report=read_json(args.staging_report), budget_eur=args.budget_eur)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "superagente-integrado.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "superagente-ejecutivo.md").write_text(format_executive(report), encoding="utf-8")
    print(f"Integrated read-only review complete: {report['summary']['total_tasks']} proposals, 0 deployments")

if __name__ == "__main__":
    main()
