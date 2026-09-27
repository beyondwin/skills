#!/usr/bin/env bash
# usage: run_batch.sh <parallel> <jobs-file>   (one "cond model rep [--kill-after-task]" per line)
set -uo pipefail
cd "$(dirname "$0")"
P="$1"; JOBS="$2"; mkdir -p logs
grep -v '^\s*$' "$JOBS" | xargs -P "$P" -L 1 bash -c 'n=$(echo "$@" | tr " " "_"); python3 bench.py "$@" > "logs/$BENCH_TAG-$n.log" 2>&1; echo "done $n: $(tail -1 logs/$BENCH_TAG-$n.log)"' _
