# Cost Dashboard Script

`scripts/cost_dashboard.py` reads a billing CSV and produces daily totals,
per-dimension, and per-service/dimension cost summaries. Results are printed to
the terminal and, optionally, written to CSV files.

## Usage

```bash
# Print summaries to the terminal only
python scripts/cost_dashboard.py --csv data/sample_billing.csv

# Write output CSVs to a directory (preferred flag)
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/

# Legacy flag – still works, prints a deprecation warning
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/
```

## Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--csv FILE` | Yes | Path to the input billing CSV. |
| `--out DIR` | No | Directory to write output CSVs into. |
| `--out-dir DIR` | No | **Deprecated.** Alias for `--out`. Use `--out` instead. |

> **Note:** `--out` and `--out-dir` are mutually exclusive. Passing both flags
> will produce an error and exit with status 1.

## Input CSV format

The input CSV must contain the following columns:

| Column | Description |
|--------|-------------|
| `date` | ISO 8601 date (`YYYY-MM-DD`) |
| `service` | Billing service name |
| `dimension` | Cost dimension (for example, `workflow_executions`) |
| `quantity` | Quantity consumed |
| `unit_price` | Price per unit |
| `cost` | Total line cost (`quantity × unit_price`) |

A sample input file is provided at `data/sample_billing.csv`.

## Output files

When `--out` is provided, the script creates three CSV files in the target
directory:

| File | Contents |
|------|----------|
| `daily_totals.csv` | Total cost grouped by date |
| `by_dimensions.csv` | Total cost grouped by dimension |
| `cost_breakdown.csv` | Total cost grouped by service and dimension |

## Examples

```bash
# Using the preferred --out flag
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/

# Using the deprecated --out-dir flag (still works, shows a deprecation warning)
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/

# Error: passing both flags exits with status 1
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/ --out-dir out/
# error: --out and --out-dir are mutually exclusive. Use --out (--out-dir is deprecated).
```

## Running the smoke tests

```bash
python scripts/test_cost_dashboard.py
```
