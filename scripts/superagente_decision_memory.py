#!/usr/bin/env python3
"""SuperAgente: audited decision history and conservative prioritization.

Local only: no network, commits, releases, secrets or automated publication.
All impact figures are HUMAN ESTIMATES unless evidence and measurement exist.
Decisions and outcomes are distinct events. Historic outcomes never self-validate.
"""
import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

KINDS = {"seo", "ux", "legal", "technical", "affiliate", "content", "security"}
RISKS = {"low": 1, "medium": 2, "high": 3, "critical": 4}
RESULTS = {"positive", "negative", "neutral", "inconclusive"}
MAX_LINES = 10000

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def sha(payload):
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()

def validated_day(value):
    if not isinstance(value, str):
        raise ValueError("Date must be YYYY-MM-DD")
    try:
        day = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid date") from exc
    if day.isoformat() != value:
        raise ValueError("Date must be YYYY-MM-DD")
    return value

def estimate(value):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean is not an estimate")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid estimate") from exc
    if not result.is_finite() or result < 0 or result > 1000000:
        raise ValueError("Estimate outside safe limits")
    return result

def validate_event(event):
    if not isinstance(event, dict) or event.get("schema_version") != 1:
        raise ValueError("Invalid history event version")
    kind = event.get("event_type")
    if kind not in ("decision", "outcome"):
        raise ValueError("Unknown history event type")
    decision_id = event.get("decision_id")
    if not isinstance(decision_id, str) or not 1 <= len(decision_id) <= 100 or not all(
        char.isascii() and (char.isalnum() or char in "-_.") for char in decision_id
    ):
        raise ValueError("Invalid decision ID")
    validated_day(event.get("date"))
    if kind == "decision":
        for key in ("title", "reason", "evidence_ref"):
            if not isinstance(event.get(key), str) or not event[key].strip():
                raise ValueError(f"Missing {key}")
        if event.get("category") not in KINDS or event.get("seo_risk") not in RISKS:
            raise ValueError("Unknown category or risk")
        if event.get("approved") is not False or event.get("deployed") is not False:
            raise ValueError("Creating a history entry cannot approve or deploy a change")
    else:
        if event.get("result") not in RESULTS:
            raise ValueError("Invalid measured result")
        if not isinstance(event.get("evidence_ref"), str) or not event["evidence_ref"].strip():
            raise ValueError("An outcome requires evidence")
        if event.get("manually_verified") is not True:
            raise ValueError("Only a human-verified outcome may enter the decision memory")
        if event.get("approved") is not False or event.get("deployed") is not False:
            raise ValueError("An outcome cannot grant publishing permission")
    return event

def validate_history(events):
    seen_decisions = set()
    seen_outcomes = set()
    for event in events:
        validate_event(event)
        key = event["decision_id"]
        if event["event_type"] == "decision":
            if key in seen_decisions:
                raise ValueError("Duplicate decision ID")
            seen_decisions.add(key)
        else:
            if key not in seen_decisions or key in seen_outcomes:
                raise ValueError("Outcome without decision or duplicate outcome")
            seen_outcomes.add(key)
    return events

def read_history(path):
    if not path or not Path(path).exists():
        return []
    events = []
    for index, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if index > MAX_LINES:
            raise ValueError("History exceeds limit")
        if not line.strip():
            raise ValueError("Blank history line")
        events.append(json.loads(line))
    return validate_history(events)

def append_event(path, event):
    """Explicit local append with no overwrite or silent history replacement."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Refuse history symlink")
    history = read_history(path)
    validate_history(history + [event])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical(event) + "\n")
    return len(history) + 1

def validate_candidate(item):
    if not isinstance(item, dict):
        raise ValueError("Invalid candidate")
    for name in ("id", "title", "evidence_ref"):
        if not isinstance(item.get(name), str) or not item[name].strip():
            raise ValueError(f"Candidate missing {name}")
    if item.get("category") not in KINDS or item.get("seo_risk") not in RISKS:
        raise ValueError("Unknown candidate category or risk")
    if item.get("urgency") not in ("low", "medium", "high"):
        raise ValueError("Invalid urgency")
    cost = estimate(item.get("cost_eur"))
    hours = estimate(item.get("effort_hours"))
    impact = estimate(item.get("expected_monthly_benefit_eur"))
    if cost is None or hours is None:
        raise ValueError("Cost and effort must be supplied for prioritization")
    if item.get("impact_basis") not in ("verified", "hypothesis", "unknown"):
        raise ValueError("Impact basis must be explicit")
    if item["impact_basis"] == "unknown" and impact is not None:
        raise ValueError("Unknown impact cannot have a numeric estimate")
    if item["impact_basis"] == "verified":
        if not item.get("impact_evidence_ref"):
            raise ValueError("Verified impact requires independent evidence reference")
    if impact is None and item["impact_basis"] != "unknown":
        raise ValueError("An expected impact estimate is missing")
    return cost, hours, impact

def priority_plan(candidates, history):
    validate_history(history)
    if not isinstance(candidates, list):
        raise ValueError("Candidates must be an array")
    if len(candidates) > 500:
        raise ValueError("Too many candidates")
    previous = {}
    outcomes = {}
    for event in history:
        if event["event_type"] == "decision":
            previous[event["decision_id"]] = event
        else:
            outcomes[event["decision_id"]] = event
    items = []
    ids = set()
    for candidate in candidates:
        cost, hours, impact = validate_candidate(candidate)
        id_ = candidate["id"]
        if id_ in ids:
            raise ValueError("Duplicate candidate ID")
        ids.add(id_)
        risk = candidate["seo_risk"]
        category = candidate["category"]
        history_outcome = outcomes.get(id_)
        negative_outcome = history_outcome and history_outcome["result"] == "negative"
        high_risk = risk in ("high", "critical")
        sensitive = category in ("legal", "security")
        blocked = bool(high_risk or sensitive or negative_outcome)
        # Ranking is a review heuristic, not an objective business forecast.
        urgency_points = {"low": 0, "medium": 20, "high": 40}[candidate["urgency"]]
        benefit_points = min(20, int(impact / Decimal(25))) if impact is not None else 0
        evidence_points = 10 if candidate["impact_basis"] == "verified" else 0
        effort_penalty = min(25, int(hours / Decimal(2)))
        money_penalty = min(20, int(cost / Decimal(10)))
        risk_penalty = 12 * (RISKS[risk] - 1)
        score = urgency_points + benefit_points + evidence_points - effort_penalty - money_penalty - risk_penalty
        if negative_outcome:
            score -= 50
        items.append({
            "id": id_, "title": candidate["title"], "category": category,
            "evidence_ref": candidate["evidence_ref"],
            "seo_risk": risk, "score_for_editorial_triage_only": score,
            "estimated_monthly_benefit_eur": str(impact) if impact is not None else None,
            "impact_basis": candidate["impact_basis"],
            "estimated_cost_eur": str(cost), "estimated_effort_hours": str(hours),
            "prior_negative_outcome": bool(negative_outcome),
            "status": "hold_for_manual_risk_review" if blocked else "proposed_for_editorial_review",
            "reasons_for_hold": [
                reason for active, reason in (
                    (high_risk, "High/critical SEO risk"),
                    (sensitive, "Legal/security changes require specialized human approval"),
                    (bool(negative_outcome), "Previous verified negative result: examine before retry")
                ) if active
            ],
            "publication_allowed": False,
            "auto_deploy_allowed": False
        })
    items.sort(key=lambda x: (x["status"] != "proposed_for_editorial_review",
                              -x["score_for_editorial_triage_only"], x["id"]))
    return {
        "schema_version": 1, "mode": "recommendation_only",
        "decision_history_size": len(history), "history_sha256": sha(history),
        "candidate_count": len(items), "items": items,
        "ranking_note": "Scores are heuristic editorial priorities, not predictions or verified revenue.",
        "automatic_publication": False, "automated_deployment": False,
        "require_seo_mobile_qa": True, "require_editorial_approval": True
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--append-event", type=Path, help="Local JSON decision or human-verified outcome")
    parser.add_argument("--candidates", type=Path, help="JSON array of proposed work")
    parser.add_argument("--output", type=Path, help="Where to save the read-only plan")
    args = parser.parse_args()
    if args.append_event:
        event = json.loads(args.append_event.read_text(encoding="utf-8"))
        append_event(args.history, event)
        print("History event appended locally; no website modifications")
    if args.candidates:
        if not args.output:
            parser.error("--output required with --candidates")
        plan = priority_plan(json.loads(args.candidates.read_text(encoding="utf-8")), read_history(args.history))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Prioritized {plan['candidate_count']} review proposals; no deployment")
    if not args.append_event and not args.candidates:
        parser.error("Provide --append-event or --candidates")

if __name__ == "__main__":
    main()
