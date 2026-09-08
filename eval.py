#!/usr/bin/env python3
"""Deterministic verifier for the Sales ETL pipeline task.
Exits 0 on full success; non-zero on any failure."""
import os
import sys
import sqlite3
from datetime import datetime


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    db_path = '/app/sales.db'

    if not os.path.exists(db_path):
        fail("sales.db not found in /app")

    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # 1. Table existence
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_summary'")
    if not cur.fetchone():
        fail("Table 'daily_summary' not found in sales.db")

    # 2. Row count
    cur.execute("SELECT COUNT(*) FROM daily_summary")
    count = cur.fetchone()[0]
    if count != 6:
        fail(f"Expected 6 rows in daily_summary, found {count}")

    # 3. Date format
    cur.execute("SELECT date FROM daily_summary")
    for (date_val,) in cur.fetchall():
        try:
            datetime.strptime(date_val, '%Y-%m-%d')
        except (ValueError, TypeError):
            fail(f"Date value {date_val!r} is not in YYYY-MM-DD format")

    # 4. No NULL or negative revenue
    cur.execute(
        "SELECT COUNT(*) FROM daily_summary WHERE total_revenue IS NULL OR total_revenue < 0"
    )
    bad_rev = cur.fetchone()[0]
    if bad_rev:
        fail(f"{bad_rev} row(s) have NULL or negative total_revenue")

    # 5. Exact value checks (catches the silent column-swap bug)
    expected = [
        ('2024-01-15', 'North', 'Widget A',      1250.50, 5),
        ('2024-01-15', 'East',  'Widget A',          0.0, 2),
        ('2024-01-16', 'South', 'Caf\xe9 Latte',  890.00, 3),
        ('2024-01-16', 'East',  'Widget B',        275.00, 2),
        ('2024-01-17', 'North', 'Widget B',        340.75, 1),
        ('2024-01-18', 'West',  'Caf\xe9 Latte', 1100.25, 4),
    ]
    for exp_date, exp_region, exp_product, exp_revenue, exp_units in expected:
        cur.execute(
            'SELECT total_revenue, total_units FROM daily_summary '
            'WHERE date=? AND region=? AND product=?',
            (exp_date, exp_region, exp_product),
        )
        row = cur.fetchone()
        if row is None:
            fail(
                f"Missing row — date={exp_date}, region={exp_region},"
                f" product={exp_product!r}"
            )
        actual_rev, actual_units = row
        if abs(actual_rev - exp_revenue) > 0.001:
            fail(
                f"Revenue mismatch ({exp_date}, {exp_region}, {exp_product!r}): "
                f"expected {exp_revenue}, got {actual_rev}"
            )
        if actual_units != exp_units:
            fail(
                f"Units mismatch ({exp_date}, {exp_region}, {exp_product!r}): "
                f"expected {exp_units}, got {actual_units}"
            )

    conn.close()
    print("PASS: All checks passed.")
    sys.exit(0)


if __name__ == '__main__':
    main()
