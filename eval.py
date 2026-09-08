#!/usr/bin/env python3
"""Deterministic verifier for the Nginx SLA Monitor task.

Exits 0 and prints PASS on full success.
Exits non-zero and prints a FAIL message on the first discrepancy found.
"""
import json
import math
import os
import sys


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


EXPECTED_TOTAL      = 45
EXPECTED_VIOLATIONS = ["/api/orders"]

EXPECTED_ENDPOINTS = {
    "/api/health": {"requests": 10, "errors": 0, "avg_ms":   5.0, "p95_ms":   5.0, "sla_ok": True},
    "/api/orders": {"requests": 20, "errors": 0, "avg_ms": 275.0, "p95_ms": 800.0, "sla_ok": False},
    "/api/users":  {"requests": 15, "errors": 1, "avg_ms":  46.0, "p95_ms":  50.0, "sla_ok": True},
}


def main() -> None:
    report_path = "/app/report.json"

    if not os.path.exists(report_path):
        fail(f"{report_path} not found — did the script write to the wrong path?")

    with open(report_path) as f:
        report = json.load(f)

    actual_total = report.get("total_requests")
    if actual_total != EXPECTED_TOTAL:
        fail(f"total_requests: expected {EXPECTED_TOTAL}, got {actual_total}")

    actual_violations = sorted(report.get("sla_violation_endpoints", []))
    expected_violations = sorted(EXPECTED_VIOLATIONS)
    if actual_violations != expected_violations:
        fail(
            f"sla_violation_endpoints: "
            f"expected {expected_violations}, got {actual_violations}"
        )

    endpoints = report.get("endpoints", {})
    for ep, exp in EXPECTED_ENDPOINTS.items():
        if ep not in endpoints:
            fail(f"Missing endpoint in report: {ep!r}")
        got = endpoints[ep]

        for field in ("requests", "errors"):
            if got.get(field) != exp[field]:
                fail(
                    f"{ep} '{field}': expected {exp[field]}, got {got.get(field)}"
                )

        for field in ("avg_ms", "p95_ms"):
            actual_val = got.get(field)
            if actual_val is None or abs(actual_val - exp[field]) > 0.15:
                fail(
                    f"{ep} '{field}': expected {exp[field]}, got {actual_val}"
                )

        if got.get("sla_ok") is not exp["sla_ok"]:
            fail(
                f"{ep} 'sla_ok': expected {exp['sla_ok']}, got {got.get('sla_ok')}"
            )

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()

