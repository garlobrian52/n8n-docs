#!/usr/bin/env python3
"""Smoke tests for cost_dashboard.py.

Run with:
    python scripts/test_cost_dashboard.py

All tests use data/sample_billing.csv (no proprietary data).
Exit code is 0 on success, non-zero on failure.
"""

import csv
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "cost_dashboard.py")
SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sample_billing.csv")

EXPECTED_OUTPUT_FILES = {"daily_totals.csv", "by_dimensions.csv", "cost_breakdown.csv"}


def run(args, **kwargs):
    return subprocess.run(
        [sys.executable, SCRIPT] + args,
        capture_output=True,
        text=True,
        **kwargs,
    )


def test_out_flag_writes_expected_csvs():
    """Behavior 1: --out writes the three expected output CSVs."""
    with tempfile.TemporaryDirectory() as out_dir:
        result = run(["--csv", SAMPLE_CSV, "--out", out_dir])
        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}\nstderr: {result.stderr}"
        )
        produced = set(os.listdir(out_dir))
        missing = EXPECTED_OUTPUT_FILES - produced
        assert not missing, f"Missing output files: {missing}"

        # Validate daily_totals.csv has a header and data rows
        with open(os.path.join(out_dir, "daily_totals.csv"), newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert rows, "daily_totals.csv is empty"
        assert "date" in rows[0] and "total_cost" in rows[0], (
            f"Unexpected columns in daily_totals.csv: {list(rows[0].keys())}"
        )

        # Validate by_dimensions.csv
        with open(os.path.join(out_dir, "by_dimensions.csv"), newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert rows, "by_dimensions.csv is empty"
        assert "dimension" in rows[0] and "total_cost" in rows[0], (
            f"Unexpected columns in by_dimensions.csv: {list(rows[0].keys())}"
        )

        # Validate cost_breakdown.csv
        with open(os.path.join(out_dir, "cost_breakdown.csv"), newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert rows, "cost_breakdown.csv is empty"
        assert "service" in rows[0] and "dimension" in rows[0] and "total_cost" in rows[0], (
            f"Unexpected columns in cost_breakdown.csv: {list(rows[0].keys())}"
        )

    print("PASS test_out_flag_writes_expected_csvs")


def test_out_dir_flag_backward_compatible():
    """Behavior 2: --out-dir still works (backward compatible)."""
    with tempfile.TemporaryDirectory() as out_dir:
        result = run(["--csv", SAMPLE_CSV, "--out-dir", out_dir])
        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}\nstderr: {result.stderr}"
        )
        produced = set(os.listdir(out_dir))
        missing = EXPECTED_OUTPUT_FILES - produced
        assert not missing, f"Missing output files: {missing}"
        assert "deprecated" in result.stderr.lower(), (
            "Expected a deprecation warning on stderr when using --out-dir"
        )

    print("PASS test_out_dir_flag_backward_compatible")


def test_both_flags_error():
    """Behavior 3: passing both --out and --out-dir exits with status 1 and a friendly message."""
    with tempfile.TemporaryDirectory() as out_dir:
        result = run(["--csv", SAMPLE_CSV, "--out", out_dir, "--out-dir", out_dir])
        assert result.returncode == 1, (
            f"Expected exit code 1, got {result.returncode}\nstderr: {result.stderr}"
        )
        assert "mutually exclusive" in result.stderr.lower() or "cannot both" in result.stderr.lower(), (
            f"Expected a friendly mutual-exclusion message on stderr, got:\n{result.stderr}"
        )

    print("PASS test_both_flags_error")


def main():
    failures = []
    for test in [
        test_out_flag_writes_expected_csvs,
        test_out_dir_flag_backward_compatible,
        test_both_flags_error,
    ]:
        try:
            test()
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failures.append(test.__name__)
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"ERROR {test.__name__}: {exc}")
            failures.append(test.__name__)

    if failures:
        print(f"\n{len(failures)} test(s) failed: {', '.join(failures)}")
        sys.exit(1)
    else:
        print(f"\nAll tests passed.")


if __name__ == "__main__":
    main()
