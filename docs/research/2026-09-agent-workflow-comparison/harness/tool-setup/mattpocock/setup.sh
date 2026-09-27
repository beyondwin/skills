#!/usr/bin/env bash
# Headless stand-in for the interactive /setup-matt-pocock-skills step.
# Writes what that skill would write for: local-markdown tracker, default
# triage labels, single-context domain docs. Idempotent.
# Usage: setup.sh <repo_dir>
set -euo pipefail
REPO="${1:?usage: setup.sh <repo_dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
SEED="$HERE/repo/skills/engineering/setup-matt-pocock-skills"
[ -d "$SEED" ] || { echo "missing seed dir $SEED" >&2; exit 1; }

mkdir -p "$REPO/docs/agents"
cp "$SEED/issue-tracker-local.md" "$REPO/docs/agents/issue-tracker.md"
cp "$SEED/domain.md"              "$REPO/docs/agents/domain.md"
cp "$SEED/triage-labels.md"       "$REPO/docs/agents/triage-labels.md"

# Pick file per the skill's rule: CLAUDE.md if present, else AGENTS.md, else create CLAUDE.md.
if   [ -f "$REPO/CLAUDE.md" ]; then TARGET="$REPO/CLAUDE.md"
elif [ -f "$REPO/AGENTS.md" ]; then TARGET="$REPO/AGENTS.md"
else TARGET="$REPO/CLAUDE.md"; : > "$TARGET"
fi

if ! grep -q '^## Agent skills' "$TARGET"; then
  [ -s "$TARGET" ] && printf '\n' >> "$TARGET"
  cat >> "$TARGET" <<'EOF'
## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
EOF
fi
echo "setup done: $TARGET, $REPO/docs/agents/"
