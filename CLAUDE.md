@AGENTS.md

# Claude Code notes

These add Claude Code facts to AGENTS.md. AGENTS.md wins on any conflict.

## Working tree

- `~/.claude/skills/<name>` and `~/.agents/skills/<name>` are symlinks to `skills/<name>/` in this
  checkout. An edit there changes every running session's skill at once.
- Several sessions share this checkout and move `HEAD` without notice. For multi-commit work,
  `git worktree add` a private checkout in your scratchpad, commit and verify there, and
  fast-forward `main` at the end. Check `git rev-parse --abbrev-ref HEAD` before any commit in
  the shared tree.

## Models and subagents

- Current models: Opus 5.5 (`claude-opus-5-5`, alias `opus`), Fable 5.1 (`claude-fable-5-1`,
  alias `fable`), Sonnet 5.5 (`claude-sonnet-5-5`, alias `sonnet`), Haiku 4.5. Write model names
  in docs and fixtures with these IDs.
- Waygent's Claude Code tiers are `sonnet` → `opus` → `fable`; name the model in every
  dispatch (see `skills/waygent/SKILL.md`, `Models`).
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
