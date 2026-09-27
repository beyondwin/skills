#!/usr/bin/env bash
# Recreate the probe work directory with every tool pinned to the commit that was measured.
# Usage: fetch_tools.sh <work_dir>
# Afterwards run each tool-setup/<tool>/ script from inside <work_dir>/tools/<tool>/ (see README.md).
set -euo pipefail
WORK="${1:?usage: fetch_tools.sh <work_dir>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$WORK/tools" "$WORK/probe" "$WORK/plugins/wo/.claude-plugin" "$WORK/plugins/wo/skills"

pin() {  # pin <url> <dest> <sha>
  [ -d "$2/.git" ] || git clone -q "$1" "$2"
  git -C "$2" fetch -q --depth 1 origin "$3" 2>/dev/null || git -C "$2" fetch -q origin
  git -C "$2" checkout -q "$3"
}

pin https://github.com/prekuter/dryforge          "$WORK/dryforge"                 904f257
pin https://github.com/jha0313/skills_repo        "$WORK/skills_repo"              900d395
pin https://github.com/mattpocock/skills          "$WORK/tools/mattpocock/repo"    c55ee46
pin https://github.com/garrytan/gstack            "$WORK/tools/gstack/repo"        01593aa
pin https://github.com/bmad-code-org/BMAD-METHOD  "$WORK/tools/bmad/repo"          5e33d3c
pin https://github.com/github/spec-kit            "$WORK/tools/speckit/clone"      c00dc05
pin https://github.com/Fission-AI/OpenSpec        "$WORK/tools/openspec/src"       79b6aa9
pin https://github.com/ghuntley/how-to-ralph-wiggum "$WORK/tools/ralph/repo"       88d488a

# workflow-orchestrator is a bare skill folder; wrap it as a plugin so --plugin-dir can load it.
cp -R "$WORK/skills_repo/workflow-orchestrator" "$WORK/plugins/wo/skills/"
printf '{"name":"wo","version":"1.5.0","description":"workflow-orchestrator wrapper"}\n' \
  > "$WORK/plugins/wo/.claude-plugin/plugin.json"

for t in mattpocock gstack bmad speckit openspec ralph; do
  cp "$HERE"/tool-setup/"$t"/*.sh "$WORK/tools/$t/"
done
cp -R "$HERE/driver.py" "$HERE/judge.py" "$HERE/runner.py" "$HERE/aggregate.py" "$HERE/judge_all.sh" \
      "$HERE/tables.py" "$HERE/build_report.py" "$HERE/s4_coexist.py" "$HERE"/continue_gstack*.sh \
      "$HERE/conditions.json" "$HERE/personas" "$HERE/fixtures" "$WORK/probe/"
mkdir -p "$WORK/probe/fixtures/empty"
echo "superpowers is not fetched: the probe used the locally installed 6.4.1 (commit 5bf4e78) at ~/.agents/plugins/superpowers."
echo "work dir ready: $WORK"
