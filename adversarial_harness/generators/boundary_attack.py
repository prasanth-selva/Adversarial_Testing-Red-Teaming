import math


def make_line(ip, slot, endpoint, status, latency_s):
    ts = f"08/Jan/2024:10:{slot % 60:02d}:{(slot // 60) % 60:02d} +0000"
    return f'{ip} - - [{ts}] "GET {endpoint} HTTP/1.1" {status} 512 "-" "test/1.0" {latency_s:.6f}'


def generate(log_path):
    lines = []
    slot = 0

    for _ in range(19):
        lines.append(make_line("10.0.0.1", slot, "/api/target", 200, 0.100))
        slot += 1
    lines.append(make_line("10.0.0.2", slot, "/api/target", 200, 0.800))
    slot += 1

    for _ in range(21):
        lines.append(make_line("10.0.1.1", slot, "/api/safe", 200, 0.100))
        slot += 1

    for _ in range(95):
        lines.append(make_line("10.0.2.1", slot, "/api/bulk", 200, 0.100))
        slot += 1
    for _ in range(5):
        lines.append(make_line("10.0.2.2", slot, "/api/bulk", 200, 0.600))
        slot += 1

    with open(log_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    target_times = sorted([0.100] * 19 + [0.800])
    safe_times = sorted([0.100] * 21)
    bulk_times = sorted([0.100] * 95 + [0.600] * 5)

    return {
        "name": "Category A — Boundary Value (p95 index)",
        "trap": "off-by-one in p95 index flips sla_ok for /api/target",
        "expected": {
            "/api/target": {
                "requests": 20,
                "errors": 0,
                "p95_ms": round(target_times[math.floor(20 * 0.95)] * 1000, 1),
                "sla_ok": round(target_times[math.floor(20 * 0.95)] * 1000, 1) <= 500.0,
            },
            "/api/safe": {
                "requests": 21,
                "errors": 0,
                "p95_ms": round(safe_times[math.floor(21 * 0.95)] * 1000, 1),
                "sla_ok": True,
            },
            "/api/bulk": {
                "requests": 100,
                "errors": 0,
                "p95_ms": round(bulk_times[math.floor(100 * 0.95)] * 1000, 1),
                "sla_ok": round(bulk_times[math.floor(100 * 0.95)] * 1000, 1) <= 500.0,
            },
        },
    }
