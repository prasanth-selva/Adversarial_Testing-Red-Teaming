# Task: Fix the Broken Nginx SLA Monitor

## Background

An engineering team runs a Python script (`analyze.py`) that reads the Nginx
access log after each deployment and produces a per-endpoint SLA compliance
report. A recent refactor broke the script. The on-call team is blind until
you fix it.

Your task: identify and fix all defects in `/app/analyze.py` so that
`python3 eval.py` exits with code `0`.

---

## Log format

The Nginx instance is configured with the following `log_format`:

```
$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent
"$http_referer" "$http_user_agent" $request_time
```

The `$request_time` field is in **seconds** (e.g. `0.142`).  
The log file is at `/app/access.log`.

Example line:

```
10.0.1.3 - - [08/Jan/2024:10:02:10 +0000] "GET /api/orders HTTP/1.1" 200 1024 "-" "python-requests/2.28.0" 0.100
```

---

## What `analyze.py` must produce

Write a JSON report to **`/app/report.json`** with the following structure:

```json
{
  "total_requests": <int>,
  "endpoints": {
    "<endpoint>": {
      "requests": <int>,
      "errors":   <int>,
      "avg_ms":   <float rounded to 1 decimal place>,
      "p95_ms":   <float rounded to 1 decimal place>,
      "sla_ok":   <bool>
    }
  },
  "sla_violation_endpoints": ["<endpoint>", ...]
}
```

### Metric definitions

| Field | Definition |
|-------|------------|
| `errors` | Responses with HTTP status **≥ 500** (server errors only; 4xx responses are **not** counted as errors) |
| `avg_ms` | Arithmetic mean of response times in **milliseconds** |
| `p95_ms` | 95th-percentile response time in **milliseconds** — the value at index `floor(n × 0.95)` of the ascending-sorted list |
| `sla_ok` | `true` if `p95_ms ≤ 500`, otherwise `false` |
| `sla_violation_endpoints` | List of endpoint paths where `sla_ok` is `false` |

---

## Constraints

- Working directory: `/app`
- Do **not** modify `eval.py` or `access.log`.
- Run the fixed script with: `python3 analyze.py`
- The script must exit with code `0`.
- No third-party libraries are available; use only the Python standard library.

---

## Success criterion

```bash
cd /app && python3 analyze.py && python3 eval.py
# Must print: PASS
# Must exit:  0
```
