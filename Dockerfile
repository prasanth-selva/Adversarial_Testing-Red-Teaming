# syntax=docker/dockerfile:1
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3 sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Generate Latin-1 encoded sales.csv (\xe9 = é, an intentional encoding trap)
RUN python3 - << 'EOF'
with open('/app/sales.csv', 'wb') as f:
    f.write(b'id,date,region,product,revenue,units\n')
    f.write(b'1,2024-01-15,North,Widget A,1250.50,5\n')
    f.write(b'2,01/16/2024,South,Caf\xe9 Latte,890.00,3\n')
    f.write(b'3,2024-01-15,East,Widget A,,2\n')
    f.write(b'4,2024-01-17,North,Widget B,340.75,1\n')
    f.write(b'5,01/18/2024,West,Caf\xe9 Latte,1100.25,4\n')
    f.write(b'6,2024-01-16,East,Widget B,275.00,2\n')
EOF

COPY etl_pipeline.py /app/etl_pipeline.py
COPY eval.py         /app/eval.py
COPY solve.sh        /app/solve.sh
RUN chmod +x /app/solve.sh

# Default: run the broken pipeline so the baseline eval fails
CMD ["python3", "etl_pipeline.py"]
