#!/bin/bash
# judge every finished run that has no judge.json yet (max 6 parallel)
cd "$(dirname "$0")"
ls -d runs/main/*/ | while read d; do
  [ -e "$d/meta.json" ] && [ ! -e "$d/judge.json" ] && echo "$d"
done | xargs -P 6 -I{} sh -c 'python3 judge.py {} >> logs/judge.log 2>&1; echo "JUDGED {}" >> logs/judge.log'
echo "JUDGE PASS DONE" >> logs/judge.log
