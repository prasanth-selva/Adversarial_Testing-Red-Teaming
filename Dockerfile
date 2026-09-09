# syntax=docker/dockerfile:1
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Generate a deterministic Nginx access log (45 lines, 3 endpoints).
# Format: combined log + $request_time (in seconds).
#
# Endpoint breakdown:
#   /api/health  10 x 200 @ 0.005 s  → p95 =   5 ms  (no violation)
#   /api/orders  15 x 200 @ 0.100 s
#                 5 x 200 @ 0.800 s  → p95 = 800 ms  (SLA BREACH: >500 ms)
#   /api/users   12 x 200 @ 0.050 s
#                 2 x 404 @ 0.020 s
#                 1 x 500 @ 0.050 s  → p95 =  50 ms  (no violation; 1 server error)
# ---------------------------------------------------------------------------
RUN python3 - << 'EOF'
lines = []

for i in range(10):
    ts = f"08/Jan/2024:10:{i:02d}:00 +0000"
    lines.append(
        f'10.0.0.{i+1} - - [{ts}]'
        f' "GET /api/health HTTP/1.1" 200 64 "-" "Go-http-client/1.1" 0.005'
    )

for i in range(15):
    ts = f"08/Jan/2024:10:{i:02d}:10 +0000"
    lines.append(
        f'10.0.1.{i+1} - - [{ts}]'
        f' "GET /api/orders HTTP/1.1" 200 1024 "-" "python-requests/2.28.0" 0.100'
    )
for i in range(5):
    ts = f"08/Jan/2024:10:{i+15:02d}:10 +0000"
    lines.append(
        f'10.0.1.{i+16} - - [{ts}]'
        f' "GET /api/orders HTTP/1.1" 200 1024 "-" "python-requests/2.28.0" 0.800'
    )

for i in range(12):
    ts = f"08/Jan/2024:10:{i:02d}:20 +0000"
    lines.append(
        f'10.0.2.{i+1} - bob [{ts}]'
        f' "GET /api/users HTTP/1.1" 200 512 "-" "curl/7.88.0" 0.050'
    )
for i in range(2):
    ts = f"08/Jan/2024:10:{i+12:02d}:20 +0000"
    lines.append(
        f'10.0.2.{i+13} - bob [{ts}]'
        f' "GET /api/users HTTP/1.1" 404 128 "-" "curl/7.88.0" 0.020'
    )
lines.append(
    '10.0.2.15 - - [08/Jan/2024:10:14:20 +0000]'
    ' "GET /api/users HTTP/1.1" 500 64 "-" "python-requests/2.28.0" 0.050'
)

with open('/app/access.log', 'w') as f:
    f.write('\n'.join(lines) + '\n')
EOF

COPY analyze.py /app/analyze.py
COPY eval.py    /app/eval.py
COPY solve.sh   /app/solve.sh
COPY access.log /app/access.log
RUN chmod +x /app/solve.sh

# Default: run the broken analyzer so the baseline eval.py fails
CMD ["python3", "analyze.py"]
