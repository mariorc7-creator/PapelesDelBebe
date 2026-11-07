#!/usr/bin/env python3
"""Deterministic regression scenarios for three verified 2026 regional schemes.

Sources:
- Asturias: official 2026 natality notice (published 2026-04-01).
- Extremadura: official 2026 natality call, deadline 2026-09-30.
- Catalonia: Generalitat infant benefit 2026, cutoff 2026-07-14.

This is a conservative *content validation oracle*, NOT an eligibility award
or general-purpose legal interpreter. Unmodeled facts, conflicting deadlines
and missing case context lead to 'manual_review', NEVER an inferred entitlement
or automatic website update.
"""
import argparse
import calendar
from datetime import date
import json
from pathlib import Path

SOURCES={
    "asturias":"https://juventud.asturias.es/-/ayudas-para-el-fomento-de-la-natalidad-y-la-adopci%C3%B3n-en-el-principado-de-asturias%C2%A0%C2%A0.-2025",
    "extremadura":"https://www.juntaex.es/w/0702824",
    "cataluna":"https://tramits.gencat.cat/es/tramits/tramits-temes/Prestacio-per-a-families-amb-infants?moda=1"
}
AS_OF=date(2026,11,7)
def as_date(s):
    try:
        d=date.fromisoformat(s)
        if d.isoformat()!=s:raise ValueError()
        return d
    except (ValueError,TypeError,AttributeError):
        raise ValueError("Invalid ISO 8601 date") from None

def add_months(day,n):
    month0=day.month-1+n
    year=day.year+month0//12
    month=month0%12+1
    return date(year,month,min(day.day,calendar.monthrange(year,month)[1]))

def response(scheme,verdict,reason,*,source,deadline=None,amount=None):
    return {"scheme":scheme,"verdict":verdict,"reason":reason,
            "source":source,"deadline":deadline.isoformat() if deadline else None,
            "amount_eur":amount,"eligible_confirmed":False,
            "publication_allowed":False}

def assess(case,as_of=AS_OF):
    """Classify explicitly covered test cases, never infer full eligibility."""
    if not isinstance(case,dict):raise ValueError("Expected case object")
    scheme=case.get("scheme")
    if scheme not in SOURCES:raise ValueError("Unsupported scheme")
    when=as_date(case.get("event_date"))
    as_of=as_date(as_of) if isinstance(as_of,str) else as_of
    if as_of<date(2026,1,1):raise ValueError("As-of outside modeled period")
    source=SOURCES[scheme]
    if scheme=="extremadura":
        # Official 2026 application window and eligible birth period are distinct.
        if when<date(2025,9,1) or when>date(2026,8,31):
            return response(scheme,"out_of_event_window",
                "Birth/adoption date outside published eligible event period.",source=source)
        residents=case.get("population")
        if not isinstance(residents,int) or isinstance(residents,bool) or residents<0:
            return response(scheme,"manual_review","Municipality population missing or invalid.",source=source)
        if residents>=3000:
            return response(scheme,"outside_population_scope",
                            "Official call applies only to settlements below 3,000 inhabitants.",source=source)
        cutoff=date(2026,9,30)
        if as_of>cutoff:
            return response(scheme,"closed","2026 application window ended 30 September.",source=source,deadline=cutoff,amount=500)
        if as_of<date(2026,8,7):
            return response(scheme,"not_open_yet","2026 window starts 7 August.",source=source,deadline=cutoff,amount=500)
        return response(scheme,"open_pending_checks","During published window; residence, fiscal and other conditions must be verified.",source=source,deadline=cutoff,amount=500)
    if scheme=="asturias":
        if when<date(2025,10,1) or when>date(2026,9,30):
            return response(scheme,"out_of_event_window","Outside 2026 call's covered birth/adoption dates.",source=source)
        if when<=date(2026,3,31):
            return response(scheme,"manual_review",
                "Pre-publication births need exact extract-publication date and special two-month deadline; do not infer.",source=source)
        end=add_months(when,2)
        if as_of>end:
            status="individual_deadline_passed"
            reason="Two-month individual application deadline passed, even if general portal remains visible."
        else:
            status="open_pending_checks"
            reason="Within individual application window; income, residence and other requirements still apply."
        ordinal=case.get("child_order")
        depopulated=case.get("depopulated_municipality")
        if depopulated is True:amount=2200
        elif depopulated is False and isinstance(ordinal,int) and not isinstance(ordinal,bool) and ordinal>=1:
            amount=1200 if ordinal==1 else 1700
        else:amount=None
        return response(scheme,status,reason,source=source,deadline=end,amount=amount)
    # Catalonia: three months after 2026-07-14, one month before 2026-07-13.
    months=3 if when>=date(2026,7,14) else 1
    end=add_months(when,months)
    if when<date(2026,1,1) or when>as_of:
        return response(scheme,"manual_review","Event outside modeled 2026 period or in future.",source=source)
    status="individual_deadline_passed" if as_of>end else "open_pending_checks"
    special=case.get("large_or_single_parent_certified")
    amount=750 if special is True else (650 if special is False else None)
    return response(scheme,status,
        "Application deadline computed from event date, not a general calendar-year cutoff; income and status require verification.",
        source=source,deadline=end,amount=amount)

def validate_casebook(data):
    if not isinstance(data,dict) or data.get("schema_version")!=1 or data.get("published_automatically") is not False:
        raise ValueError("Untrusted casebook")
    cases=data.get("cases")
    if not isinstance(cases,list) or not cases:raise ValueError("Empty casebook")
    results=[]
    for row in cases:
        if not isinstance(row,dict) or not isinstance(row.get("id"),str):
            raise ValueError("Invalid case row")
        found=assess(row["input"],row.get("as_of","2026-11-07"))
        expect=row.get("expected")
        if not isinstance(expect,dict):raise ValueError("Missing expected factual classification")
        for key,value in expect.items():
            if found.get(key)!=value:raise ValueError(f"{row['id']}: {key}: got {found.get(key)!r}, expected {value!r}")
        results.append({"id":row["id"],"passed":True,"result":found})
    return {"schema_version":1,"count":len(results),"passed":len(results),
            "automatic_legal_truth_established":False,
            "production_publication_allowed":False,"results":results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--casebook",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=validate_casebook(json.loads(a.casebook.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Regional legal acceptance: {result['passed']}/{result['count']} cases; zero auto-publish permission")
if __name__=="__main__":main()
