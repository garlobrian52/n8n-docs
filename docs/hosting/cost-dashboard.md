# Cost dashboard CLI

The `scripts/cost_dashboard.py` script ingests a billing CSV file and prints
cost summary tables to standard output. You can optionally write the summaries
as CSV files to an output directory.

## Requirements

- Python 3.8 or later (no third-party dependencies required)

## Input CSV format

The input file must be a [CSV](https://docs.python.org/3/library/csv.html) with the following columns:

| Column | Description |
|--------|-------------|
| `date` | ISO-8601 date (for example, `2024-01-01`) |
| `service` | Billing service name |
| `dimension` | Cost dimension (for example, `workflow_executions`) |
| `quantity` | Quantity consumed |
| `unit_price` | Price per unit |
| `cost` | Total line cost (`quantity × unit_price`) |

A sample file is available at `data/sample_billing.csv`.

## Usage

### Print summary tables

```bash
python scripts/cost_dashboard.py --csv data/sample_billing.csv
```

The script prints three tables:

- **Daily Totals** – total cost per day
- **Spend by Dimension** – total cost per cost dimension
- **Cost Breakdown** – total cost per service and dimension combination

### Write output CSV files

Use `--out <dir>` to write the summary tables as CSV files:

```bash
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/
```

This creates three files in the `out/` directory:

| File | Contents |
|------|----------|
| `daily_totals.csv` | Daily cost totals |
| `by_dimensions.csv` | Cost totals by dimension |
| `cost_breakdown.csv` | Cost totals by service and dimension |

## Flags

| Flag | Description |
|------|-------------|
| `--csv FILE` | **(Required)** Path to the input billing CSV file |
| `--out DIR` | Directory to write output CSV files |
| `--out-dir DIR` | **(Deprecated)** Alias for `--out`. Use `--out` in new scripts |

/// warning | Deprecated flag
`--out-dir` is kept for backward compatibility. Use `--out` in all new
scripts and pipelines.
///

Passing both `--out` and `--out-dir` at the same time exits with status `1`
and prints a descriptive error message.

## Examples

```bash
# Print to stdout only
python scripts/cost_dashboard.py --csv data/sample_billing.csv

# Write CSVs to the out/ directory (preferred)
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/

# Write CSVs using the legacy flag (deprecated)
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/

# Passing both flags produces an error
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/ --out-dir out/
# error: --out and --out-dir are mutually exclusive. Use --out (--out-dir is deprecated).
```
