#!/usr/bin/env bash
# probe wrapper: per-trial gstack state ($GSTACK_HOME from the driver), local bare origin (gstack /review fetches origin), feature branch (gstack never creates one)
set -euo pipefail
S="$(cd "$(dirname "$0")" && pwd -P)"
REPO="$(cd "$1" && pwd -P)"
: "${GSTACK_HOME:?driver must set a per-trial GSTACK_HOME}"
rm -rf "$GSTACK_HOME"; mkdir -p "$GSTACK_HOME/plans"
bash "$S/setup.sh" "$REPO"
git init -q --bare "$REPO/../origin.git"
git -C "$REPO" remote add origin "$REPO/../origin.git" 2>/dev/null || true
git -C "$REPO" push -q origin main
git -C "$REPO" checkout -q -b work
