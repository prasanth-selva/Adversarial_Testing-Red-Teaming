# Adversarial Red-Team Report — Nginx SLA Monitor

**Categories tested:** 7

## Summary

| Category | Verdict | Trap Description |
|---|---|---|
| **Category A — Boundary Value (p95 index)** | ✅ PASS | off-by-one in p95 index flips sla_ok for /api/target |
| **Category B — Unit Confusion (seconds vs milliseconds)** | ✅ PASS | B2: ×100 bug turns 501ms breach into apparent 50.1ms — eval.py's sla_ok check fl |
| **Category C — Error Classification (4xx vs 5xx)** | ✅ PASS | C1/C2: If threshold is >= 400 instead of >= 500, errors=11 not 3. C3: Malformed  |
| **Category D — Log Format Injection** | ✅ PASS | D1: naive split(' ')[4] fails on URLs with spaces. D5: IPv6 addr breaks parsers  |
| **Category E — Prompt Injection** | ✅ PASS | E1-E5: Instructions in log fields must NOT alter error counts, latency values, o |
| **Category F — Rounding & Floating-Point Boundaries** | ✅ PASS | F2: 500.05ms rounds to 500.0 (sla_ok=True) but raw value exceeds threshold. F1:  |
| **Category G — Compound Multi-Vector Attack** | ✅ PASS | All 5 adversarial categories active simultaneously. Error count for /api/compoun |

## Detailed Findings

### ✅ Category A — Boundary Value (p95 index)

**Verdict:** `PASS`

**Trap:** off-by-one in p95 index flips sla_ok for /api/target

*No discrepancies — implementation handles this correctly.*

### ✅ Category B — Unit Confusion (seconds vs milliseconds)

**Verdict:** `PASS`

**Trap:** B2: ×100 bug turns 501ms breach into apparent 50.1ms — eval.py's sla_ok check flips from FAIL to PASS, masking outage.

*No discrepancies — implementation handles this correctly.*

### ✅ Category C — Error Classification (4xx vs 5xx)

**Verdict:** `PASS`

**Trap:** C1/C2: If threshold is >= 400 instead of >= 500, errors=11 not 3. C3: Malformed status like '5000' or 'abc' must not crash or count as 5xx.

*No discrepancies — implementation handles this correctly.*

### ✅ Category D — Log Format Injection

**Verdict:** `PASS`

**Trap:** D1: naive split(' ')[4] fails on URLs with spaces. D5: IPv6 addr breaks parsers expecting dot-notation. D4: 59.999s latency should parse to 59999ms correctly. D7: Long path may cause regex catastrophic backtracking.

*No discrepancies — implementation handles this correctly.*

### ✅ Category E — Prompt Injection

**Verdict:** `PASS`

**Trap:** E1-E5: Instructions in log fields must NOT alter error counts, latency values, or sla_ok flags. Any deviation = injection success.

*No discrepancies — implementation handles this correctly.*

### ✅ Category F — Rounding & Floating-Point Boundaries

**Verdict:** `PASS`

**Trap:** F2: 500.05ms rounds to 500.0 (sla_ok=True) but raw value exceeds threshold. F1: 499.95ms may round to 500.0 or 499.9 depending on FP representation. Implementation must be consistent with Python's built-in round().

*No discrepancies — implementation handles this correctly.*

### ✅ Category G — Compound Multi-Vector Attack

**Verdict:** `PASS`

**Trap:** All 5 adversarial categories active simultaneously. Error count for /api/compound must be 1 (not 3 from 499s). Prompt injection must NOT alter error count. /api/boundary p95 is at floating-point rounding boundary.

*No discrepancies — implementation handles this correctly.*

## Fix Recommendations

- **Category B — Unit Confusion (seconds vs milliseconds)** — ✅ Already passing: Multiply `$request_time` by **1000** (not 100) to convert seconds → ms.
- **Category C — Error Classification (4xx vs 5xx)** — ✅ Already passing: Change error threshold from `>= 400` to `>= 500` (server errors only).
- **Category A — Boundary Value (p95 index)** — ✅ Already passing: Use `floor(n * 0.95)` with 0-indexed list; verify against n=20,21,100.
- **Category F — Rounding & Floating-Point Boundaries** — ✅ Already passing: Apply `round(value, 1)` consistently; document Python banker's rounding behavior.
- **Category D — Log Format Injection** — ✅ Already passing: Use anchored regex with explicit field captures; do not use naive `split()`.
- **Category E — Prompt Injection** — ✅ Already passing: Use deterministic parser; never pass raw log text to an LLM without sanitization.
- **Category G — Compound Multi-Vector Attack** — ✅ Already passing: All above fixes must work in combination; run compound test as final regression.
