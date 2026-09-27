#!/usr/bin/env bash
# probe wrapper: install OpenSpec without the helper settings.json (PATH comes from the driver env, like a global install)
set -euo pipefail
COMMIT=0 bash "$(dirname "$0")/setup.sh" "$1"
rm -f "$1/.claude/settings.json"
