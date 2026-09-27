#!/usr/bin/env bash
# Set up GitHub Spec Kit (core SDD, Claude Code skills mode) in an existing git repo.
# Usage: setup.sh <repo_dir>
# - Uses the local clone next to this script (pinned commit), bundled assets only (no template download).
# - Keeps uv cache/tools inside this scratch dir; installs nothing globally.
# - Never runs `git init`, never commits, never touches existing history. Files are left untracked.
# - Idempotent: if .specify/init-options.json already exists, does nothing (re-running
#   `specify init --force` would overwrite an edited .specify/memory/constitution.md).
# - Optional: SPECKIT_EXTENSIONS="git bug" to add bundled extensions (default: none = upstream default).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLONE="$HERE/clone"
REPO="${1:?usage: setup.sh <repo_dir>}"
REPO="$(cd "$REPO" && pwd)"

export UV_CACHE_DIR="$HERE/uv-cache"
export UV_TOOL_DIR="$HERE/uv-tools"
export UV_PYTHON_INSTALL_DIR="$HERE/uv-python"

[ -d "$CLONE/.git" ] || { echo "missing clone at $CLONE" >&2; exit 1; }
git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "$REPO is not a git repo" >&2; exit 1; }

if [ -f "$REPO/.specify/init-options.json" ] && [ -d "$REPO/.claude/skills/speckit-specify" ]; then
  echo "spec-kit already set up in $REPO; nothing to do"
  exit 0
fi

ext_args=()
for e in ${SPECKIT_EXTENSIONS:-}; do ext_args+=(--extension "$e"); done

HEAD_BEFORE="$(git -C "$REPO" rev-parse -q --verify HEAD || echo none)"
( cd "$REPO" && uvx --from "$CLONE" specify init --here --integration claude --script sh \
    --force --non-interactive --ignore-agent-tools ${ext_args[@]+"${ext_args[@]}"} )
HEAD_AFTER="$(git -C "$REPO" rev-parse -q --verify HEAD || echo none)"
[ "$HEAD_BEFORE" = "$HEAD_AFTER" ] || { echo "WARNING: HEAD changed ($HEAD_BEFORE -> $HEAD_AFTER)" >&2; exit 1; }

echo "spec-kit $(git -C "$CLONE" rev-parse --short HEAD) set up in $REPO. Added:"
git -C "$REPO" status --short -uall -- .claude .specify
