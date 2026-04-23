# Cost Dashboard Script

`scripts/cost_dashboard.py` reads a billing CSV and produces per-service,
per-month, and per-project cost summaries. Results are printed to the terminal
and, optionally, written to CSV files.

## Usage

```bash
# Print summaries to the terminal only
python scripts/cost_dashboard.py --csv data/sample_billing.csv

# Write output CSVs to a directory
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/
```

## Arguments

| Flag | Required | Description |
|------|----------|-------------|
| `--csv PATH` | Yes | Path to the input billing CSV. |
| `--out DIR` | No | Directory to write output CSVs into. |
| `--out-dir DIR` | No | **Deprecated.** Alias for `--out`. Use `--out` instead. |

> **Note:** `--out` and `--out-dir` are mutually exclusive. Passing both flags
> will produce an error and exit with status 1.

## Input CSV format

The input CSV must contain at minimum these columns:

| Column | Description |
|--------|-------------|
| `date` | ISO 8601 date (`YYYY-MM-DD`) |
| `service` | Cloud service name |
| `project` | Project identifier |
| `amount_usd` | Cost in USD |

A sample input file is provided at `data/sample_billing.csv`.

## Output files

When `--out` is provided, the script creates three CSV files in the target
directory:

| File | Contents |
|------|----------|
| `summary_by_service.csv` | Total cost grouped by service |
| `summary_by_month.csv` | Total cost grouped by month (`YYYY-MM`) |
| `summary_by_project.csv` | Total cost grouped by project |

## Examples

```bash
# Using the preferred --out flag
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/

# Using the deprecated --out-dir flag (still works, shows a deprecation warning)
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out-dir out/

# Error: passing both flags exits with status 1
python scripts/cost_dashboard.py --csv data/sample_billing.csv --out out/ --out-dir out/
# ERROR: --out and --out-dir cannot both be specified. Use --out (--out-dir is deprecated).
```
