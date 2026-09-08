#!/usr/bin/env bash
set -euo pipefail

cat > /app/analyze.py << 'PYEOF'
"""Nginx access-log SLA monitor (fixed)."""
import re
import json
import math
from collections import defaultdict

LOG_PATTERN = re.compile(
    r'(\S+) - (\S+) \[([^\]]+)\] "(\S+) (\S+) [^"]+" (\d+) (\d+) "[^"]*" "[^"]*" (\S+)'
)

SLA_P95_THRESHOLD_MS = 500.0


def parse_log(path: str) -> list:
    entries = []
    with open(path) as f:
        for line in f:
            m = LOG_PATTERN.match(line.strip())
            if not m:
                continue
            entries.append({
                'endpoint':         m.group(5),
                'status':           int(m.group(6)),
                'response_time_ms': float(m.group(8)) * 1000,
            })
    return entries


def compute_stats(entries: list) -> dict:
    buckets: dict = defaultdict(lambda: {'times': [], 'errors': 0})

    for e in entries:
        ep = e['endpoint']
        buckets[ep]['times'].append(e['response_time_ms'])
        if e['status'] >= 500:
            buckets[ep]['errors'] += 1

    report = {}
    for ep, data in sorted(buckets.items()):
        times = data['times']
        n     = len(times)
        s     = sorted(times)
        avg   = round(sum(times) / n, 1)
        p95   = round(s[math.floor(n * 0.95)], 1)
        report[ep] = {
            'requests': n,
            'errors':   data['errors'],
            'avg_ms':   avg,
            'p95_ms':   p95,
            'sla_ok':   p95 <= SLA_P95_THRESHOLD_MS,
        }
    return report


def main() -> None:
    entries    = parse_log('/app/access.log')
    stats      = compute_stats(entries)
    violations = [ep for ep, s in stats.items() if not s['sla_ok']]

    result = {
        'total_requests':          len(entries),
        'endpoints':               stats,
        'sla_violation_endpoints': violations,
    }

    with open('/app/report.json', 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Analysis complete — {len(violations)} SLA violation(s) detected.")


if __name__ == '__main__':
    main()
PYEOF

cd /app && python3 analyze.py

