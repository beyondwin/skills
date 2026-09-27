#!/bin/bash
cd "$(dirname "$0")"
until [ -e runs/main/s1-gstack/meta.json ]; do sleep 30; done
echo "gstack s1 done" >> logs/s2-gstack-continue.log
PROBE_TAG=main python3 driver.py s2 gstack --continue 16 >> logs/s2-gstack-continue.log 2>&1
echo "CONTINUE DONE rc=$?" >> logs/s2-gstack-continue.log
