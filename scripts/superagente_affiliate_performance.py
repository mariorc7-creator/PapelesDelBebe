#!/usr/bin/env python3
"""Affiliate performance from *user-provided* official CSV exports.

No network calls, website mutations, secrets or invented conversion attribution.
Clicks are Vercel Analytics events, sales are Amazon Associates report totals.
These are independent sources; joining them by visitor is NOT possible here.

Expected Vercel-normalized CSV: date,category,clicks
Expected Amazon-normalized CSV: date,ordered_items,shipped_items,commission_eur

Columns have intentionally strict names: mapping the official export columns to
these formats requires a documented, reviewed export adapter, not guessing.
Missing inputs remain null; zero is only shown when data is explicitly present.
"""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

CLICKS_COLUMNS = {"date", "category", "clicks"}
AMAZON_COLUMNS = {"date", "ordered_items", "shipped_items", "commission_eur"}
MAX_ROWS = 50000

def _read_csv(path, required):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or set(reader.fieldnames) != required:
            raise ValueError(f"CSV columns must be exactly {sorted(required)}")
        rows = []
        for index, row in enumerate(reader, start=2):
            if index > MAX_ROWS + 1:
                raise ValueError("Too many rows")
            if any(value is None for value in row.values()) or None in row:
                raise ValueError(f"Malformed CSV at line {index}")
            rows.append(row)
    return rows

def _day(value):
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date: {value}") from exc
    if parsed.isoformat() != value:
        raise ValueError("Date must use YYYY-MM-DD")
    return parsed

def _quantity(value):
    if not value.isascii() or not value.isdecimal():
        raise ValueError(f"Invalid nonnegative count: {value!r}")
    result = int(value)
    if result > 100000000:
        raise ValueError("Count exceeds safety limit")
    return result

def _money(value):
    try:
        money = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid commission amount") from exc
    if not money.is_finite() or abs(money) > Decimal("100000000"):
        raise ValueError("Invalid commission amount")
    if money.as_tuple().exponent < -2:
        raise ValueError("Commission must have at most two decimals")
    return money

def build_report(clicks_path=None, amazon_path=None, start=None, end=None):
    if not clicks_path and not amazon_path:
        raise ValueError("At least one export file is required")
    start_date = _day(start) if start else None
    end_date = _day(end) if end else None
    if start_date and end_date and start_date > end_date:
        raise ValueError("End date precedes start date")
    def in_window(day):
        return (not start_date or day >= start_date) and (not end_date or day <= end_date)

    click_totals = {}
    click_dates = set()
    if clicks_path:
        for row in _read_csv(Path(clicks_path), CLICKS_COLUMNS):
            day = _day(row["date"])
            category = row["category"].strip()
            if not category or len(category) > 80:
                raise ValueError("Invalid category")
            count = _quantity(row["clicks"])
            if in_window(day):
                click_dates.add(day.isoformat())
                click_totals[category] = click_totals.get(category, 0) + count
    ordered = shipped = 0
    commission = Decimal("0.00")
    amazon_dates = set()
    if amazon_path:
        for row in _read_csv(Path(amazon_path), AMAZON_COLUMNS):
            day = _day(row["date"])
            order_count = _quantity(row["ordered_items"])
            shipped_count = _quantity(row["shipped_items"])
            value = _money(row["commission_eur"])
            if in_window(day):
                amazon_dates.add(day.isoformat())
                ordered += order_count
                shipped += shipped_count
                commission += value
    return {
        "schema_version": 1,
        "mode": "review_only",
        "period": {"from": start, "to": end},
        "data_sources": {
            "clicks": "normalized_vercel_analytics_export" if clicks_path else None,
            "amazon": "normalized_amazon_associates_export" if amazon_path else None
        },
        "clicks": {
            "total": sum(click_totals.values()) if clicks_path else None,
            "by_category": dict(sorted(click_totals.items(), key=lambda item: (-item[1], item[0]))) if clicks_path else None,
            "days_with_report_rows": len(click_dates) if clicks_path else None
        },
        "amazon": {
            "ordered_items": ordered if amazon_path else None,
            "shipped_items": shipped if amazon_path else None,
            "commissions_eur": str(commission.quantize(Decimal("0.01"))) if amazon_path else None,
            "days_with_report_rows": len(amazon_dates) if amazon_path else None
        },
        "conversion_rate": None,
        "conversion_rate_note": "No visitor-level attribution between Vercel events and Amazon Associates; conversion rate not estimated.",
        "coverage_note": "Totals include ONLY the supplied rows within the selected date window. Missing dates are not assumed zero.",
        "verified_import": False,
        "verification_note": "A local CSV import cannot establish provenance or certify that a file is an unmodified official export.",
        "publication_allowed": False,
        "website_modified": False,
        "automated_actions": []
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clicks-csv", type=Path)
    parser.add_argument("--amazon-csv", type=Path)
    parser.add_argument("--start", help="YYYY-MM-DD")
    parser.add_argument("--end", help="YYYY-MM-DD")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.clicks_csv, args.amazon_csv, args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Affiliate performance: report generated from supplied exports; no production changes")

if __name__ == "__main__":
    main()
