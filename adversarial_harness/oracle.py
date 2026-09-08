import re
import json
import math
import sys
from collections import defaultdict

LOG_PATTERN = re.compile(
    r'(\S+) - (\S+) \[([^\]]+)\] "(\S+) (\S+) [^"]+" (\d+) (\d+) "[^"]*" "[^"]*" (\S+)'
)

SLA_THRESHOLD_MS = 500.0


def compute_oracle(log_path):
    buckets = defaultdict(lambda: {"times_ms": [], "errors": 0})

    with open(log_path) as f:
        for raw in f:
            m = LOG_PATTERN.match(raw.strip())
            if not m:
                continue
            endpoint = m.group(5)
            status = int(m.group(6))
            time_ms = float(m.group(8)) * 1000.0

            buckets[endpoint]["times_ms"].append(time_ms)
            if status >= 500:
                buckets[endpoint]["errors"] += 1

    total = sum(len(v["times_ms"]) for v in buckets.values())
    endpoints = {}

    for ep in sorted(buckets):
        times = buckets[ep]["times_ms"]
        errors = buckets[ep]["errors"]
        n = len(times)
        s = sorted(times)
        avg_ms = round(sum(times) / n, 1)
        p95_ms = round(s[math.floor(n * 0.95)], 1)
        sla_ok = p95_ms <= SLA_THRESHOLD_MS

        endpoints[ep] = {
            "requests": n,
            "errors": errors,
            "avg_ms": avg_ms,
            "p95_ms": p95_ms,
            "sla_ok": sla_ok,
        }

    violations = sorted(ep for ep, v in endpoints.items() if not v["sla_ok"])

    return {
        "total_requests": total,
        "endpoints": endpoints,
        "sla_violation_endpoints": violations,
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/app/access.log"
    print(json.dumps(compute_oracle(path), indent=2))
