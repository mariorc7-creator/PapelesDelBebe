#!/usr/bin/env python3
"""Conservative alignment of proposed legal edits with quoted official evidence.

This is a deterministic *contradiction detector*, not autonomous legal
interpretation. For numeric or explicit-status changes, reject a proposed
replacement unless the actual asserted value appears in the exact official
excerpt (with limited accepted spelling/format variations). A mismatch is
never automatically accepted, even if an editorial boolean is true.

No network, site changes, publishing or inferred legal entitlement.
"""
from decimal import Decimal, InvalidOperation
import re
import unicodedata

MONEY=re.compile(r"(?<!\w)(\d{1,3}(?:[.\s]\d{3})+|\d{1,8})(?:,(\d{1,2}))?\s*(?:€|euros?|eur\b)",re.I)
PERCENT=re.compile(r"(?<!\w)(\d{1,3})(?:,(\d{1,2}))?\s*%",re.I)
DURATION=re.compile(r"(?<!\w)(\d{1,3})\s*(d[ií]as?|mes(?:es)?|a[nñ]os?)\b",re.I)
ISO_DATE=re.compile(r"\b(20\d{2})-(0[1-9]|1[012])-([012]\d|3[01])\b")
SPANISH_DATE=re.compile(r"\b([0-3]?\d)\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(20\d{2})\b",re.I)
MONTHS={m:i+1 for i,m in enumerate(("enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"))}
STATUS={
 "abierta": "open", "abierto": "open", "abiertas": "open",
 "cerrada": "closed", "cerrado": "closed", "finalizada": "closed",
 "finalizado": "closed", "suspendida": "suspended", "suspendido": "suspended",
}
STATUS_PATTERN=re.compile(r"\b(?:abierta|abierto|abiertas|cerrada|cerrado|finalizada|finalizado|suspendida|suspendido)\b",re.I)

def normalize_text(text):
    s=unicodedata.normalize("NFD",text.lower())
    return "".join(c for c in s if not unicodedata.combining(c))

def parse_number(s):
    s=re.sub(r"[.\s]","",s)
    try:return str(Decimal(s.replace(",","." )).normalize())
    except InvalidOperation:raise ValueError("Bad amount") from None

def extracted(text):
    if not isinstance(text,str):raise ValueError("Text must be string")
    values={"money":set(),"percent":set(),"duration":set(),"dates":set(),"status":set()}
    for m in MONEY.finditer(text):
        raw=m.group(1)+(","+m.group(2) if m.group(2) else "")
        values["money"].add(parse_number(raw))
    for m in PERCENT.finditer(text):
        raw=m.group(1)+(","+m.group(2) if m.group(2) else "")
        values["percent"].add(parse_number(raw))
    for m in DURATION.finditer(text):
        unit=normalize_text(m.group(2))
        if unit.startswith("dia"):unit="day"
        elif unit.startswith("mes"):unit="month"
        else:unit="year"
        values["duration"].add((int(m.group(1)),unit))
    for m in ISO_DATE.finditer(text):
        from datetime import date
        try: values["dates"].add(date(int(m.group(1)),int(m.group(2)),int(m.group(3))).isoformat())
        except ValueError:pass
    for m in SPANISH_DATE.finditer(text):
        from datetime import date
        try: values["dates"].add(date(int(m.group(3)),MONTHS[m.group(2).lower()],int(m.group(1))).isoformat())
        except ValueError:pass
    for m in STATUS_PATTERN.finditer(text):
        values["status"].add(STATUS[m.group(0).lower()])
    return values

def check_claim(kind, original, proposed, official_quote):
    """Reject mismatched explicit factual claims; do not assert legal truth."""
    if not all(isinstance(x,str) and x.strip() for x in (kind,original,proposed,official_quote)):
        raise ValueError("Missing claim or official quote")
    before=extracted(original)
    after=extracted(proposed)
    source=extracted(official_quote)
    kinds={"amount":("money",),"deadline":("dates","duration"),"application_status":("status",),
           "eligibility":("money","percent","dates","duration"),"requirements":("money","percent","dates","duration"),
           "other":("money","percent","dates","duration","status")}
    if kind not in kinds:raise ValueError("Unknown legal claim kind")
    # If claim explicitly asserts something, it must be evidenced. Never
    # interpret absence of a value or negation as a verified fact.
    asserted={k:after[k] for k in kinds[kind] if after[k]}
    if not asserted:
        raise ValueError("No machine-verifiable assertion in proposed claim; specialist review required")
    if kind=="amount" and not after["money"]:
        raise ValueError("Amount edit has no explicit monetary figure")
    if kind=="deadline" and not (after["dates"] or after["duration"]):
        raise ValueError("Deadline edit has no explicit date or duration")
    if kind=="application_status" and not after["status"]:
        raise ValueError("Status edit lacks explicit open/closed/suspended token")
    for key, values in asserted.items():
        missing=values-source[key]
        if missing:
            raise ValueError("Proposed "+key+" unsupported by exact source excerpt")
    # If source text is ambiguous (e.g. BOTH open and closed), a status cannot
    # be determined from a superficial keyword match.
    if kind=="application_status" and len(source["status"])!=1:
        raise ValueError("Conflicting or ambiguous official status")
    # Detect changes where the old and new value are the same numeric assertion.
    if kind in ("amount","deadline","application_status") and all(
        before[key]==after[key] for key in kinds[kind]
    ):
        raise ValueError("No change in asserted legal value")
    return {
      "mechanical_consistency":True,
      "legal_applicability_proven":False,
      "publication_allowed":False,
      "assertion_categories":sorted(asserted),
    }
