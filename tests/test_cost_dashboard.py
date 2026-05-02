"""Tests for scripts/cost_dashboard.py."""

import csv
import os
import types

import pytest

# ---------------------------------------------------------------------------
# Helpers to import the module under test without requiring it to be a package
# ---------------------------------------------------------------------------

import importlib.util

_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "cost_dashboard.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("cost_dashboard", _SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Cannot load module from {_SCRIPT!r}: "
            "spec_from_file_location returned None. "
            "Check that the script path is correct and the file exists."
        )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cd = _load_module()


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


def test_parse_args_csv_only(tmp_path):
    csv_file = str(tmp_path / "billing.csv")
    args = cd.parse_args(["--csv", csv_file])
    assert args.csv == csv_file
    assert args.out is None
    assert args.out_dir is None


def test_parse_args_with_out(tmp_path):
    csv_file = str(tmp_path / "billing.csv")
    args = cd.parse_args(["--csv", csv_file, "--out", "outdir/"])
    assert args.out == "outdir/"
    assert args.out_dir is None


def test_parse_args_with_out_dir(tmp_path):
    csv_file = str(tmp_path / "billing.csv")
    args = cd.parse_args(["--csv", csv_file, "--out-dir", "legacy/"])
    assert args.out is None
    assert args.out_dir == "legacy/"


def test_parse_args_missing_csv():
    with pytest.raises(SystemExit):
        cd.parse_args([])


# ---------------------------------------------------------------------------
# resolve_output_dir
# ---------------------------------------------------------------------------


def _make_args(out=None, out_dir=None):
    return types.SimpleNamespace(out=out, out_dir=out_dir)


def test_resolve_output_dir_only_out():
    args = _make_args(out="mydir/")
    assert cd.resolve_output_dir(args) == "mydir/"


def test_resolve_output_dir_only_out_dir():
    args = _make_args(out_dir="legacydir/")
    assert cd.resolve_output_dir(args) == "legacydir/"


def test_resolve_output_dir_neither():
    args = _make_args()
    assert cd.resolve_output_dir(args) is None


def test_resolve_output_dir_both_raises(capsys):
    args = _make_args(out="a/", out_dir="b/")
    with pytest.raises(SystemExit):
        cd.resolve_output_dir(args)
    captured = capsys.readouterr()
    assert "mutually exclusive" in captured.err


# ---------------------------------------------------------------------------
# read_billing
# ---------------------------------------------------------------------------


def test_read_billing(tmp_path):
    billing = tmp_path / "billing.csv"
    billing.write_text("date,service,dimension,cost\n2024-01-01,Compute,prod,100.00\n")
    rows = cd.read_billing(str(billing))
    assert len(rows) == 1
    assert rows[0]["date"] == "2024-01-01"
    assert rows[0]["cost"] == "100.00"


# ---------------------------------------------------------------------------
# compute_daily_totals
# ---------------------------------------------------------------------------


def test_compute_daily_totals():
    rows = [
        {"date": "2024-01-01", "cost": "100.00"},
        {"date": "2024-01-01", "cost": "50.00"},
        {"date": "2024-01-02", "cost": "75.50"},
    ]
    result = cd.compute_daily_totals(rows)
    assert result == [
        {"date": "2024-01-01", "total_cost": 150.00},
        {"date": "2024-01-02", "total_cost": 75.50},
    ]


def test_compute_daily_totals_sorted():
    rows = [
        {"date": "2024-01-03", "cost": "10.00"},
        {"date": "2024-01-01", "cost": "20.00"},
    ]
    result = cd.compute_daily_totals(rows)
    assert result[0]["date"] == "2024-01-01"
    assert result[1]["date"] == "2024-01-03"


# ---------------------------------------------------------------------------
# compute_by_dimensions
# ---------------------------------------------------------------------------


def test_compute_by_dimensions():
    rows = [
        {"dimension": "prod", "cost": "100.00"},
        {"dimension": "dev", "cost": "40.00"},
        {"dimension": "prod", "cost": "20.00"},
    ]
    result = cd.compute_by_dimensions(rows)
    assert {"dimension": "dev", "total_cost": 40.00} in result
    assert {"dimension": "prod", "total_cost": 120.00} in result


# ---------------------------------------------------------------------------
# compute_cost_breakdown
# ---------------------------------------------------------------------------


def test_compute_cost_breakdown():
    rows = [
        {"service": "Compute", "cost": "200.00"},
        {"service": "Storage", "cost": "50.00"},
        {"service": "Compute", "cost": "100.00"},
    ]
    result = cd.compute_cost_breakdown(rows)
    totals = {r["service"]: r["total_cost"] for r in result}
    assert totals["Compute"] == 300.00
    assert totals["Storage"] == 50.00


# ---------------------------------------------------------------------------
# _sum_by – error paths
# ---------------------------------------------------------------------------


def test_sum_by_missing_key_field(capsys):
    rows = [{"cost": "10.00"}]  # no "date" field
    with pytest.raises(SystemExit):
        cd._sum_by(rows, "date")
    assert "missing required column" in capsys.readouterr().err


def test_sum_by_invalid_cost(capsys):
    rows = [{"date": "2024-01-01", "cost": "bad"}]
    with pytest.raises(SystemExit):
        cd._sum_by(rows, "date")
    assert "invalid cost value" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# write_csv
# ---------------------------------------------------------------------------


def test_write_csv(tmp_path):
    out_file = str(tmp_path / "sub" / "output.csv")
    rows = [{"date": "2024-01-01", "total_cost": 100.0}]
    cd.write_csv(out_file, ["date", "total_cost"], rows)
    with open(out_file, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        written = list(reader)
    assert written == [{"date": "2024-01-01", "total_cost": "100.0"}]


# ---------------------------------------------------------------------------
# main – end-to-end
# ---------------------------------------------------------------------------


def test_main_no_out_dir(tmp_path, capsys):
    billing = tmp_path / "billing.csv"
    billing.write_text(
        "date,service,dimension,cost\n"
        "2024-01-01,Compute,prod,100.00\n"
        "2024-01-01,Storage,dev,50.00\n"
    )
    cd.main(["--csv", str(billing)])
    captured = capsys.readouterr()
    assert "Daily Totals" in captured.out
    assert "2024-01-01" in captured.out


def test_main_with_out(tmp_path, capsys):
    billing = tmp_path / "billing.csv"
    billing.write_text(
        "date,service,dimension,cost\n"
        "2024-01-01,Compute,prod,100.00\n"
    )
    out_dir = str(tmp_path / "out")
    cd.main(["--csv", str(billing), "--out", out_dir])
    assert os.path.isfile(os.path.join(out_dir, "daily_totals.csv"))
    assert os.path.isfile(os.path.join(out_dir, "by_dimensions.csv"))
    assert os.path.isfile(os.path.join(out_dir, "cost_breakdown.csv"))


def test_main_with_out_dir(tmp_path):
    billing = tmp_path / "billing.csv"
    billing.write_text(
        "date,service,dimension,cost\n"
        "2024-01-01,Compute,prod,100.00\n"
    )
    out_dir = str(tmp_path / "legacy_out")
    cd.main(["--csv", str(billing), "--out-dir", out_dir])
    assert os.path.isfile(os.path.join(out_dir, "daily_totals.csv"))


def test_main_mutual_exclusion_error(tmp_path, capsys):
    billing = tmp_path / "billing.csv"
    billing.write_text("date,service,dimension,cost\n2024-01-01,Compute,prod,100.00\n")
    with pytest.raises(SystemExit):
        cd.main(["--csv", str(billing), "--out", "a/", "--out-dir", "b/"])
    assert "mutually exclusive" in capsys.readouterr().err


def test_main_with_sample_billing(capsys):
    sample = os.path.join(
        os.path.dirname(__file__), "..", "data", "sample_billing.csv"
    )
    if not os.path.isfile(sample):
        pytest.skip("data/sample_billing.csv not present")
    cd.main(["--csv", sample])
    captured = capsys.readouterr()
    assert "Daily Totals" in captured.out
    assert "Spend by Dimension" in captured.out
    assert "Cost Breakdown by Service" in captured.out
