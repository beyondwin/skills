#!/bin/bash
# Usage: run_loop.sh <repo_dir> <plan|build> <max_iters>     (RALPH_MODEL=opus by default)
# Headless equivalent of upstream files/loop.sh: `cat PROMPT_<mode>.md | claude -p ...` per iteration,
# fresh context each time. Never pushes. Stream per iteration -> <repo_dir>/../ralph_iter_NN.jsonl
set -uo pipefail
REPO="$(cd "${1:?repo_dir}" && pwd)"; MODE="${2:?plan|build}"; MAX="${3:?max_iters}"
MODEL="${RALPH_MODEL:-opus}"
case "$MODE" in plan) PROMPT_FILE=PROMPT_plan.md;; build) PROMPT_FILE=PROMPT_build.md;; *) echo "mode must be plan|build"; exit 2;; esac
cd "$REPO"
[ -f "$PROMPT_FILE" ] || { echo "Error: $PROMPT_FILE not found (run setup.sh)"; exit 1; }
if [ "$MODE" = build ] && ! grep -qv '^\s*\(<!--.*-->\)\?\s*$' IMPLEMENTATION_PLAN.md 2>/dev/null; then
  echo "Error: IMPLEMENTATION_PLAN.md missing/empty; run plan mode first"; exit 1; fi
OUTDIR="$(cd .. && pwd)"; MANIFEST="$OUTDIR/ralph_iters.tsv"
snap() { echo "$(git rev-parse HEAD 2>/dev/null)|$(git status --porcelain | shasum | cut -c1-12)|$(shasum IMPLEMENTATION_PLAN.md 2>/dev/null | cut -c1-12)|$(git diff | shasum | cut -c1-12)"; }
echo "Mode: $MODE  Prompt: $PROMPT_FILE  Branch: $(git branch --show-current)  Max: $MAX  Model: $MODEL"
i=0; nocommit=0
while [ "$i" -lt "$MAX" ]; do
  last=$(ls "$OUTDIR"/ralph_iter_*.jsonl 2>/dev/null | sed -E 's/.*ralph_iter_0*([0-9]+)\.jsonl/\1/' | sort -n | tail -1)
  NN=$(printf '%02d' $(( ${last:-0} + 1 ))); OUT="$OUTDIR/ralph_iter_$NN.jsonl"
  before=$(snap); head_before=$(git rev-parse --short HEAD 2>/dev/null)
  cat "$PROMPT_FILE" | claude -p \
      --setting-sources project \
      --permission-mode bypassPermissions \
      --model "$MODEL" \
      --output-format stream-json \
      --verbose \
      --strict-mcp-config \
      --disallowedTools "Bash(git push:*)" > "$OUT"
  rc=$?
  # RALPH-HARNESS safety net: a model that takes "@IMPLEMENTATION_PLAN.md" literally writes that filename
  if [ -f "@IMPLEMENTATION_PLAN.md" ]; then echo "  NOTE: merging stray @IMPLEMENTATION_PLAN.md"; mv -f "@IMPLEMENTATION_PLAN.md" IMPLEMENTATION_PLAN.md; fi
  i=$((i+1)); after=$(snap)
  printf '%s\t%s\t%s\t%s\trc=%s\n' "$NN" "$MODE" "$head_before" "$(git rev-parse --short HEAD 2>/dev/null)" "$rc" >> "$MANIFEST"
  python3 - "$OUT" <<'PY'
import json,sys
for l in open(sys.argv[1]):
    try: d=json.loads(l)
    except Exception: continue
    if d.get("type")=="result":
        print(f"  result: subtype={d.get('subtype')} turns={d.get('num_turns')} cost=${d.get('total_cost_usd')} dur={d.get('duration_ms')}ms")
        print("  " + str(d.get("result",""))[:400].replace("\n","\n  "))
PY
  echo "======================== LOOP $i ($OUT) ========================"
  [ "$rc" -ne 0 ] && { echo "claude exited rc=$rc; stopping"; break; }
  [ "$before" = "$after" ] && { echo "No changes this iteration; stopping"; break; }
  if [ "$MODE" = build ]; then
    if [ "$head_before" = "$(git rev-parse --short HEAD 2>/dev/null)" ]; then nocommit=$((nocommit+1)); else nocommit=0; fi
    [ "$nocommit" -ge 2 ] && { echo "Two build iterations without a commit; stopping"; break; }
  fi
  if [ "$MODE" = build ] && grep -q -- '- \[x\]' IMPLEMENTATION_PLAN.md 2>/dev/null && ! grep -q -- '- \[ \]' IMPLEMENTATION_PLAN.md; then
    echo "Plan has no unchecked items; stopping"; break; fi
done
[ "$i" -ge "$MAX" ] && echo "Reached max iterations: $MAX"
exit 0
