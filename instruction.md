# Task: Fix the Broken Sales ETL Pipeline

## Working Directory
`/app`

## Background

You are given a Python ETL script (`etl_pipeline.py`) that is supposed to:

1. Read sales transaction data from `sales.csv`
2. Clean and normalise the data
3. Insert each row into the `daily_summary` table in a SQLite database (`sales.db`)

The pipeline is currently broken and produces incorrect results (or crashes before finishing). Your job is to identify and fix **all** defects so that `python3 eval.py` exits with code `0`.

## Input file: `sales.csv`

| Column    | Notes                                                                 |
|-----------|-----------------------------------------------------------------------|
| `id`      | Integer row identifier                                                |
| `date`    | Either `YYYY-MM-DD` **or** `MM/DD/YYYY` — both formats appear        |
| `region`  | Free-text region name                                                 |
| `product` | Product name — may contain non-ASCII characters (Latin-1 encoded)    |
| `revenue` | Decimal value; **some rows are blank** — treat blanks as `0.0`       |
| `units`   | Integer unit count                                                    |

The file is **Latin-1 encoded**.

## Expected output: `sales.db`

A SQLite database file at `/app/sales.db` containing a table `daily_summary`:

```sql
CREATE TABLE daily_summary (
    date          TEXT,    -- always YYYY-MM-DD
    region        TEXT,
    product       TEXT,
    total_revenue REAL,    -- 0.0 when source value was blank
    total_units   INTEGER
);
```

All 6 source rows must appear as individual rows in `daily_summary`.

## Constraints

- Do **not** modify `eval.py`.
- Do **not** hardcode expected values into `etl_pipeline.py`.
- The fixed script must run with: `python3 etl_pipeline.py`
- Exit code of `etl_pipeline.py` must be `0`.

## Success Criterion

```
python3 eval.py   # must exit 0 and print: PASS: All checks passed.
```
