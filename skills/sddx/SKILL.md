---
name: sddx
description: Use when executing a Superpowers implementation plan with an external Cursor or Grok CLI implementer instead of a native implementer subagent. Use when the user runs /sddx or $sddx, asks to run SDD with Grok as implementer, or wants the current Claude Code or Codex session to stay orchestrator and reviewer. Do not use for writing a spec or plan, pre-sdd-review, or native subagent-driven-development without an external implementer.
license: Apache-2.0
compatibility: Requires a local Git repository, an implementation plan file, and Claude Code or Codex as the orchestrator host. Implementer CLIs are optional and resolved at runtime.
metadata:
  version: "1.1.0"
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

Select reviewer effort separately, including on re-review and final review.
On Claude Code, High means dispatching the reviewer the way SDD already does,
with no `model` argument, so model and session effort are both inherited.
XHigh means dispatching `subagent_type: sddx-reviewer-xhigh`, still with no
`model` argument. Never pass a `model` argument that is not the orchestrator's
own model; on Claude Code that means passing none at all.

| Review scope | Effort |
| --- | --- |
| Clear requirements, local changes, straightforward integration | High |
| Changes to locking, ordering, or concurrently shared state; changes to an auth, permission, secret, or sandbox boundary; a round 4-5 re-review; a defect the reviews keep missing | XHigh |

Decide from the review-package stat, the task brief, the changed paths, and
the ledger. Do not read the diff body to pick effort; that is reviewing the
task yourself and it pollutes controller context. File count, line count, a
hard implementation, a short diff, and "this is the final review" are not
triggers. A re-review keeps the original defect's risk; a smaller diff alone
does not lower it.

Escalation is a floor, not a ceiling. If the session already runs at XHigh or
above, the plain dispatch already satisfies it, so do not use the escalation
agent and do not lower the session.

Agent definitions ship with the skill. Do not create or edit one during a run.

Record every review dispatch in the ledger. High is one line,
`Task N review: sddx default — high`. XHigh must name a trigger and a
referent, `Task N review: sddx-reviewer-xhigh — <trigger>: <path or brief
phrase>`. A trigger you cannot tie to a path is not a trigger; use High.
The model is not part of these lines; it is always the orchestrator's. If the
host cannot confirm the model ID, record that once for the run rather than on
each dispatch.

This section's effort escalation needs the definition to be present. It is
absent on Codex, and on Claude Code it can be absent if the definition did not
load. When it is unavailable, report that the requested effort cannot be set,
continue at the plain dispatch, and do not substitute another model or effort.
Do not create the definition. A missing definition never blocks the run.

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
- Reviewer XHigh because the diff is long
- Reviewer High because the diff is short
- Reviewer XHigh because the worker ran XHigh
- Final review XHigh because it is final
- Reviewer XHigh to be safe
- Reading the diff body to pick reviewer effort
- Re-dispatching at XHigh to clear `Cannot verify from diff`
- Lowering the reviewer model because effort is XHigh
- `sddx-reviewer-xhigh` in the ledger without a trigger and a path
- Passing a `model` override to a reviewer
- Escalating when the session already runs at XHigh or above
- Writing or editing an agent definition during a run

All of these except the reviewer flags mean: stop, restore the overlay,
continue SDD with the external worker.

For the reviewer flags the remedy is different: stop, re-dispatch the review
with the correct definition and no `model` override, and record it in the
ledger.
