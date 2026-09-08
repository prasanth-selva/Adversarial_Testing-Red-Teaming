def make_line(ip, slot, endpoint, status, latency_s=0.050):
    ts = f"08/Jan/2024:10:{slot % 60:02d}:{(slot // 60) % 60:02d} +0000"
    return f'{ip} - - [{ts}] "GET {endpoint} HTTP/1.1" {status} 256 "-" "test/1.0" {latency_s:.6f}'


def generate(log_path):
    lines = []
    slot = 0

    statuses = [200] * 5 + [400] * 2 + [404] * 3 + [499] * 1 + [500] * 2 + [503] * 1

    for i, status in enumerate(statuses):
        lines.append(make_line(f"10.0.0.{i+1}", slot, "/api/errors", status))
        slot += 1

    malformed = ["5000", "99", "abc", "0"]
    for i, bad in enumerate(malformed):
        ts = f"08/Jan/2024:10:{slot % 60:02d}:{(slot // 60) % 60:02d} +0000"
        lines.append(
            f'10.0.9.{i+1} - - [{ts}] "GET /api/malformed HTTP/1.1" {bad} 0 "-" "fuzz/1.0" 0.001000'
        )
        slot += 1

    with open(log_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return {
        "name": "Category C — Error Classification (4xx vs 5xx)",
        "trap": (
            "If threshold is >= 400 instead of >= 500, errors become 11 instead of 3. "
            "Malformed status codes like '5000' or 'abc' must not crash the parser."
        ),
        "expected": {
            "/api/errors": {
                "requests": 14,
                "errors": 3,
                "sla_ok": True,
            },
        },
    }
