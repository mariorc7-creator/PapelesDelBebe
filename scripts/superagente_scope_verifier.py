#!/usr/bin/env python3
"""Strict legal scope support check, without pretending to interpret law.

Each proposed fact must have source-bound explicit evidence for jurisdiction,
beneficiary class, exceptions, effective dates and application status. Values
must occur in their exact quoted source text. Ambiguity fails closed.
This validates provenance and textual consistency, NOT legal eligibility.
"""
from datetime import date
import re
from superagente_claim_consistency import extracted, normalize_text

FIELDS=("jurisdiction","benefit","beneficiaries","exceptions","effective_from",
        "effective_until","application_status")
UNCERTAINTY=re.compile(
    r"\b(?:quiz[aá]s|podr[ií]a|posible|pendiente de confirmar|por determinar|"
    r"sin confirmar|consultar|verificar|sujeto a cambios)\b",re.I)
NEGATION=re.compile(r"\b(?:no|sin|excepto|salvo|excluid[oa]s?)\b",re.I)

def is_date(value):
    try:
        return isinstance(value,str) and date.fromisoformat(value).isoformat()==value
    except ValueError:
        return False

def verify_scope(scope, evidence, full_text):
    if not isinstance(scope,dict) or not isinstance(evidence,dict) or not isinstance(full_text,str):
        raise ValueError("Scope and evidence required")
    missing=set(FIELDS)-set(scope)
    if missing or set(FIELDS)-set(evidence):
        raise ValueError("Missing essential jurisdiction, dates, exceptions or beneficiary evidence")
    details={}
    for field in FIELDS:
        row=evidence[field]
        if not isinstance(row,dict):
            raise ValueError("Missing explicit evidence object: "+field)
        quote=row.get("quote")
        literal=row.get("literal")
        if not isinstance(quote,str) or len(quote)<20 or len(quote)>1200 or quote not in full_text:
            raise ValueError("Scope quote missing from exact official snapshot: "+field)
        if not isinstance(literal,str) or not literal.strip() or len(literal)>140:
            raise ValueError("Unclear scope literal: "+field)
        if UNCERTAINTY.search(literal):
            raise ValueError("Scope requires independent specialist interpretation: "+field)
        if normalize_text(literal) not in normalize_text(quote):
            raise ValueError("Scope literal not in its official quote: "+field)
        value=scope[field]
        if field in ("jurisdiction","benefit","beneficiaries","exceptions"):
            if not isinstance(value,str) or not value.strip():
                raise ValueError("Blank scope: "+field)
            # The structured scope cannot silently change the claim in citation.
            if normalize_text(value)!=normalize_text(literal):
                raise ValueError("Scope claim differs from cited literal: "+field)
        elif field in ("effective_from","effective_until"):
            if not is_date(value):
                raise ValueError("Exact effective date required: "+field)
            if value not in extracted(literal)["dates"]:
                raise ValueError("Effective date unsupported in official literal: "+field)
        elif field=="application_status":
            states=extracted(quote)["status"]
            if value not in ("open","closed","suspended") or len(states)!=1 or value not in states:
                raise ValueError("Ambiguous application status or unsupported claim")
            if value not in extracted(literal)["status"]:
                raise ValueError("Status literal does not support claim")
        details[field]={"source_quote":quote,"cited_literal":literal,"mechanically_supported":True}
    if date.fromisoformat(scope["effective_from"])>date.fromisoformat(scope["effective_until"]):
        raise ValueError("Inverted legal validity period")
    # Negation is frequently material. Keep all beneficiary/exclusion cases
    # for accountable review, even if the literal and quote match exactly.
    ambiguous=bool(NEGATION.search(evidence["beneficiaries"]["quote"]) or
                   NEGATION.search(evidence["exceptions"]["quote"]))
    return {"scope_citations":details,"potential_exclusion_requires_review":ambiguous,
            "legal_applicability_proven":False,"automatic_publication_allowed":False}
