#!/usr/bin/env python3
"""Fail-closed legal fact verification for SuperAgente editorial proposals.

This module verifies provenance, exact supporting evidence, scope and
mechanical consistency. It DOES NOT infer legal meaning or determine that
a claim is true. A separate accountable editorial reviewer must attest
interpretation and applicability; no automatic legal publishing.
"""
import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

HEX=re.compile(r"^[0-9a-f]{64}$")
DATE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
ALLOWED_KIND={"amount","deadline","eligibility","application_status","requirements","other"}
ALLOWED_STATUS={"open","closed","not_applicable","uncertain"}
REQUIRED_SCOPE=("jurisdiction","benefit","beneficiaries","effective_from","effective_until",
                "exceptions","application_status")
def sha(text): return sha256(text.encode("utf-8")).hexdigest()

def nonempty(value):
    return isinstance(value,str) and bool(value.strip())

def iso_date(value):
    if value is None:return None
    if not isinstance(value,str) or not DATE.fullmatch(value):
        raise ValueError("Invalid ISO date")
    return date.fromisoformat(value)

def verify(claims, watchlist, watch_report, snapshots, root):
    """Validate documentary links for a proposed batch, never grant approval."""
    if not isinstance(claims,dict) or claims.get("schema_version")!=1 or claims.get("publication_allowed") is not False:
        raise ValueError("Untrusted claim manifest")
    sources=watchlist.get("sources",[])
    reports=watch_report.get("results",[])
    captures=snapshots.get("snapshots",[])
    rows=claims.get("claims")
    if not all(isinstance(x,list) for x in (sources,reports,captures,rows)) or not rows or len(rows)>100:
        raise ValueError("Malformed evidence collections")
    def keyed(items, key):
        ans={}
        for x in items:
            if not isinstance(x,dict) or not nonempty(x.get(key)) or x[key] in ans:
                raise ValueError("Invalid or duplicate official source")
            ans[x[key]]=x
        return ans
    allowed=keyed(sources,"url")
    status=keyed(reports,"url")
    actual=keyed(captures,"url")
    if set(status)!=set(allowed) or not set(actual).issubset(allowed):
        raise ValueError("Source set mismatch")
    from superagente_semantic_evidence import site_file
    root=Path(root).resolve()
    validated=[]
    used=set()
    for item in rows:
        if not isinstance(item,dict):raise ValueError("Malformed legal claim")
        source_url=item.get("source_url")
        if source_url not in allowed:raise ValueError("Source is not allowlisted")
        p=urlsplit(source_url)
        if p.scheme!="https" or p.hostname!=allowed[source_url].get("approved_host"):
            raise ValueError("Official hostname mismatch")
        if status[source_url].get("status") not in ("changed_needs_review","unchanged"):
            raise ValueError("No completed official source capture")
        snapshot=actual.get(source_url)
        if not snapshot or not nonempty(snapshot.get("text")):
            raise ValueError("Missing source snapshot")
        text=snapshot["text"]
        digest=sha(text)
        if digest!=snapshot.get("sha256") or digest!=status[source_url].get("sha256") or digest!=item.get("source_sha256"):
            raise ValueError("Stale or altered source evidence")
        source_quote=item.get("source_quote")
        if not nonempty(source_quote) or len(source_quote)<20 or len(source_quote)>1200 or source_quote not in text:
            raise ValueError("Official evidence must be an exact 20-1200 character excerpt")
        page_url=allowed[source_url].get("page")
        rel,page=site_file(page_url,root)
        html=page.read_text(encoding="utf-8")
        if item.get("path")!=rel or item.get("page_sha256")!=sha(html):
            raise ValueError("Mismatched or stale page")
        original=item.get("old_claim")
        replacement=item.get("new_claim")
        if not nonempty(original) or not nonempty(replacement) or original==replacement:
            raise ValueError("Expected exact replacement of real, unique claim")
        if any("<" in s or ">" in s for s in (original,replacement)):
            raise ValueError("HTML edits prohibited")
        if html.count(original)!=1:
            raise ValueError("Claim is stale, missing or duplicated")
        kind=item.get("kind")
        if kind not in ALLOWED_KIND:raise ValueError("Unknown legal claim type")
        scope=item.get("scope")
        if not isinstance(scope,dict) or any(k not in scope for k in REQUIRED_SCOPE):
            raise ValueError("Missing applicable legal scope")
        if not all(nonempty(scope[k]) for k in ("jurisdiction","benefit","beneficiaries","exceptions")):
            raise ValueError("Incomplete jurisdiction or exceptions")
        if scope["application_status"] not in ALLOWED_STATUS:
            raise ValueError("Unclear application status")
        first=iso_date(scope["effective_from"])
        last=iso_date(scope["effective_until"])
        if first and last and first>last:raise ValueError("Inverted validity dates")
        # Two explicit uncertainty gates, including future law and ambiguous scope.
        if scope["application_status"]=="uncertain" or item.get("legal_conflict_detected") is not False:
            raise ValueError("Uncertain applicability requires manual legal analysis")
        reviewer=item.get("reviewer")
        if (not isinstance(reviewer,dict) or not nonempty(reviewer.get("name")) or
            reviewer.get("independent_factual_check") is not True or
            reviewer.get("scope_and_exceptions_checked") is not True or
            not nonempty(reviewer.get("evidence_ref")) or
            not nonempty(reviewer.get("reviewed_at"))):
            raise ValueError("Missing accountable independent review")
        review_stamp=iso_date(reviewer["reviewed_at"])
        if review_stamp>date.today():raise ValueError("Future editorial review impossible")
        key=(source_url,rel,original)
        if key in used:raise ValueError("Duplicate claim")
        used.add(key)
        validated.append({
            "path":rel, "source_url":source_url,
            "source_sha256":digest,"page_sha256":sha(html),
            "source_quote":source_quote,"old_claim":original,"new_claim":replacement,
            "kind":kind,"scope":scope,"reviewer":reviewer["name"],
            "evidence_ref":reviewer["evidence_ref"],
            "ready_for_branch_only":True,
            "auto_publish_allowed":False
        })
    return {
        "schema_version":1,"mode":"documentary_evidence_validation",
        "validated_count":len(validated),"records":validated,
        "automatic_legal_truth_established":False,
        "branch_edits_require_editorial_loop_approval":True,
        "automatic_publication_allowed":False,
        "warning":"Exact quote + human scope attestation is review evidence, not a machine proof of legal validity."
    }

def to_branch_manifest(report, review_date):
    """Convert externally reviewed, bound evidence to an updater input.

    The updater still performs page SHA and source mapping checks independently.
    This conversion is not a deployment authorization.
    """
    iso_date(review_date)
    if not isinstance(report,dict) or report.get("mode")!="documentary_evidence_validation":
        raise ValueError("Unverified report")
    rows=report.get("records")
    if not isinstance(rows,list) or not rows:
        raise ValueError("Empty verification report")
    paths=set()
    changes=[]
    for row in rows:
        path=row.get("path")
        if path in paths:
            raise ValueError("Multiple facts in a page need combined editorial revision")
        paths.add(path)
        if row.get("ready_for_branch_only") is not True or row.get("auto_publish_allowed") is not False:
            raise ValueError("Unverified or publishable claim")
        changes.append({
            "path":path, "original_sha256":row["page_sha256"],
            "source_sha256":row["source_sha256"], "official_source_url":row["source_url"],
            "action":"change","search":row["old_claim"],"replacement":row["new_claim"],
            "review_date":review_date, "independent_source_verification":True,
            "editorial_approval":True, "reviewer":row["reviewer"],
            "evidence_ref":row["evidence_ref"],
        })
    return {"schema_version":1,"status":"editorially_verified_for_branch_only",
            "publication_allowed":False,"changes":changes}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--claims",type=Path,required=True)
    p.add_argument("--watchlist",type=Path,required=True)
    p.add_argument("--watch-report",type=Path,required=True)
    p.add_argument("--snapshots",type=Path,required=True)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    v=lambda f:json.loads(f.read_text(encoding="utf-8"))
    result=verify(v(a.claims),v(a.watchlist),v(a.watch_report),v(a.snapshots),a.root)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{result['validated_count']} evidence-grounded edits eligible for separate batch editorial check; no publishing")
if __name__=="__main__":main()
