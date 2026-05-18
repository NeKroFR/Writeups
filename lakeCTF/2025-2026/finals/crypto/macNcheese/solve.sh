#!/bin/bash
set -e
N=${N:-14}
TMP=$(mktemp -d)
for i in $(seq 1 $N); do
    sage phase1.sage $RANDOM "$TMP/$i.pkl" > "$TMP/$i.log" 2>&1 &
done
while :; do
    for f in "$TMP"/*.pkl; do [ -s "$f" ] && cp "$f" phase1_result.pkl && break 2; done
    sleep 3
done
pkill -P $$ 2>/dev/null || true
sage solve.sage
