#!/usr/bin/env python3
"""SuperAgente V1 operational readiness gate (fail closed).

Deliberately NOT a deployment tool or permissions grant. An isolated coordinator
can be coded and tested without being ready for autonomous operation.
"""
import argparse
import json
from pathlib import Path

REQUIRED = (
    "official_sources_verified",
    "seo_baseline_verified",
    "mobile_visual_regression_passed",
    "preview_content_verified",
    "manual_editorial_approval",
    "private_data_access_authorized",
    "deployment_rollback_verified",
)

def assess(integrated_report, evidence):
    if not isinstance(integrated_report, dict) or integrated_report.get("mode") != "offline_integrated_review":
        raise ValueError("Invalid integrated report")
    gates = integrated_report.get("gates", {})
    if gates.get("publish_to_production_allowed") is not False or gates.get("automation_enabled") is not False:
        raise ValueError("Integrated report must prohibit publishing and scheduling")
    if not isinstance(evidence, dict):
        raise ValueError("Missing evidence")
    statuses = {key: evidence.get(key) is True for key in REQUIRED}
    blocker = [key for key, checked in statuses.items() if not checked]
    remote = gates.get("rollback_verified_in_remote_preview") is True
    if not remote:
        blocker.append("rollback_verified_in_remote_preview")
    if gates.get("staging_requires_reverification") is True:
        blocker.append("staging_requires_reverification")
    if gates.get("candidate_cost_exceeds_budget") is True:
        blocker.append("budget_exceeded")
    # This is informational readiness, NEVER deployment authorization.
    return {
        "schema_version": 1, "version": "superagente-v1.0",
        "technical_modules_ready_for_review": True,
        "operational_readiness": "ready_for_human_go_no_go" if not blocker else "blocked",
        "criteria": statuses,
        "blocking_reasons": sorted(set(blocker)),
        "automatic_activation_allowed": False,
        "production_deployment_allowed": False,
        "gsc_wizard_allowed": False,
        "note": "True flags require independently audited evidence. This gate cannot authorize deployment."
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--integrated-json", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = assess(json.loads(args.integrated_json.read_text(encoding="utf-8")),
                    json.loads(args.evidence.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"V1.0 readiness: {result['operational_readiness']} ({len(result['blocking_reasons'])} blockers); deployment remains forbidden")

if __name__ == "__main__":
    main()
