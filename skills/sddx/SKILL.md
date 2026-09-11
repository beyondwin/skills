---
name: sddx
description: Use when executing a Superpowers implementation plan with an external Cursor or Grok CLI implementer instead of a native implementer subagent. Use when the user runs /sddx or $sddx, asks to run SDD with Grok as implementer, or wants the current Claude Code or Codex session to stay orchestrator and reviewer. Do not use for writing a spec or plan, pre-sdd-review, or native subagent-driven-development without an external implementer.
license: Apache-2.0
compatibility: Requires a local Git repository, an implementation plan file, and Claude Code or Codex as the orchestrator host. Implementer CLIs are optional and resolved at runtime.
metadata:
  version: "1.0.3"
  updated_at: "2026-09-11"
---

# SDDx

Use installed Superpowers `subagent-driven-development` for the workflow.
SDDx overrides implementer dispatch, reviewer model/effort selection, and
worker evidence checks below. Keep the remaining SDD workflow unchanged.

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

The current session is the orchestrator. Follow
subagent-driven-development for worktree, ledger, task-brief,
review-package, the fix loop, whole-branch review, and
finishing-a-development-branch.

When SDD would dispatch an implementer subagent, do not. Dispatch the
external worker using `references/dispatch.md` and
`references/worker-prompt.md`.

Process exit 0 is not task completion. Verify the report, actual test exit
codes, task commits, tool-call/results log, and native review. Record role
compliance as PASS, FAIL, or UNVERIFIED in the existing ledger. A successful
prohibited read is FAIL even when tests pass or the report says no concerns.
Missing or incomplete tool evidence is UNVERIFIED, never PASS. Neither FAIL
nor UNVERIFIED permits a clean DONE. Check shell commands/results as well as
file-read and search tools; plan excerpts in search results are prohibited
content too. An attempted read alone does not prove content was returned.
Give the reviewer the evidence and any discrepancy with the worker report.
`Search paths` limits content searches. Filename-only listings inside the
current worktree (including its root) and direct reads of repository
ignore/build/test configuration needed for the task are allowed inspection,
not scope deviations. With no other deviation, `Scope deviations: none` is
correct; do not require a concern or ruling solely for these actions. This
permission never covers reading full-plan content, credentials, or secrets.

BLOCKED, NEEDS_CONTEXT, a missing report, or an unclear result must not become
DONE. Resolve concerns through the existing ruling procedure. A later apology
or compliant call cannot erase an earlier violation. Do not require a new
commit just to correct a report or verify existing code.

## Reviewers

Task reviewers, scoped re-reviewers, and the final reviewer stay native
(Claude Code Task or Codex spawn_agent) and use the active orchestrator's
model. This overrides SDD's cheaper-model and strongest-final-model choices.
Inherit the model when the host supports it; otherwise specify the confirmed
orchestrator model ID. Do not pick a separate reviewer model or hardcode a
preferred model family. If the model ID is unavailable, record it as inherited
and unknown rather than guess.

Select reviewer effort separately, including on re-review and final review:

| Review scope | Effort |
| --- | --- |
| Clear requirements, local changes, straightforward integration | High |
| Complex cross-task effects, concurrency/races, security/permissions, or repeatedly missed defects | XHigh |

Keep the original defect's risk in scope on re-review; a small diff alone
does not justify lowering effort. Do not inherit a lower session effort.
Record model (or inheritance), effort, and a short reason in the ledger.
If the host cannot preserve the model or set the requested effort, report
that limitation; do not silently substitute another model or effort.

## Implementer

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
