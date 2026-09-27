#!/usr/bin/env bash
# Install BMAD-METHOD (npm bmad-method, stable) into a repo dir for Claude Code, no prompts.
# Usage: setup.sh <repo_dir>
# Adds: <repo>/.claude/skills/bmad-*/ (29 skills), <repo>/_bmad/ (config, manifests, render scripts),
#       <repo>/_bmad-output/ (empty artifact folder). Nothing is written to ~/.claude.
# Requires: node/npx >= 20.12, uv + python3.11 (BMad skills render via `uv run` at invocation time).
set -euo pipefail
REPO="${1:?usage: setup.sh <repo_dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
BMAD_VERSION="${BMAD_VERSION:-6.12.0}"
export npm_config_cache="${npm_config_cache:-$HERE/.npm}"
export npm_config_update_notifier=false
mkdir -p "$REPO"
REPO="$(cd "$REPO" && pwd)"
ACTION=()
if [ -f "$REPO/_bmad/_config/manifest.yaml" ]; then ACTION=(--action quick-update); fi
cd "$REPO"
npx -y "bmad-method@${BMAD_VERSION}" install \
  --directory "$REPO" --modules bmm --tools claude-code --yes --no-shims \
  --user-name User --communication-language "${BMAD_LANG:-Korean}" --document-output-language "${BMAD_LANG:-Korean}" \
  "${ACTION[@]+"${ACTION[@]}"}" </dev/null
test -f "$REPO/.claude/skills/bmad-build/SKILL.md"
test -f "$REPO/_bmad/scripts/render_skill.py"
echo "BMAD ${BMAD_VERSION} installed: $(ls -d "$REPO"/.claude/skills/bmad-* | wc -l | tr -d ' ') skills in $REPO/.claude/skills"
