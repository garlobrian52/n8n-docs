#!/usr/bin/env python3
"""Cost Dashboard CLI

Ingests a billing CSV and prints three summary tables:
  1. Daily totals with day-over-day change.
  2. Spend by dimensions (Organization Plan, Entity Name, Entity Type, CSP,
     Region, Warehouse ID, Service ID).
  3. Cost-component breakdown summing each ``... ($)`` money column.

Usage
-----
  python scripts/cost_dashboard.py --csv data/sample_billing.csv

  # Write CSV outputs to a directory
  python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/
  python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/

Flags
-----
--csv       Path to the input billing CSV.  (required)
--out       Output directory for CSV files.  (preferred spelling)
--out-dir   Output directory for CSV files.  (legacy alias; cannot be combined
            with --out)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Column helpers
# ---------------------------------------------------------------------------

DIMENSION_COLS = [
    "Organization Plan",
    "Entity Name",
    "Entity Type",
    "CSP",
    "Region",
    "Warehouse ID",
    "Service ID",
]


def _money_columns(df: pd.DataFrame) -> list[str]:
    """Return all columns whose names end with ' ($)'."""
    return [c for c in df.columns if c.endswith(" ($)")]


def _total_column(money_cols: list[str]) -> str | None:
    """Return the name of the Total column, if present."""
    for col in money_cols:
        if col.lower().startswith("total"):
            return col
    return None


def _component_columns(money_cols: list[str]) -> list[str]:
    """Return money columns that are *not* the Total column."""
    return [c for c in money_cols if not c.lower().startswith("total")]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load the billing CSV, coercing money columns to numeric.

    Blank or non-numeric values in money columns are treated as 0.0.
    A warning is printed to stderr for each column that contains values
    requiring coercion.
    """
    try:
        df = pd.read_csv(path, parse_dates=["Date"])
    except FileNotFoundError:
        print(f"error: CSV file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not read CSV file: {exc}", file=sys.stderr)
        sys.exit(1)

    money_cols = _money_columns(df)
    for col in money_cols:
        coerced = pd.to_numeric(df[col], errors="coerce")
        n_bad = coerced.isna().sum() - df[col].isna().sum()
        if n_bad > 0:
            print(
                f"warning: {n_bad} non-numeric value(s) in column '{col}' "
                "coerced to 0.0",
                file=sys.stderr,
            )
        df[col] = coerced.fillna(0.0)
    return df


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------


def daily_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Table 1 – Daily totals with day-over-day change.

    Columns: Date, total_usd, dod_change
    """
    money_cols = _money_columns(df)
    total_col = _total_column(money_cols)

    if total_col:
        daily = df.groupby("Date")[total_col].sum().reset_index()
        daily.rename(columns={total_col: "total_usd"}, inplace=True)
    else:
        # Fall back: sum all money columns
        daily = df.groupby("Date")[money_cols].sum()
        daily["total_usd"] = daily.sum(axis=1)
        daily = daily[["total_usd"]].reset_index()

    daily.sort_values("Date", inplace=True)
    daily["dod_change"] = daily["total_usd"].diff()
    daily.reset_index(drop=True, inplace=True)
    return daily


def spend_by_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    """Table 2 – Spend aggregated by billing dimensions.

    Columns: all DIMENSION_COLS present + total_usd
    """
    money_cols = _money_columns(df)
    total_col = _total_column(money_cols)

    present_dims = [c for c in DIMENSION_COLS if c in df.columns]

    if total_col:
        agg = df.groupby(present_dims)[total_col].sum().reset_index()
        agg.rename(columns={total_col: "total_usd"}, inplace=True)
    else:
        agg = df.groupby(present_dims)[money_cols].sum()
        agg["total_usd"] = agg.sum(axis=1)
        agg = agg[["total_usd"]].reset_index()

    agg.sort_values("total_usd", ascending=False, inplace=True)
    agg.reset_index(drop=True, inplace=True)
    return agg


def cost_components(df: pd.DataFrame) -> pd.DataFrame:
    """Table 3 – Cost-component breakdown.

    Each ``... ($)`` column (excluding Total) is summed; a Total row is
    appended.
    """
    money_cols = _money_columns(df)
    total_col = _total_column(money_cols)
    component_cols = _component_columns(money_cols)

    sums = {col: df[col].sum() for col in component_cols}
    rows = [{"component": col, "total_usd": val} for col, val in sums.items()]

    if total_col:
        rows.append({"component": total_col, "total_usd": df[total_col].sum()})

    result = pd.DataFrame(rows, columns=["component", "total_usd"])
    return result


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _print_table(title: str, df: pd.DataFrame) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)
    print(df.to_string(index=False))


def _write_csvs(out_dir: Path, tables: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, df in tables.items():
        dest = out_dir / filename
        df.to_csv(dest, index=False)
        print(f"Wrote {dest}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest a billing CSV and print cost-summary tables.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--csv",
        required=True,
        metavar="PATH",
        help="Path to the input billing CSV.",
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        default=None,
        help="Output directory for CSV files (preferred flag).",
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        default=None,
        dest="out_dir",
        help="Output directory for CSV files (legacy alias for --out).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Conflict detection: both --out and --out-dir supplied
    if args.out is not None and args.out_dir is not None:
        print(
            "error: --out and --out-dir are mutually exclusive; "
            "use --out (preferred) or --out-dir (legacy), not both.",
            file=sys.stderr,
        )
        return 1

    # Resolve output directory (prefer --out, fall back to --out-dir)
    out_dir: Path | None = None
    if args.out is not None:
        out_dir = Path(args.out)
    elif args.out_dir is not None:
        out_dir = Path(args.out_dir)

    # Load data
    df = load_csv(args.csv)

    # Build tables
    tbl_daily = daily_totals(df)
    tbl_dimensions = spend_by_dimensions(df)
    tbl_components = cost_components(df)

    # Print to stdout
    _print_table("Table 1: Daily Totals", tbl_daily)
    _print_table("Table 2: Spend by Dimensions", tbl_dimensions)
    _print_table("Table 3: Cost-Component Breakdown", tbl_components)

    # Write CSVs if requested
    if out_dir is not None:
        _write_csvs(
            out_dir,
            {
                "daily_totals.csv": tbl_daily,
                "spend_by_dimensions.csv": tbl_dimensions,
                "cost_components.csv": tbl_components,
            },
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
