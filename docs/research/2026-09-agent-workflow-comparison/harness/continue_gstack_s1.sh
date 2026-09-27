#!/bin/bash
cd "$(dirname "$0")"
until grep -q "CONTINUE DONE" logs/s2-gstack-continue.log 2>/dev/null; do sleep 30; done
PROBE_TAG=main python3 driver.py s1 gstack --continue 16 >> logs/s1-gstack-continue.log 2>&1
echo "CONTINUE DONE rc=$?" >> logs/s1-gstack-continue.log
