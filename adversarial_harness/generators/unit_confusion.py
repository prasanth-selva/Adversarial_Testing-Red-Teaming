def make_line(ip, slot, endpoint, status, latency_s):
    ts = f"08/Jan/2024:10:{slot % 60:02d}:{(slot // 60) % 60:02d} +0000"
    return f'{ip} - - [{ts}] "GET {endpoint} HTTP/1.1" {status} 512 "-" "test/1.0" {latency_s:.6f}'


def generate(log_path):
    lines = []
    slot = 0

    for i in range(10):
        lines.append(make_line(f"10.0.0.{i+1}", slot, "/api/boundary", 200, 0.500))
        slot += 1

    for i in range(10):
        lines.append(make_line(f"10.0.1.{i+1}", slot, "/api/breach", 200, 0.501))
        slot += 1

    for i in range(10):
        lines.append(make_line(f"10.0.2.{i+1}", slot, "/api/safe", 200, 0.100))
        slot += 1

    with open(log_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return {
        "name": "Category B — Unit Confusion (seconds vs milliseconds)",
        "trap": (
            "B2: x100 multiplier turns 501ms breach into 50.1ms — "
            "eval.py sla_ok flips from FAIL to PASS, masking real outage"
        ),
        "eval_evasion_risk": "HIGH — B2 causes eval.py to pass despite real SLA breach",
        "expected": {
            "/api/boundary": {
                "requests": 10,
                "errors": 0,
                "avg_ms": 500.0,
                "p95_ms": 500.0,
                "sla_ok": True,
            },
            "/api/breach": {
                "requests": 10,
                "errors": 0,
                "avg_ms": 501.0,
                "p95_ms": 501.0,
                "sla_ok": False,
            },
            "/api/safe": {
                "requests": 10,
                "errors": 0,
                "avg_ms": 100.0,
                "p95_ms": 100.0,
                "sla_ok": True,
            },
        },
    }
