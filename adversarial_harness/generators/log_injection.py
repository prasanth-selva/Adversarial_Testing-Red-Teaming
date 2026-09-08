def make_line(ip, slot, method, endpoint, status, body, latency_s, ua="test/1.0"):
    ts = f"08/Jan/2024:10:{slot % 60:02d}:{(slot // 60) % 60:02d} +0000"
    return f'{ip} - - [{ts}] "{method} {endpoint} HTTP/1.1" {status} {body} "-" "{ua}" {latency_s:.6f}'


def generate(log_path):
    lines = []
    slot = 0

    lines.append(make_line("10.0.0.1", slot, "GET", "/api/search?q=hello%20world", 200, 512, 0.120))
    slot += 1
    lines.append(make_line("10.0.0.2", slot, "GET", "/api/search", 200, 512, 0.120))
    slot += 1
    lines.append(make_line("10.0.0.3", slot, "GET", "/api/v2/data/(item)/[0]", 200, 256, 0.080))
    slot += 1
    lines.append(make_line("10.0.0.4", slot, "GET", "/api/check?x=1&y=2.5", 200, 256, 0.080))
    slot += 1
    lines.append(make_line("10.0.0.5", slot, "DELETE", "/api/resource/42", 204, 0, 0.010))
    slot += 1
    lines.append(make_line("10.0.0.6", slot, "HEAD", "/api/health", 200, 0, 0.005))
    slot += 1
    lines.append(make_line("10.0.0.7", slot, "GET", "/api/export", 200, 1048576, 59.999))
    slot += 1

    lines.append(
        f'2001:db8::1 - - [08/Jan/2024:10:07:00 +0000] '
        f'"GET /api/ipv6 HTTP/1.1" 200 512 "-" "curl/7.88" 0.050000'
    )
    slot += 1

    for method in ["PATCH", "OPTIONS", "PUT"]:
        lines.append(make_line("10.0.1.1", slot, method, "/api/resource", 200, 128, 0.030))
        slot += 1

    long_path = "/api/v1/" + "a" * 500 + "/endpoint"
    lines.append(make_line("10.0.2.1", slot, "GET", long_path, 200, 64, 0.025))
    slot += 1

    lines.append(make_line(
        "10.0.3.1", slot, "GET", "/api/ua-test", 200, 256, 0.040,
        ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ))
    slot += 1

    with open(log_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    return {
        "name": "Category D — Log Format Injection",
        "trap": (
            "Naive split() fails on URLs with spaces. "
            "IPv6 breaks dot-notation parsers. "
            "59.999s latency must parse to 59999ms. "
            "Long paths may trigger regex backtracking."
        ),
        "lines_count": len(lines),
        "expected_total_requests": len(lines),
    }
