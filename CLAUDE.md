@AGENTS.md

# Claude Code notes

These add Claude Code facts to AGENTS.md. AGENTS.md wins on any conflict.

## Working tree

- Inspect actual installation targets before changing them. A symlink from a host's skill
  directory to this checkout makes edits visible to sessions that use that link.
- Check the branch and working-tree state before editing or committing. Use an isolated
  worktree when concurrent work would conflict, and integrate only within the user's scope.

## Models and subagents

- Use the model selected for the task. Record the model and effort that actually ran from
  the transcript; a static model list or local setting is not execution evidence.
- Brief subagents with the files, the exact output shape, and the read-only or write scope.
  State limits once, plainly; capitals and repeated warnings add nothing.

## Live runs (`claude -p`)

Run only within explicitly approved scope (AGENTS.md).

- Isolate with `--setting-sources project --strict-mcp-config`, not a fake `HOME`: a fake
  `HOME` logs `claude -p` out on macOS. Unset `CLAUDECODE` and `CLAUDE_CODE_*` first.
- Typical launch: `claude -p --output-format stream-json --verbose --setting-sources project
  --strict-mcp-config --permission-mode bypassPermissions --model opus --effort high`.
- Set effort with `--effort` or `CLAUDE_CODE_EFFORT_LEVEL`. `CLAUDE_EFFORT` is output only, and
  `--setting-sources project` skips the user's `effortLevel`, so a launch without `--effort`
  runs at the session default.
- The model and effort that actually ran are in the transcript (`message.model`, top-level
  `effort`), not in `advisorModel`.
- `--resume` reports `total_cost_usd` as a running total. Take the last value per session;
  sum only across sessions.
- Headless sessions end at end of turn and kill backgrounded children. Wait in the
  foreground (for example `run_worker.py wait`).
- Use a fresh fixture repo per run at a fixed path, with no `cp -R` or symlinks, and record
  the SHA-256 of the skill text each run used.
