#!/usr/bin/env python3
"""cost_dashboard.py – Summarise a billing CSV and write output CSVs.

Usage examples
--------------
# Show summary tables in the terminal only:
    python scripts/cost_dashboard.py --csv data/sample_billing.csv

# Write output CSVs to the ``out/`` directory (preferred flag):
    python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/

# Legacy flag (deprecated, kept for backward compatibility):
    python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/
"""

import argparse
import csv
import os
import sys
from collections import defaultdict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_billing(csv_path: str) -> list[dict]:
    """Return rows from *csv_path* as a list of dicts."""
    with open(csv_path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _summarise(rows: list[dict]) -> tuple[dict, dict, dict]:
    """Return (by_service, by_month, by_project) aggregation dicts."""
    by_service: dict[str, float] = defaultdict(float)
    by_month: dict[str, float] = defaultdict(float)
    by_project: dict[str, float] = defaultdict(float)

    for row in rows:
        amount = float(row["amount_usd"])
        by_service[row["service"]] += amount
        # month key: YYYY-MM derived from the date column (YYYY-MM-DD)
        month = row["date"][:7]
        by_month[month] += amount
        by_project[row["project"]] += amount

    return dict(by_service), dict(by_month), dict(by_project)


def _write_csv(path: str, fieldnames: list[str], rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _print_table(title: str, data: dict, key_header: str) -> None:
    print(f"\n=== {title} ===")
    print(f"  {key_header:<30} amount_usd")
    print(f"  {'-'*30} ----------")
    for key, total in sorted(data.items()):
        print(f"  {key:<30} {total:>10.2f}")


def _to_rows(data: dict, key_field: str) -> list[dict]:
    """Convert an aggregation dict to a list of CSV row dicts."""
    return [
        {key_field: k, "amount_usd": f"{v:.2f}"}
        for k, v in sorted(data.items())
    ]


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cost_dashboard.py",
        description="Summarise a billing CSV and optionally write output CSVs.",
    )
    parser.add_argument(
        "--csv",
        required=True,
        metavar="PATH",
        help="Path to the input billing CSV file.",
    )
    parser.add_argument(
        "--out",
        default=None,
        metavar="DIR",
        help="Directory to write output CSVs into.",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        metavar="DIR",
        dest="out_dir",
        help="(Deprecated) Alias for --out. Use --out instead.",
    )
    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Mutual-exclusion check
    if args.out is not None and args.out_dir is not None:
        print(
            "ERROR: --out and --out-dir cannot both be specified. "
            "Use --out (--out-dir is deprecated).",
            file=sys.stderr,
        )
        return 1

    # Resolve the effective output directory (prefer --out over --out-dir)
    out_dir: str | None = args.out if args.out is not None else args.out_dir

    if args.out_dir is not None:
        print(
            "WARNING: --out-dir is deprecated and will be removed in a future "
            "release. Use --out instead.",
            file=sys.stderr,
        )

    # Read and summarise
    try:
        rows = _read_billing(args.csv)
    except FileNotFoundError:
        print(f"ERROR: input file not found: {args.csv}", file=sys.stderr)
        return 1

    by_service, by_month, by_project = _summarise(rows)

    # Print to terminal
    _print_table("Cost by Service", by_service, "service")
    _print_table("Cost by Month", by_month, "month")
    _print_table("Cost by Project", by_project, "project")

    # Write CSVs when an output directory was requested
    if out_dir is not None:
        _write_csv(
            os.path.join(out_dir, "summary_by_service.csv"),
            ["service", "amount_usd"],
            _to_rows(by_service, "service"),
        )
        _write_csv(
            os.path.join(out_dir, "summary_by_month.csv"),
            ["month", "amount_usd"],
            _to_rows(by_month, "month"),
        )
        _write_csv(
            os.path.join(out_dir, "summary_by_project.csv"),
            ["project", "amount_usd"],
            _to_rows(by_project, "project"),
        )
        print(f"\nOutput CSVs written to: {out_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
