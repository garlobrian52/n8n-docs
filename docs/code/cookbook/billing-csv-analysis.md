---
title: Analyze a billing CSV
description: Ingest a billing CSV and produce summary tables using Python (pandas) or SQL (DuckDB) inside the n8n Code node.
contentType: howto
---

# Analyze a billing CSV

This page shows how to ingest a billing CSV and produce three common summary tables inside the n8n [Code node](/integrations/builtin/core-nodes/n8n-nodes-base.code/index.md):

1. **Daily totals** – total spend per day with a day-over-day change column.
2. **Spend by dimensions** – spend broken down by any combination of `Organization Plan`, `Entity Type`, `CSP`, and `Region`.
3. **Cost-component breakdown** – `Service Compute ($)` vs other charges, derived from `Total ($)`.

Both a **Python (pandas)** and a **SQL (DuckDB)** version are provided. All examples use the same synthetic CSV snippet so you can paste them straight into the Code node and run them without any external data.

/// note | Code node language
Switch the Code node **Language** dropdown to **Python** or keep it as **JavaScript** and adapt the logic. The examples below match the language selection shown in the tabs.
///

## Sample billing CSV

Use this tiny synthetic CSV to test the examples. In a real workflow the CSV arrives as binary data from a previous node, such as the [Read/Write Files from Disk](/integrations/builtin/core-nodes/n8n-nodes-base.readwritefile.md) node or an [HTTP Request](/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/index.md) node.

```csv
Date,Organization Plan,Entity Name,Entity Type,Warehouse ID,Service ID,CSP,Region,Service Compute ($),Total ($)
2024-01-01,Standard,Acme Corp,Customer,WH-001,SVC-A,AWS,us-east-1,120.50,135.00
2024-01-01,Standard,Globex Inc,Reseller,WH-002,SVC-B,GCP,us-central1,80.00,92.00
2024-01-01,Premium,Initech LLC,Customer,WH-003,SVC-A,Azure,eastus,200.00,215.00
2024-01-02,Standard,Acme Corp,Customer,WH-001,SVC-A,AWS,us-east-1,130.00,145.50
2024-01-02,Standard,Globex Inc,Reseller,WH-002,SVC-B,GCP,us-central1,75.00,88.00
2024-01-02,Premium,Initech LLC,Customer,WH-003,SVC-A,Azure,eastus,210.00,226.00
2024-01-03,Standard,Acme Corp,Customer,WH-001,SVC-A,AWS,us-east-1,115.00,128.00
2024-01-03,Standard,Globex Inc,Reseller,WH-002,SVC-B,GCP,us-central1,82.00,94.00
2024-01-03,Premium,Initech LLC,Customer,WH-003,SVC-A,Azure,eastus,205.00,221.00
```

## Python (pandas) examples

The examples below assume the CSV text is stored in the first input item:

```python
# $input.first().json.csv_text contains the raw CSV string delivered by a
# previous node (for example, a Read/Write Files from Disk node that reads the
# file as text, or an HTTP Request node returning the CSV body).
import io, pandas as pd

csv_text = _input.first().json["csv_text"]
df = pd.read_csv(io.StringIO(csv_text))

# Ensure numeric columns are parsed correctly
df["Service Compute ($)"] = pd.to_numeric(df["Service Compute ($)"], errors="coerce")
df["Total ($)"] = pd.to_numeric(df["Total ($)"], errors="coerce")

# Parse date column
df["Date"] = pd.to_datetime(df["Date"])
```

### Daily totals with day-over-day change

```python
import io, pandas as pd

csv_text = _input.first().json["csv_text"]
df = pd.read_csv(io.StringIO(csv_text))
df["Date"] = pd.to_datetime(df["Date"])
df["Service Compute ($)"] = pd.to_numeric(df["Service Compute ($)"], errors="coerce")
df["Total ($)"] = pd.to_numeric(df["Total ($)"], errors="coerce")

daily = (
    df.groupby("Date", as_index=False)
    .agg(
        service_compute=("Service Compute ($)", "sum"),
        total=("Total ($)", "sum"),
    )
    .sort_values("Date")
)

daily["prev_total"] = daily["total"].shift(1)
daily["dod_change"] = daily["total"] - daily["prev_total"]
daily["dod_pct"] = (daily["dod_change"] / daily["prev_total"] * 100).round(2)
daily = daily.drop(columns=["prev_total"])

# Return each row as an n8n item
return [{"json": row} for row in daily.to_dict(orient="records")]
```

**Output columns:** `Date`, `service_compute`, `total`, `dod_change`, `dod_pct`

### Spend by dimensions

Adjust `group_cols` to any combination of the dimension columns.

```python
import io, pandas as pd

csv_text = _input.first().json["csv_text"]
df = pd.read_csv(io.StringIO(csv_text))
df["Service Compute ($)"] = pd.to_numeric(df["Service Compute ($)"], errors="coerce")
df["Total ($)"] = pd.to_numeric(df["Total ($)"], errors="coerce")

group_cols = ["Organization Plan", "Entity Type", "CSP", "Region"]

by_dims = (
    df.groupby(group_cols, as_index=False)
    .agg(
        service_compute=("Service Compute ($)", "sum"),
        total=("Total ($)", "sum"),
    )
    .sort_values("total", ascending=False)
)

return [{"json": row} for row in by_dims.to_dict(orient="records")]
```

**Output columns:** `Organization Plan`, `Entity Type`, `CSP`, `Region`, `service_compute`, `total`

### Cost-component breakdown

`Service Compute ($)` is one known cost component. The remainder (`other_charges`) is `Total ($) - Service Compute ($)`.

```python
import io, pandas as pd

csv_text = _input.first().json["csv_text"]
df = pd.read_csv(io.StringIO(csv_text))
df["Service Compute ($)"] = pd.to_numeric(df["Service Compute ($)"], errors="coerce")
df["Total ($)"] = pd.to_numeric(df["Total ($)"], errors="coerce")

totals = {
    "service_compute": float(df["Service Compute ($)"].sum()),
    "total": float(df["Total ($)"].sum()),
}
totals["other_charges"] = round(totals["total"] - totals["service_compute"], 4)
totals["service_compute_pct"] = round(
    totals["service_compute"] / totals["total"] * 100, 2
)
totals["other_charges_pct"] = round(
    totals["other_charges"] / totals["total"] * 100, 2
)

return [{"json": totals}]
```

**Output keys:** `service_compute`, `total`, `other_charges`, `service_compute_pct`, `other_charges_pct`

---

## SQL (DuckDB) examples

[DuckDB](https://duckdb.org/) can query a CSV string directly using its `read_csv_auto` function. The examples read the raw CSV text from the first input item, write it to a temporary in-memory path, then run SQL against it.

/// note | DuckDB in n8n Code node
DuckDB is not bundled with the n8n Code node by default. Run these queries in a self-hosted n8n instance where you have installed `duckdb` (for example via a [custom npm package](/hosting/configuration/npm-packages/)) or adapt the logic to JavaScript/Python using the pandas approach above.
///

### Daily totals with day-over-day change

```sql
-- Assumes the CSV is saved as /tmp/billing.csv by a previous node.
-- Replace the path if your workflow stores the file elsewhere.

WITH daily AS (
    SELECT
        CAST(Date AS DATE)                     AS date,
        SUM("Service Compute ($)")             AS service_compute,
        SUM("Total ($)")                       AS total
    FROM read_csv_auto('/tmp/billing.csv', header = true)
    GROUP BY CAST(Date AS DATE)
),
with_lag AS (
    SELECT
        date,
        service_compute,
        total,
        LAG(total) OVER (ORDER BY date)        AS prev_total
    FROM daily
)
SELECT
    date,
    service_compute,
    total,
    total - prev_total                         AS dod_change,
    ROUND((total - prev_total) / prev_total * 100, 2) AS dod_pct
FROM with_lag
ORDER BY date;
```

### Spend by dimensions

```sql
SELECT
    "Organization Plan",
    "Entity Type",
    "CSP",
    "Region",
    SUM("Service Compute ($)")  AS service_compute,
    SUM("Total ($)")            AS total
FROM read_csv_auto('/tmp/billing.csv', header = true)
GROUP BY
    "Organization Plan",
    "Entity Type",
    "CSP",
    "Region"
ORDER BY total DESC;
```

### Cost-component breakdown

```sql
SELECT
    SUM("Service Compute ($)")                              AS service_compute,
    SUM("Total ($)")                                        AS total,
    SUM("Total ($)") - SUM("Service Compute ($)")           AS other_charges,
    ROUND(SUM("Service Compute ($)") / SUM("Total ($)") * 100, 2)
                                                            AS service_compute_pct,
    ROUND(
        (SUM("Total ($)") - SUM("Service Compute ($)")) / SUM("Total ($)") * 100,
        2
    )                                                       AS other_charges_pct
FROM read_csv_auto('/tmp/billing.csv', header = true);
```

---

## CSV schema reference

| Column | Type | Notes |
|--------|------|-------|
| `Date` | string / date | ISO 8601 date (`YYYY-MM-DD`) |
| `Organization Plan` | string | Subscription tier (for example, `Standard`, `Premium`) |
| `Entity Name` | string | Name of the billed entity |
| `Entity Type` | string | Role of the entity (for example, `Customer`, `Reseller`) |
| `Warehouse ID` | string | Identifier of the compute warehouse |
| `Service ID` | string | Identifier of the billed service |
| `CSP` | string | Cloud Service Provider (`AWS`, `GCP`, `Azure`) |
| `Region` | string | Cloud region identifier |
| `Service Compute ($)` | numeric | Compute-specific charge in USD |
| `Total ($)` | numeric | Total charge in USD (compute + other components) |
