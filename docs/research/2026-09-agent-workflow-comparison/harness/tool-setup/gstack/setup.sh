#!/usr/bin/env bash
# Idempotent project-local install of gstack into <repo_dir>/.claude/skills/.
# All of gstack's ~ writes (hooks in settings.json, config, state) are sandboxed
# into this scratch dir: fake HOME for setup, GSTACK_HOME for runtime.
#
# Usage:  setup.sh <repo_dir>
# Then run claude inside <repo_dir> with:  source <scratch>/env.sh
set -euo pipefail
S="$(cd "$(dirname "$0")" && pwd -P)"
REPO_DIR="$(cd "${1:?usage: setup.sh <repo_dir>}" && pwd -P)"
SRC="$S/repo"                      # git clone --depth 1 of garrytan/gstack
export HOME="$S/home"              # setup writes ~/.claude/settings.json hooks here, not real home
export GSTACK_HOME="${GSTACK_HOME:-$S/state}"      # per-trial state when the driver sets it
export GSTACK_PLAN_DIR="${GSTACK_PLAN_DIR:-$GSTACK_HOME/plans}"
mkdir -p "$HOME" "$GSTACK_HOME" "$GSTACK_PLAN_DIR"

[ -d "$SRC/.git" ] || git clone --depth 1 https://github.com/garrytan/gstack "$SRC"
command -v bun >/dev/null || { echo "WARN: bun missing; browse/make-pdf/design binaries will not build; non-browser skills still load" >&2; }

# 1. Link the pack into the project exactly where the vendored layout expects it.
mkdir -p "$REPO_DIR/.claude/skills"
ln -sfn "$SRC" "$REPO_DIR/.claude/skills/gstack"

# 2. Run gstack's own setup through the symlinked path (INSTALL_GSTACK_DIR uses
#    `pwd`, so INSTALL_SKILLS_DIR = <repo>/.claude/skills). It builds binaries in
#    $SRC once (skips if fresh) and creates <repo>/.claude/skills/<name>/SKILL.md
#    symlinks + _gstack-command alias. Chromium download skipped unless asked.
( cd "$REPO_DIR" && GSTACK_SKIP_PLAYWRIGHT="${GSTACK_SKIP_PLAYWRIGHT:-1}" \
    "$REPO_DIR/.claude/skills/gstack/setup" --host claude --no-prefix --no-team \
    --no-plan-tune-hooks --no-timeline-stop-hook -q ) </dev/null

# 2b. Rewrite hardcoded global paths in the pack's markdown (SKILL.md + sections,
#     checklists, docs the skills read). Without this ~1,000 command lines like
#     `~/.claude/skills/gstack/bin/gstack-slug` miss (no global install) and
#     `~/.gstack/projects/...` writes land in the REAL home. Idempotent: rewritten
#     paths no longer match. Re-applied every run because setup may regenerate.
find "$SRC" -name '*.md' -not -path '*/node_modules/*' -not -path '*/.git/*' \
     -not -path "$SRC/test/*" -not -path "$SRC/.agents/*" -print0 |
  { xargs -0 grep -lE '(~|\$HOME|\$\{HOME\})/\.(claude/skills/gstack|gstack)' 2>/dev/null || true; } |
  while IFS= read -r f; do
    sed -i '' -E \
      -e "s#(~|\\\$HOME|\\\$\\{HOME\\})/\\.claude/skills/gstack#$SRC#g" \
      -e "s#(~|\\\$HOME|\\\$\\{HOME\\})/\\.gstack#\\\${GSTACK_HOME}#g" "$f"
  done

# 3. Pre-seed "user already onboarded" state so the first skill turn is not
#    consumed by lake-intro / telemetry / proactive / routing / update prompts.
CFG="$SRC/bin/gstack-config"
"$CFG" set telemetry off >/dev/null
"$CFG" set proactive true >/dev/null
"$CFG" set routing_declined true >/dev/null
"$CFG" set update_check false >/dev/null
for m in .completeness-intro-seen .telemetry-prompted .proactive-prompted \
         .feature-prompted-model-overlay .activated .first-loop-tip-shown \
         .writing-style-prompted; do touch "$GSTACK_HOME/$m"; done

# 4. Keep the install out of the project's git status.
if [ -d "$REPO_DIR/.git" ]; then
  EX="$REPO_DIR/.git/info/exclude"; mkdir -p "$(dirname "$EX")"
  grep -qx '.claude/skills/' "$EX" 2>/dev/null || echo '.claude/skills/' >> "$EX"
fi

test -x "$REPO_DIR/.claude/skills/gstack/bin/gstack-skill-start"
echo "gstack installed: $(ls "$REPO_DIR/.claude/skills" | grep -vc '^gstack$') skill entries in $REPO_DIR/.claude/skills"
