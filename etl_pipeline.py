import csv
import sqlite3
from datetime import datetime

# Bug 1: File is Latin-1 encoded; opening as utf-8 raises UnicodeDecodeError
# on any row whose product name contains a non-ASCII character.
with open('sales.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

conn = sqlite3.connect('sales.db')
cur = conn.cursor()

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
    # Bug 2: Only one date format is tried; MM/DD/YYYY rows raise ValueError.
    date = datetime.strptime(row['date'], '%Y-%m-%d').strftime('%Y-%m-%d')

    region  = row['region']
    product = row['product']

    # Bug 3: int() raises ValueError on float strings (e.g. '1250.50') and on
    # empty strings (blank revenue values).
    revenue = int(row['revenue'])
    units   = int(row['units'])

    # Bug 4 (silent): the positional values are swapped — units ends up in
    # total_revenue and revenue ends up in total_units.  The INSERT succeeds
    # without error, so the script exits 0, but the stored data is wrong.
    cur.execute(
        'INSERT INTO daily_summary (date, region, product, total_revenue, total_units)'
        ' VALUES (?, ?, ?, ?, ?)',
        (date, region, product, units, revenue),   # <-- swapped!
    )

conn.commit()
conn.close()
print('ETL pipeline completed successfully.')
