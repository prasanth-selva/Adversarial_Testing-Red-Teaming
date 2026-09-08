#!/usr/bin/env bash
# Golden solution: overwrites etl_pipeline.py with all four bugs fixed,
# then executes it so eval.py will pass.
set -euo pipefail

cat > /app/etl_pipeline.py << 'PYEOF'
import csv
import sqlite3
from datetime import datetime


def parse_date(raw: str) -> str:
    """Accept YYYY-MM-DD or MM/DD/YYYY; always return YYYY-MM-DD."""
    for fmt in ('%Y-%m-%d', '%m/%d/%Y'):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: {raw!r}")


# Fix 1: open with the correct encoding.
with open('sales.csv', encoding='latin-1') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

conn = sqlite3.connect('sales.db')
cur  = conn.cursor()

cur.execute('''
    CREATE TABLE IF NOT EXISTS daily_summary (
        date          TEXT,
        region        TEXT,
        product       TEXT,
        total_revenue REAL,
        total_units   INTEGER
    )
''')

for row in rows:
    # Fix 2: try both date formats.
    date = parse_date(row['date'])

    region  = row['region']
    product = row['product']

    # Fix 3: use float(), default blank values to 0.0.
    revenue_raw = row['revenue'].strip()
    revenue = float(revenue_raw) if revenue_raw else 0.0
    units   = int(row['units'])

    # Fix 4: values are in the correct order — revenue then units.
    cur.execute(
        'INSERT INTO daily_summary (date, region, product, total_revenue, total_units)'
        ' VALUES (?, ?, ?, ?, ?)',
        (date, region, product, revenue, units),
    )

conn.commit()
conn.close()
print('ETL pipeline completed successfully.')
PYEOF

cd /app && python3 etl_pipeline.py
