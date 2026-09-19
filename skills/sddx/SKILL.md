---
name: sddx
description: Use when the user runs /sddx or $sddx. Do not use for writing a spec or plan, writing-plans, executing-plans including Native inline execution, pre-sdd-review, native subagent-driven-development, or any request that does not contain /sddx or $sddx.
license: Apache-2.0
compatibility: Requires a local Git repository, an implementation plan file, and Claude Code or Codex as the orchestrator host. Implementer CLIs are optional and resolved at runtime.
metadata:
  version: "4.0.0"
  updated_at: "2026-09-19"
---

# SDDx

Use installed Superpowers `subagent-driven-development` for the workflow.
SDDx overrides implementer dispatch, reviewer model/effort selection, worker
evidence checks, and plan-scope authorization below. Keep the remaining SDD
workflow unchanged.

<HARD-GATE>
Do not copy Superpowers SDD into this skill.
Do not edit Superpowers files.
Do not implement in the orchestrator session.
Activate only when the user message contains /sddx or $sddx.
Do not activate on native SDD, executing-plans (including Native inline),
writing-plans, pre-sdd-review, or any request that does not contain
/sddx or $sddx.
Violating the letter of this gate is violating the spirit.
</HARD-GATE>

The only invocation is `$sddx` on Codex and `/sddx` on Claude Code.

## Arguments

    sddx <plan-file> [cursor|grok|c|g]

A file link or a plain-language reference to the same plan carries the same
meaning as the path argument. Read it as the plan path; do not build a
separate parser for it.

A plan together with its spec, ADR, and reference documents is one plan. Keep
one active plan and one ledger at a time. If a parent program plan states an
order, follow it. If the user gave an order for independent plans, run them in
turn and record the next plan's link in the current-state block. Never merge
sub-plan conditions into one run, and never guess an order from file names or
dates.

Ask once, and only when one of these holds:

- The plan path is absent or invalid.
- The order of independent plans is unclear.
- A parallel task's owned files or interfaces collide.

Nothing else about the input needs a question. Do not stop on a path you can
still resolve by asking for it once.

## Plan scope

The plan's task list is the authorized scope. Work the run discovers is
outside it: a fix the plan never named, a sub-task split out of one it did,
harness repair, instrumentation, a measurement rerun.

Ask once before dispatching the first task the plan does not name. Name what
it is, why the plan does not cover it, and what it displaces. One answer
authorizes that line of work, not every task after it; ask again when a new
line of work starts. Record the answer in the current-state block as
`Authorized scope:`, and mark each such task `UNPLANNED` in its ledger
History line so the run's own share of unplanned work stays readable.

A standing instruction to run to the end without stopping covers the plan's
tasks. It does not answer this question, because the question is about work
that did not exist when the instruction was given.

`c` means `cursor`. `g` means `grok`. Decide the backend in this order:

1. An explicit choice in this request.
2. The current state of this same run.
3. Ask once.

An explicit choice needs no re-approval on later tasks. If one message gives
two different explicit choices, confirm which one to use.

- Claude Code: AskUserQuestion. Options are Grok CLI — Grok selects the
  model. Do not pass `--model`. Requested effort goes on
  `--reasoning-effort` or `--effort` — and Cursor Agent (Grok) — the
  confirmed Grok model id whose final segment matches this task's effort.
- Codex: the available question tool, otherwise a short text question with
  numbered options; wait for one answer.

If only one backend is available, show that fact and the missing backend
`reason`, then still confirm before proceeding, unless this request already
made an explicit choice. Do not auto-select the only CLI.

Run `python3 "<skill-root>/scripts/resolve_backend.py" --backend <id> --json`
from the loaded skill root. If `available` is false for the requested
backend, stop and report `reason`. Do not automatically switch backends.
If both backends are unavailable, stop as BLOCKED.

Record `Backend: cursor|grok — <why it was chosen>` in the current-state block
of the Superpowers SDD ledger for this plan, and keep that backend until the
user directs a change. On a user-directed change, confirm the previous run
exited and that any Grok cleanup finished, then start the next attempt on the
new backend. Never pass the previous provider's session ID to the new backend.
Carry over the task, the fix-round count, open findings, and the approved
scope; a backend change does not reset the fix-round count.

On resume, check the current-state block against the real Git HEAD, the
uncommitted changes, and the recorded attempt's run state before acting. An
older `Backend:` line further down the ledger is history, not a current fact.

## Current state

One place holds the current state: the Superpowers SDD ledger for this plan.
Its first line stays exactly where SDD wrote it:

    # SDD ledger — plan: <plan file path>

Directly beneath it, keep one block delimited by
`<!-- sddx:current:start -->` and `<!-- sddx:current:end -->`, and replace the
block's contents on each update. The plan identifier stays outside the block.
Existing `Task <ID>: complete` lines and the fix-round history below the block
stay untouched, and new history is appended there once as usual. Update the
block by editing the ledger the way SDD already edits it: no separate state
writer, no database.

`references/current-state.md` holds the block template and its fields. Keep
the block at about thirty lines. Link a long open item to its detail, but
never drop it from the block.

Rewrite the block before each dispatch, and again when a task completes, a fix
round opens or closes, a ruling changes the run, or the user changes the scope.
Every field describes the run as it is now; a field that no longer matches the
evidence on disk — the attempt directory, the review lines below the block, the
Git HEAD — is a defect, and fixing it comes before the next dispatch. History
belongs below the block, never inside it: a superseded value is replaced, not
appended.

Do not create `controller-current-state.md`, `controller-recovery.md`, or any
other parallel state file. `run.json` owns one attempt's process facts; the
ledger owns user approval, task completion, review, and the next plan. Do not
sync the two in both directions.

The session that received `/sddx` or `$sddx` is the orchestrator. Use that
session's model and effort. Do not switch to a cheaper model, a strongest
final model, or the implementer's model family. Record `Orchestrator:` in
the current-state block at the start of the run.

## Controller

The current session is the orchestrator.
Do not run Superpowers `task-brief` or `task-start`. Extract the task with
`extract_task.py` as `references/dispatch.md` describes.
Do not batch same-shape plan tasks into one worker. One heading, one worker,
one review-package range.
Do not dispatch a nested controller that runs subagent-driven-development
end to end.
Follow
subagent-driven-development for worktree, ledger,
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
Every brief carries the plan's run-wide constraints in full under a
`Global constraints` heading, fix rounds included, as `references/dispatch.md`
describes. The worker cannot read the plan: a constraint that is not in the
brief does not exist for it, and the review then reports it as a defect the
worker was never given a way to avoid.

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

Record how each review was actually dispatched, in the ledger. High is one
line, `Task N review: sddx default — high`. XHigh must name a trigger and a
referent, `Task N review: sddx-reviewer-xhigh — <trigger>: <path or brief
phrase>`. A trigger you cannot tie to a path is not a trigger; use High.
The model is not part of these lines; it is always the orchestrator's. Never
record an agent name or an applied effort that you did not confirm was used.

Record the review host, model, and effort confirmation once in the
current-state block, together with its limits, and update it only when it
changes. That includes a host that cannot confirm the model ID.

When the native reviewer host cannot be reached — a rate limit, an exhausted
quota, a host that will not spawn — reviews do not silently move. Work the
order:

1. Wait for the blocking condition to clear and re-dispatch natively. A limit
   that resets is a wait, not a reason to change reviewers.
2. Use another native path the orchestrator host offers, still at the
   orchestrator's model.
3. Stop and ask. Name the limit, what is waiting on it, and what an external
   reviewer would cost.

Only the user's answer moves a review off the native host. The implementer's
own model family is the last choice even then: a reviewer drawn from it reviews
its own work, which is the independence this section exists to keep. Record the
new host, its model, and the reason in the current-state block, and name it on
every review line it produced, so a later reader can tell which verdicts came
from which reviewer without reconstructing the run.

This section's effort escalation needs the definition to be present. It is
absent on Codex, and on Claude Code it can be absent if the definition did not
load. Record that constraint once for the run in the current-state block, then
continue at the plain dispatch without repeating the report on later
dispatches, and do not substitute another model or effort. If the inherited
session effort is already XHigh or above, the plain dispatch already satisfies
the requirement and there is no missing definition to report at all. Do not
create the definition. A missing definition never blocks the run.

## Implementer

Choose implementer effort per task from the brief and the owned files,
before dispatch. Do not ask the user per task. Do not copy the session
effort onto the implementer. Reviewer XHigh does not force implementer
XHigh, and the reverse is not a trigger either.

| Implementation | Effort |
| --- | --- |
| Clear local or mechanical change, straightforward integration | High |
| Changes to concurrency, races, locking, ordering, or shared state; auth, permission, secret, or sandbox boundaries; tangled side effects across subsystems; High already failed review on this task | XHigh |

Architecture ambiguity is a ruling, not XHigh. File count, line count,
"this is important", and "to be safe" are not triggers. Record
`Task N worker-effort: high|xhigh — <reason>` in the ledger and
`Worker effort:` in the current-state block. A reason you cannot name
is High.

Fresh worker per task. Resume the same worker session for fix rounds 1-3
only when the requested effort is unchanged. When implementer effort
increases, dispatch a fresh worker. Rounds 4-5 use a fresh worker at
XHigh.

If the worker returns NEEDS_CONTEXT or BLOCKED, rule and re-dispatch.
Record `Task N worker-session: <id>` in the ledger and keep the confirmed
session ID in the current-state block.

Write `--attempt-dir` under the plan directory from Superpowers
`sdd-workspace`, never a shared flat `.superpowers/` name.

Launch every attempt with `python3 "<skill-root>/scripts/run_worker.py" run`
as `references/dispatch.md` describes. Do not hand-compose a provider command,
and do not write a new execution script for a run. Read a running or finished
attempt only through `run_worker.py status`, which answers with metadata,
`pid_alive`, a bounded tools index, and optional log windows; never dump a
whole worker log into this session. Copy `session_id` from that status — it
is filled while `state` is still `running`. `stale` is true when the record
says `running` and the process is gone; that record is not a live worker.

A stale attempt can still be resumable. When `session_id` is null because the
runner was killed before it could record one, `session_id_in_log` carries the
session the worker itself reported. Resume from it rather than re-running the
task from scratch; a null there means nothing was reported and the fallback to
a fresh attempt applies.

There is no automatic retry anywhere in these helpers. `run.json.state` is
process state, not task state, and process exit 0 is not a clean DONE.

Do not pass `--worktree` to the worker. The worker cwd is the current
Superpowers worktree.

Do not copy host credentials or environment values into the worker prompt
or `--prompt-file`. If the worker needs a host-outside side effect (push,
publish, shared-branch update), stop and return BLOCKED. Do not treat that
as review-passable DONE.

## Errors and host verification

A confirmed provider 402 balance exhaustion, or an auth or permission failure,
ends the attempt. Record in the current-state block the condition that must
change, and do not re-run under the same condition. A literal `402` in source
or test text is not a provider error. Do not blanket-retry a transient error
either: record cause, changed condition, and justification through the
existing SDD ruling procedure before another attempt.

The fix-round cap is unchanged. Neither a backend change nor more supplied
context resets it.

Split verification in the brief under two headings, `Worker checks` and
`Host checks`. The worker runs the Worker checks. An outstanding host check
comes back through the existing `NEEDS_CONTEXT` or `BLOCKED` status with the
items named; there is no new worker status for it. When the host can fill in
the result and no code change is needed, run the host check here and do not
call the worker again for the same reason.

A report-only correction is an evidence correction. It does not require a code
change, a new commit, or a full re-review. A recorded role violation stays
recorded; a later apology or a later success does not erase it.

Reuse an existing verification only when the relevant source, tests, and
environment are unchanged. Do not build a separate receipt system for it.

## Hosts

| Item | Claude Code | Codex |
| --- | --- | --- |
| Invocation | `/sddx` | `$sddx` |
| Asking for a backend | AskUserQuestion where available | the available question tool, else a short text question |
| Extraction, worker launch, status query | the same product Python scripts | the same product Python scripts |
| Review | native Task, no `model` argument, inherited | native `spawn_agent`, inherited model |
| XHigh | inherited if already satisfied, else the installed definition | inherited if already satisfied, else only what the host really provides |
| No escalation mechanism | record the constraint once, then the existing fallback | record the constraint once, then the existing fallback |

A change to the shared product source applies to new runs on both hosts.
Verify that the real load path points at this product; do not silently fix a
stale copy somewhere else. An already-running context is not updated
automatically: apply the change to new runs, and resume an existing run
explicitly after checking its ledger record and its processes. The supported OS is macOS. Do not add Windows transport. Refuse Windows at the product CLIs.

## Red flags

- Activating without `/sddx` or `$sddx` in the user message
- Running Superpowers `task-brief` or `task-start` during sddx
- Batching same-shape plan tasks into one worker
- Dispatching a nested controller that runs subagent-driven-development end to end
- Switching the orchestrator model or effort away from this session
- Copying the session effort onto the implementer
- Implementer XHigh to be safe, or because the reviewer ran XHigh
- Asking implementer effort on every task
- Resuming a High worker after effort increased to XHigh
- Passing `--model` to Grok to pin grok-4.6
- Native implementer subagent
- Copying SDD into this file
- Asking for a backend on every task
- Stopping on a missing plan path instead of asking once
- Dispatching a task the plan does not name without asking once
- Reading a standing "do not stop" as authority for unplanned work
- Re-running a task whose `session_id_in_log` was still resumable
- A brief without the plan's run-wide constraints
- Moving a review off the native host without asking
- A reviewer from the implementer's own model family
- A current-state field the evidence on disk contradicts
- Two active plans, or a second ledger
- Guessing a plan order from file names or dates
- Raising effort because the design is unclear
- Treating PATH `agent` as Cursor
- Auto-failover when Cursor is missing
- Auto-selecting the only available backend without confirmation
- Passing the previous provider's session ID to a new backend
- Resetting the fix-round count after a backend change
- A second current-state file beside the ledger block
- Hand-composing a provider command, or a new execution script per run
- Dumping a whole worker log into this session
- Re-querying the same status offset in a short loop
- Retrying after a confirmed 402 without a changed condition
- Calling the worker again for a host-only check
- Repeating the missing-definition report on later dispatches
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
