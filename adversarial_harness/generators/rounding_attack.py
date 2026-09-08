import math


def make_line(ip, slot, endpoint, status, latency_s):
    ts = f"08/Jan/2024:10:{slot % 60:02d}:{(slot // 60) % 60:02d} +0000"
    return f'{ip} - - [{ts}] "GET {endpoint} HTTP/1.1" {status} 256 "-" "rounding-test/1.0" {latency_s:.9f}'


def p95_of(times_s):
    n = len(times_s)
    s = sorted(t * 1000 for t in times_s)
    return round(s[math.floor(n * 0.95)], 1)


def generate(log_path):
    lines = []
    slot = 0

    for _ in range(19):
        lines.append(make_line("10.0.0.1", slot, "/api/f1", 200, 0.100))
        slot += 1
    lines.append(make_line("10.0.0.2", slot, "/api/f1", 200, 0.49995))
    slot += 1

    for _ in range(19):
        lines.append(make_line("10.0.1.1", slot, "/api/f2", 200, 0.100))
        slot += 1
    lines.append(make_line("10.0.1.2", slot, "/api/f2", 200, 0.50005))
    slot += 1

    for _ in range(19):
        lines.append(make_line("10.0.2.1", slot, "/api/f3", 200, 0.100))
        slot += 1
    lines.append(make_line("10.0.2.2", slot, "/api/f3", 200, 0.50015))
    slot += 1

    for _ in range(5):
        lines.append(make_line("10.0.3.1", slot, "/api/f4", 200, 0.200))
        slot += 1
    for _ in range(5):
        lines.append(make_line("10.0.3.2", slot, "/api/f4", 200, 0.800))
        slot += 1

    with open(log_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    f1_p95 = p95_of([0.100] * 19 + [0.49995])
    f2_p95 = p95_of([0.100] * 19 + [0.50005])
    f3_p95 = p95_of([0.100] * 19 + [0.50015])

    return {
        "name": "Category F — Rounding & Floating-Point Boundaries",
        "trap": (
            "499.95ms and 500.05ms sit on Python banker's rounding boundary. "
            "Inconsistent rounding flips sla_ok across the 500ms threshold."
        ),
        "expected": {
            "/api/f1": {"requests": 20, "errors": 0, "p95_ms": f1_p95, "sla_ok": f1_p95 <= 500.0},
            "/api/f2": {"requests": 20, "errors": 0, "p95_ms": f2_p95, "sla_ok": f2_p95 <= 500.0},
            "/api/f3": {"requests": 20, "errors": 0, "p95_ms": f3_p95, "sla_ok": f3_p95 <= 500.0},
            "/api/f4": {
                "requests": 10,
                "errors": 0,
                "avg_ms": round(sum([200.0] * 5 + [800.0] * 5) / 10, 1),
            },
        },
    }
