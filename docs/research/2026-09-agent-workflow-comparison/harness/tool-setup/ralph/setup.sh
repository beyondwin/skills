#!/bin/bash
# Usage: setup.sh <repo_dir> ["ultimate goal sentence"]
# Installs the Ralph Playbook files (ghuntley/how-to-ralph-wiggum @ 88d488a, files/*) into an
# existing git repo. Deviations from upstream (push neutralized) are marked "RALPH-HARNESS".
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/repo/files"
REPO="${1:?usage: setup.sh <repo_dir> [goal]}"
GOAL="${2:-}"
cd "$REPO"
git rev-parse --is-inside-work-tree >/dev/null || { echo "not a git repo: $REPO"; exit 1; }

for f in PROMPT_plan.md PROMPT_build.md loop.sh AGENTS.md; do
  if [ -e "$f" ] && [ "$f" = AGENTS.md ]; then echo "WARN: AGENTS.md exists, left untouched"; continue; fi
  cp "$SRC/$f" "$f"
done
# Upstream ships IMPLEMENTATION_PLAN.md as a one-line HTML comment; copy it (unless present) so the
# prompts' @IMPLEMENTATION_PLAN.md reference resolves to a real file (smoke without it: haiku wrote "@IMPLEMENTATION_PLAN.md").
[ -e IMPLEMENTATION_PLAN.md ] || cp "$SRC/IMPLEMENTATION_PLAN.md" IMPLEMENTATION_PLAN.md
mkdir -p specs
chmod +x loop.sh

# RALPH-HARNESS: fill the [project-specific goal] placeholder of PROMPT_plan.md
if [ -n "$GOAL" ]; then
  GOAL="$GOAL" python3 - <<'PY'
import os; p="PROMPT_plan.md"; s=open(p).read()
open(p,"w").write(s.replace("[project-specific goal]", os.environ["GOAL"]))
PY
else
  echo "WARN: no goal given; PROMPT_plan.md still contains [project-specific goal]"
fi

# RALPH-HARNESS: neutralize push. (a) prompt sentence removed
python3 - <<'PY'
p="PROMPT_build.md"; s=open(p).read()
t=s.replace(" After the commit, `git push`.", "")
assert t!=s, "push sentence not found"; open(p,"w").write(t)
p="loop.sh"; s=open(p).read()
old='''    git push origin "$CURRENT_BRANCH" || {
        echo "Failed to push. Creating remote branch..."
        git push -u origin "$CURRENT_BRANCH"
    }'''
new='''    # RALPH-HARNESS: push disabled for the comparison
    # git push origin "$CURRENT_BRANCH" || { git push -u origin "$CURRENT_BRANCH"; }
    :'''
assert old in s, "push block not found"; open(p,"w").write(s.replace(old,new))
PY
# (b) repo-local pushurl made unroutable if a remote exists
for r in $(git remote); do git config "remote.$r.pushurl" "no-push://disabled-by-ralph-harness"; done
# (c) run_loop.sh additionally passes --disallowedTools "Bash(git push:*)"
echo "Ralph files installed in $REPO: $(ls PROMPT_plan.md PROMPT_build.md loop.sh AGENTS.md | tr '\n' ' ')specs/"
