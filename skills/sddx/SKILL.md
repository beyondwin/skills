---
name: sddx
description: Use when executing a Superpowers implementation plan with an external Cursor or Grok CLI implementer instead of a native implementer subagent. Use when the user runs /sddx or $sddx, asks to run SDD with Grok as implementer, or wants the current Claude Code or Codex session to stay orchestrator and reviewer. Do not use for writing a spec or plan, pre-sdd-review, or native subagent-driven-development without an external implementer.
license: Apache-2.0
compatibility: Requires a local Git repository, an implementation plan file, and Claude Code or Codex as the orchestrator host. Implementer CLIs are optional and resolved at runtime.
metadata:
  version: "1.0.0"
  updated_at: "2026-09-11"
---

# SDDx

Use installed Superpowers `subagent-driven-development` unchanged, except
implementer dispatch.

<HARD-GATE>
Do not copy Superpowers SDD into this skill.
Do not edit Superpowers files.
Do not implement in the orchestrator session.
Do not activate on native SDD, executing-plans, writing-plans, or
pre-sdd-review without an explicit /sddx or $sddx or an explicit external
implementer request.
Violating the letter of this gate is violating the spirit.
</HARD-GATE>

Prefer explicit invocation: `$sddx` on Codex and `/sddx` on Claude Code.

## Arguments

    sddx <plan-file> [cursor|grok|c|g]

If the plan path is missing or is not a file, stop. Do not guess. One plan
per invocation.

`c` means `cursor`. `g` means `grok`. With a backend argument, skip the
picker. Without one, ask once for this plan.

- Claude Code: AskUserQuestion. Options are Cursor Agent CLI (Grok model)
  and Grok Build CLI.
- Codex: numbered options, wait for one answer.

If only one backend is available, show that fact and the missing backend
`reason`, then still confirm before proceeding when argv is absent. Do not
auto-select the only CLI.

Run `python3 "<skill-root>/scripts/resolve_backend.py" --backend <id> --json`
from the loaded skill root. If `available` is false for the requested
backend, stop and report `reason`. Do not automatically switch backends.
If both backends are unavailable, stop as BLOCKED.

Write `Backend: cursor|grok` into the Superpowers SDD ledger for this plan.
Keep that backend for every later task.

## Controller

The current session model is the orchestrator and reviewer. Follow
subagent-driven-development for worktree, ledger, task-brief,
review-package, the fix loop, whole-branch review, and
finishing-a-development-branch.

When SDD would dispatch an implementer subagent, do not. Dispatch the
external worker using `references/dispatch.md` and
`references/worker-prompt.md`.

Task reviewers, scoped re-reviewers, and the final reviewer stay native
(Claude Code Task or Codex spawn_agent).

Effort for the implementer is High unless the task is hard implementation
(concurrency, races, tangled side effects, or High already failed review
on this task), then XHigh. Architecture ambiguity is a ruling, not XHigh.
If the worker returns NEEDS_CONTEXT or BLOCKED, rule and re-dispatch.

Fresh worker per task. Resume the same worker session for fix rounds 1-3.
Rounds 4-5 use a fresh worker at XHigh. Record
`Task N worker-session: <id>` in the ledger.

Do not pass `--worktree` to the worker. The worker cwd is the current
Superpowers worktree.

Do not copy host credentials or environment values into the worker prompt
or `--prompt-file`. If the worker needs a host-outside side effect (push,
publish, shared-branch update), stop and return BLOCKED. Do not treat that
as review-passable DONE.

## Red flags

- Native implementer subagent
- Copying SDD into this file
- Asking for a backend on every task
- Raising effort because the design is unclear
- Treating PATH `agent` as Cursor
- Auto-failover when Cursor is missing
- Auto-selecting the only available backend without confirmation
- Controller editing application code
- Worker git push, publish, or shared-branch update
- Pasting host secrets into the worker prompt

All of these mean: stop, restore the overlay, continue SDD with the
external worker.
