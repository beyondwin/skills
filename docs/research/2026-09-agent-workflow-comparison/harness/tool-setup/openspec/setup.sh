#!/usr/bin/env bash
# Idempotently set up OpenSpec 1.13.2 (core profile, Claude Code) in an existing git repo.
# Usage: setup.sh <repo_dir>      (COMMIT=0 to skip committing the scaffold)
set -euo pipefail
S="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${1:?usage: setup.sh <repo_dir>}"
REPO="$(cd "$REPO" && pwd)"
VERSION=1.13.2
git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null

export npm_config_cache="$S/.npm" XDG_CONFIG_HOME="$S/xdg" \
  OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 OPENSPEC_NO_UPDATE_CHECK=1 OPENSPEC_NO_ANIMATION=1

# 1. Pinned CLI, installed once under the scratch dir (never global).
BIN="$S/cli/node_modules/.bin"
if [ "$("$BIN/openspec" --version 2>/dev/null || true)" != "$VERSION" ]; then
  npm install --silent --no-audit --no-fund --prefix "$S/cli" "@fission-ai/openspec@$VERSION"
fi
export PATH="$BIN:$PATH"

# 2. Scaffold (re-running init with the same args is a no-op; verified).
( cd "$REPO" && openspec init --tools claude --profile core --no-animation . >/dev/null )

# 3. Make the CLI reachable for the skills' bare `openspec ...` calls at runtime.
#    Project settings env (loaded by --setting-sources project) + a sourceable env file.
mkdir -p "$REPO/.claude"
cat > "$REPO/.claude/settings.json" <<EOF
{
  "env": {
    "PATH": "$PATH",
    "XDG_CONFIG_HOME": "$S/xdg",
    "OPENSPEC_TELEMETRY": "0",
    "DO_NOT_TRACK": "1",
    "OPENSPEC_NO_UPDATE_CHECK": "1",
    "OPENSPEC_NO_ANIMATION": "1"
  }
}
EOF
cat > "$S/env.sh" <<EOF
export PATH="$BIN:\$PATH" XDG_CONFIG_HOME="$S/xdg" OPENSPEC_TELEMETRY=0 DO_NOT_TRACK=1 OPENSPEC_NO_UPDATE_CHECK=1 OPENSPEC_NO_ANIMATION=1
EOF

# 4. Sanity: CLI sees the root.
( cd "$REPO" && openspec list --json | grep -q '"path"' ) || { echo "openspec root not detected" >&2; exit 1; }

# 5. Commit scaffold so each run starts from a clean baseline.
if [ "${COMMIT:-1}" = 1 ] && [ -n "$(git -C "$REPO" status --porcelain -- .claude openspec)" ]; then
  git -C "$REPO" add .claude openspec
  git -C "$REPO" -c user.name=setup -c user.email=setup@local commit -q -m "chore: set up OpenSpec $VERSION (claude, core profile)"
fi
echo "OpenSpec $VERSION ready in $REPO (source $S/env.sh before launching claude)"
