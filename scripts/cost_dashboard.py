#!/usr/bin/env python3
"""cost_dashboard.py - Ingest a billing CSV and print summary tables.

Usage:
    python scripts/cost_dashboard.py --csv data/sample_billing.csv
    python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/
    python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/  # legacy
"""

import argparse
import csv
import os
import sys
from collections import defaultdict


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Ingest a billing CSV and print cost summary tables.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Print summary tables to stdout
  python scripts/cost_dashboard.py --csv data/sample_billing.csv

  # Write output CSVs to a directory
  python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/

  # Legacy flag (deprecated, use --out instead)
  python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/
""",
    )
    parser.add_argument(
        "--csv",
        required=True,
        metavar="FILE",
        help="Path to the input billing CSV file.",
    )
    parser.add_argument(
        "--out",
        default=None,
        metavar="DIR",
        help="Directory to write output CSV files (daily_totals.csv, by_dimensions.csv, cost_breakdown.csv).",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        metavar="DIR",
        dest="out_dir",
        help="(Deprecated) Use --out instead. Directory to write output CSV files.",
    )
    return parser.parse_args(argv)


def resolve_output_dir(args):
    """Return the output directory, or None if not specified.

    Exits with status 1 if both --out and --out-dir are provided.
    """
    if args.out is not None and args.out_dir is not None:
        print(
            "error: --out and --out-dir are mutually exclusive. "
            "Use --out (--out-dir is deprecated).",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.out is not None:
        return args.out
    if args.out_dir is not None:
        print(
            "warning: --out-dir is deprecated. Use --out instead.",
            file=sys.stderr,
        )
        return args.out_dir
    return None


def load_billing_csv(path):
    """Load billing rows from a CSV file.

    Expected columns: date, service, dimension, quantity, unit_price, cost
    """
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(
                {
                    "date": row["date"],
                    "service": row["service"],
                    "dimension": row["dimension"],
                    "quantity": float(row["quantity"]),
                    "unit_price": float(row["unit_price"]),
                    "cost": float(row["cost"]),
                }
            )
    return rows


def compute_daily_totals(rows):
    """Aggregate total cost per date."""
    totals = defaultdict(float)
    for row in rows:
        totals[row["date"]] += row["cost"]
    return [{"date": d, "total_cost": round(v, 6)} for d, v in sorted(totals.items())]


def compute_by_dimensions(rows):
    """Aggregate total cost per dimension."""
    totals = defaultdict(float)
    for row in rows:
        totals[row["dimension"]] += row["cost"]
    return [
        {"dimension": d, "total_cost": round(v, 6)}
        for d, v in sorted(totals.items())
    ]


def compute_cost_breakdown(rows):
    """Aggregate total cost per service + dimension combination."""
    totals = defaultdict(float)
    for row in rows:
        key = (row["service"], row["dimension"])
        totals[key] += row["cost"]
    return [
        {"service": s, "dimension": d, "total_cost": round(v, 6)}
        for (s, d), v in sorted(totals.items())
    ]


def print_table(title, fieldnames, data):
    """Print a simple text table to stdout."""
    col_widths = {f: len(f) for f in fieldnames}
    for row in data:
        for f in fieldnames:
            col_widths[f] = max(col_widths[f], len(str(row[f])))

    header = "  ".join(f.ljust(col_widths[f]) for f in fieldnames)
    separator = "  ".join("-" * col_widths[f] for f in fieldnames)
    print(f"\n{title}")
    print(separator)
    print(header)
    print(separator)
    for row in data:
        print("  ".join(str(row[f]).ljust(col_widths[f]) for f in fieldnames))
    print(separator)


def write_csv(path, fieldnames, data):
    """Write rows to a CSV file."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Wrote {path}", file=sys.stderr)


def main(argv=None):
    args = parse_args(argv)
    out_dir = resolve_output_dir(args)

    rows = load_billing_csv(args.csv)

    daily_totals = compute_daily_totals(rows)
    by_dimensions = compute_by_dimensions(rows)
    cost_breakdown = compute_cost_breakdown(rows)

    print_table("Daily Totals", ["date", "total_cost"], daily_totals)
    print_table("Spend by Dimension", ["dimension", "total_cost"], by_dimensions)
    print_table(
        "Cost Breakdown",
        ["service", "dimension", "total_cost"],
        cost_breakdown,
    )

    if out_dir is not None:
        write_csv(
            os.path.join(out_dir, "daily_totals.csv"),
            ["date", "total_cost"],
            daily_totals,
        )
        write_csv(
            os.path.join(out_dir, "by_dimensions.csv"),
            ["dimension", "total_cost"],
            by_dimensions,
        )
        write_csv(
            os.path.join(out_dir, "cost_breakdown.csv"),
            ["service", "dimension", "total_cost"],
            cost_breakdown,
        )


if __name__ == "__main__":
    main()
