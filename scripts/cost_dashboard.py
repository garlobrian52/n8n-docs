#!/usr/bin/env python3
"""Cost dashboard CLI.

Ingests a billing CSV and writes summary tables.

Usage examples::

    # Preferred flag:
    python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/

    # Legacy/deprecated flag (kept for backward compatibility):
    python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/

Output files written to the chosen directory:
  - daily_totals.csv
  - by_dimensions.csv
  - cost_breakdown.csv

Langfuse tracing is enabled automatically when LANGFUSE_PUBLIC_KEY,
LANGFUSE_SECRET_KEY, and LANGFUSE_HOST environment variables are set.
"""

import argparse
import csv
import os
import sys
from collections import defaultdict

try:
    from langfuse.decorators import langfuse_context, observe

    _LANGFUSE_AVAILABLE = True
except ImportError:
    _LANGFUSE_AVAILABLE = False

    def observe(*args, **kwargs):  # type: ignore[misc]
        """No-op shim when langfuse is not installed."""

        def decorator(func):
            return func

        return decorator if not args else decorator(args[0])

    class _LangfuseContextStub:
        def update_current_observation(self, **kwargs):
            pass

        def update_current_trace(self, **kwargs):
            pass

        def flush(self):
            pass

    langfuse_context = _LangfuseContextStub()  # type: ignore[assignment]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Ingest a billing CSV and write cost summary tables.",
    )
    parser.add_argument(
        "--csv",
        required=True,
        metavar="PATH",
        help="Path to the input billing CSV file.",
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        default=None,
        help="Directory to write output CSV files (preferred flag).",
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        default=None,
        dest="out_dir",
        help="Directory to write output CSV files (deprecated; use --out instead).",
    )
    return parser.parse_args(argv)


def resolve_output_dir(args):
    """Return the effective output directory or None, enforcing mutual exclusion."""
    if args.out is not None and args.out_dir is not None:
        print(
            "error: --out and --out-dir are mutually exclusive. "
            "Please specify only one.",
            file=sys.stderr,
        )
        sys.exit(1)
    return args.out if args.out is not None else args.out_dir


@observe()
def read_billing(csv_path):
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    langfuse_context.update_current_observation(
        input={"csv_path": csv_path},
        output={"row_count": len(rows)},
    )
    return rows


_COST_DECIMALS = 2


def _sum_by(rows, key_field):
    """Accumulate costs grouped by key_field and return rounded totals."""
    totals = defaultdict(float)
    for i, row in enumerate(rows, start=2):
        key = row.get(key_field)
        if key is None:
            print(
                f"error: row {i} is missing required column '{key_field}'.",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            totals[key] += float(row["cost"])
        except (KeyError, ValueError) as exc:
            print(f"error: row {i} has invalid cost value: {exc}", file=sys.stderr)
            sys.exit(1)
    return {k: round(v, _COST_DECIMALS) for k, v in sorted(totals.items())}


@observe()
def compute_daily_totals(rows):
    result = [
        {"date": d, "total_cost": t} for d, t in _sum_by(rows, "date").items()
    ]
    langfuse_context.update_current_observation(
        input={"row_count": len(rows)},
        output={"days": len(result)},
    )
    return result


@observe()
def compute_by_dimensions(rows):
    result = [
        {"dimension": dim, "total_cost": t}
        for dim, t in _sum_by(rows, "dimension").items()
    ]
    langfuse_context.update_current_observation(
        input={"row_count": len(rows)},
        output={"dimensions": len(result)},
    )
    return result


@observe()
def compute_cost_breakdown(rows):
    result = [
        {"service": svc, "total_cost": t}
        for svc, t in _sum_by(rows, "service").items()
    ]
    langfuse_context.update_current_observation(
        input={"row_count": len(rows)},
        output={"services": len(result)},
    )
    return result


def write_csv(path, fieldnames, rows):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_table(title, rows, fields):
    print(f"\n=== {title} ===")
    header = "  ".join(f"{f:<20}" for f in fields)
    print(header)
    print("-" * len(header))
    for row in rows:
        print("  ".join(f"{str(row[f]):<20}" for f in fields))


@observe(name="cost-dashboard-run")
def main(argv=None):
    args = parse_args(argv)
    out_dir = resolve_output_dir(args)

    langfuse_context.update_current_trace(
        input={"csv": args.csv, "out_dir": out_dir},
    )

    rows = read_billing(args.csv)

    daily = compute_daily_totals(rows)
    by_dim = compute_by_dimensions(rows)
    breakdown = compute_cost_breakdown(rows)

    print_table("Daily Totals", daily, ["date", "total_cost"])
    print_table("Spend by Dimension", by_dim, ["dimension", "total_cost"])
    print_table("Cost Breakdown by Service", breakdown, ["service", "total_cost"])

    if out_dir is not None:
        os.makedirs(out_dir, exist_ok=True)
        write_csv(os.path.join(out_dir, "daily_totals.csv"), ["date", "total_cost"], daily)
        write_csv(
            os.path.join(out_dir, "by_dimensions.csv"),
            ["dimension", "total_cost"],
            by_dim,
        )
        write_csv(
            os.path.join(out_dir, "cost_breakdown.csv"),
            ["service", "total_cost"],
            breakdown,
        )
        print(f"\nOutput written to: {out_dir}")
        print("  daily_totals.csv")
        print("  by_dimensions.csv")
        print("  cost_breakdown.csv")

    langfuse_context.update_current_trace(
        output={
            "row_count": len(rows),
            "days": len(daily),
            "dimensions": len(by_dim),
            "services": len(breakdown),
        },
    )
    langfuse_context.flush()


if __name__ == "__main__":
    main()
