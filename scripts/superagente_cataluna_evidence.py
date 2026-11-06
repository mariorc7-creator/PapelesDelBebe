#!/usr/bin/env python3
"""Check seven literal source excerpts against a captured Catalonia official page.

Literal excerpt matching is documentary evidence only, not a legal judgment.
No site files, review dates, releases or production are changed.
"""
import argparse
import hashlib
import json
from pathlib import Path

URL = "https://tramits.gencat.cat/es/tramits/tramits-temes/Prestacio-per-a-families-amb-infants?moda=1"
PAGE = "https://www.papelesdelbebe.es/ayuda-nacimiento-cataluna/"
TOPICS = {
  "eligibility": "Uno de los progenitores debe haber residido legalmente en Catalunya durante al menos 5 años",
  "amount": "El importe de la prestación es de 650 euros por niño",
  "deadline": "Puedes presentar la solicitud durante 3 meses",
  "documents": "Documento identificativo de la persona solicitante (DNI o NIE)",
  "procedure": "Por Internet | Presencialmente | Por videoatención",
  "compatibility": "Esta prestación es compatible con cualquier otra ayuda familiar otorgada por las administraciones públicas.",
  "official_link": "Prestación para familias con hijos Solicitar la prestación",
}
ADDITIONAL = {
  "special_amount": "el importe es de 750 euros",
  "old_deadline": "Tienes 1 mes para presentar la solicitud",
  "deadline_cutoff": "a partir del 14 de julio de 2026",
}
def normalize(text):
    return " ".join(text.split())

def inspect(captures, root, page=PAGE, url=URL):
    entries = captures.get("captures") if isinstance(captures, dict) else None
    if not isinstance(entries, list):
        raise ValueError("invalid captures")
    matches = [x for x in entries if isinstance(x,dict) and x.get("source_url") == url]
    if len(matches) != 1:
        raise ValueError("exactly one capture required")
    record = matches[0]
    value = record.get("text")
    if not isinstance(value,str) or not value:
        raise ValueError("missing captured text")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    if record.get("sha256") != digest:
        raise ValueError("capture text hash mismatch")
    if record.get("fetch_method") != "https_pinned_public_ip_tls_hostname_no_redirect":
        raise ValueError("unapproved capture method")
    path = Path(root).resolve() / "ayuda-nacimiento-cataluna" / "index.html"
    if not path.is_file():
        raise ValueError("missing source HTML")
    page_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    normalized = normalize(value)
    def row(key, excerpt):
        return {"topic":key, "excerpt":excerpt,
                "present_in_capture":normalize(excerpt) in normalized}
    checks = [row(k,v) for k,v in TOPICS.items()]
    extra = [row(k,v) for k,v in ADDITIONAL.items()]
    missing = [x["topic"] for x in checks + extra if not x["present_in_capture"]]
    return {"schema_version":1, "page":page, "source_url":url,
            "page_sha256":page_hash, "capture_text_sha256":digest,
            "captured_at_utc":record.get("captured_at_utc"),
            "seven_topics_with_source_excerpt":sum(c["present_in_capture"] for c in checks),
            "checks":checks, "additional_checks":extra, "missing_excerpts":missing,
            "legal_applicability_verified":False,"editorial_approval":False,
            "review_date_update":False,"publication_allowed":False,
            "warning":"Excerpt presence proves text exists in capture, not correctness of page claims or full legal review."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--captures",type=Path,default=Path("superagente/source-capture-report.json"))
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--output",type=Path,default=Path("superagente/research/cataluna-seven-topic-source-evidence.json"))
    args=p.parse_args()
    report=inspect(json.loads(args.captures.read_text(encoding="utf-8")),args.root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Catalonia source evidence: %s/7 topics with excerpts, %s missing" %
          (report["seven_topics_with_source_excerpt"], len(report["missing_excerpts"])))
    raise SystemExit(1 if report["missing_excerpts"] else 0)
if __name__=="__main__":
    main()
