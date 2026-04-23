#!/usr/bin/env python3
"""Cost dashboard CLI for n8n billing data.

Reads a billing CSV and writes summary CSV files to an output directory.

Usage:
    python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/

Output files written to --out-dir:
    summary_by_service.csv  - total cost per service
    summary_by_date.csv     - total cost per date
    total.csv               - grand total cost
"""

import argparse
import csv
import os
import sys
from collections import defaultdict


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate cost dashboard CSV reports from a billing CSV file."
    )
    parser.add_argument(
        "--csv",
        required=True,
        metavar="FILE",
        help="Path to the input billing CSV file.",
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        help="Directory to write output CSV files.",
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        help="Alias for --out-dir. If both are provided, --out-dir takes precedence.",
    )
    return parser.parse_args()


def read_billing_csv(path):
    """Read billing rows from a CSV file.

    Expected columns: date, service, description, quantity, unit_price, cost, currency
    """
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                row["cost"] = float(row["cost"])
            except (KeyError, ValueError):
                pass
            rows.append(row)
    return rows


def summarise_by_service(rows):
    totals = defaultdict(float)
    currencies = defaultdict(set)
    for row in rows:
        service = row.get("service", "Unknown")
        totals[service] += row.get("cost", 0.0)
        currencies[service].add(row.get("currency", "USD"))
    return [
        {
            "service": svc,
            "total_cost": round(totals[svc], 2),
            "currency": currencies[svc].pop() if len(currencies[svc]) == 1 else "MIXED",
        }
        for svc in sorted(totals)
    ]


def summarise_by_date(rows):
    totals = defaultdict(float)
    currencies = defaultdict(set)
    for row in rows:
        date = row.get("date", "Unknown")
        totals[date] += row.get("cost", 0.0)
        currencies[date].add(row.get("currency", "USD"))
    return [
        {
            "date": d,
            "total_cost": round(totals[d], 2),
            "currency": currencies[d].pop() if len(currencies[d]) == 1 else "MIXED",
        }
        for d in sorted(totals)
    ]


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()

    out_dir = args.out_dir or args.out
    if not out_dir:
        print("error: one of --out-dir or --out is required.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.csv):
        print(f"error: input file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)

    rows = read_billing_csv(args.csv)
    if not rows:
        print(f"error: no data rows found in {args.csv}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    by_service = summarise_by_service(rows)
    write_csv(
        os.path.join(out_dir, "summary_by_service.csv"),
        ["service", "total_cost", "currency"],
        by_service,
    )

    by_date = summarise_by_date(rows)
    write_csv(
        os.path.join(out_dir, "summary_by_date.csv"),
        ["date", "total_cost", "currency"],
        by_date,
    )

    grand_total = round(sum(r["total_cost"] for r in by_service), 2)
    currencies = {row.get("currency", "USD") for row in rows}
    currency = next(iter(currencies)) if len(currencies) == 1 else "MIXED"
    write_csv(
        os.path.join(out_dir, "total.csv"),
        ["total_cost", "currency"],
        [{"total_cost": grand_total, "currency": currency}],
    )

    print(f"Reports written to {out_dir}/")
    print(f"  summary_by_service.csv  ({len(by_service)} services)")
    print(f"  summary_by_date.csv     ({len(by_date)} dates)")
    print(f"  total.csv               (grand total: {grand_total} {currency})")


if __name__ == "__main__":
    main()
