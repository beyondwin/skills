---
name: sddx
description: Use when the user runs /sddx or $sddx. Do not use for writing a spec or plan, writing-plans, executing-plans including Native inline execution, pre-sdd-review, /waygent, native subagent-driven-development, or any request that does not contain /sddx or $sddx.
license: Apache-2.0
compatibility: Requires a local Git repository, an implementation plan file, the waygent skill installed next to this one, and Claude Code or Codex as the orchestrator host. Implementer CLIs are optional and resolved at runtime.
metadata:
  version: "8.0.0"
  updated_at: "2026-09-30"
---

# SDDx

SDDx is waygent with an outside coder. Follow the installed waygent skill at
`<skill-root>/../waygent/SKILL.md` as the base loop: branch, `.waygent/<plan-slug>/`
state, `guide.md`, one task at a time, test first, the `Waygent-Task: N` trailer,
one review and one fix per task, one final review, failure retry, resume, and the
report. This file changes only who writes the code and what gets checked and
recorded. Where this file says something different, this file wins.

<HARD-GATE>
Do not copy waygent into this skill.
Do not edit waygent files during a run.
Do not implement in the orchestrator session.
Activate only when the user message contains /sddx or $sddx.
Do not activate on /waygent, native SDD, executing-plans (including Native
inline), writing-plans, pre-sdd-review, or any request that does not contain
/sddx or $sddx.
Violating the letter of this gate is violating the spirit.
</HARD-GATE>

waygent's own "run only with /waygent" and "not for /sddx" lines are about
activation. They do not stop you from reading it here. If
`<skill-root>/../waygent/SKILL.md` is missing, stop as BLOCKED and say so.

## Arguments

    sddx <plan-file> [cursor|grok|c|g]

A file link or a plain-language reference to the plan is the plan path. `/sddx`
alone resumes the one folder under `.waygent/` whose `progress.md` has the SDDx
block. SDDx always needs a plan file: waygent's no-plan mode is not used here.
Keep one active plan at a time. Follow an order a parent plan states; never
guess one from file names or dates.

Ask once, and only when the plan path is absent or invalid, or the order of
independent plans is unclear. Everything else: decide and record the ruling.

## Plan scope

The plan's task list is the authorized scope. Ask once before dispatching the
first task the plan does not name (a fix the plan never named, harness repair,
a measurement rerun): name it, why the plan does not cover it, and what it
displaces. Record the answer as `Authorized scope:` and mark each such task
`UNPLANNED` in its progress line. A standing "run to the end" covers the plan's
tasks only.

## Backend

`c` means `cursor`. `g` means `grok`. Decide the backend in this order:

1. An explicit choice in this request.
2. The current state of this same run.
3. Ask once.

An explicit choice needs no re-approval on later tasks. If one message gives
two different explicit choices, confirm which one to use.

- Claude Code: AskUserQuestion. Options:
  - Grok CLI — pass `--model grok-4.7` from the resolver's `model_ids`.
    Do not pass `grok-4.6`, `grok-4.5`, or `grok-4.7-build-fast`.
  - Cursor Agent (Grok) — a `model_ids` entry whose version is 4.7, whose
    final segment matches this task's effort, and which does not
    end in `-fast`.
- Codex: the available question tool, else a short numbered question.

If only one backend is available, show that and the missing backend's
`reason`, then still confirm unless this request already chose. Do not
auto-select the only CLI. Run
`python3 "<skill-root>/scripts/resolve_backend.py" --backend <id> --json`. If
`available` is false, stop and report `reason`. Do not automatically switch
backends. Keep the backend until the user changes it; on a change, confirm the
old attempt exited, and never pass the previous provider's session ID.

## Who does what

| waygent step | SDDx |
| --- | --- |
| Implementer subagent | one outside worker attempt through `run_worker.py run` |
| The brief | `extract_task.py` output plus the waygent lines, per `references/dispatch.md` |
| "Same implementer" for a fix | `--resume <session_id>` at the same effort; else a fresh worker told what is already done |
| Retry one tier up | a fresh worker at XHigh (the worker model stays Grok 4.7) |
| Final-review fixes and the app walk | one worker attempt, one batch |
| Reviewers | native, as waygent's Models section says |

The worker cannot read the plan, so every brief carries the plan's run-wide
constraints: `extract_task.py --global-constraints` prepends them. A
constraint that is not in the brief does not exist for the worker.
`references/dispatch.md` holds the brief, launch, watch, and cleanup steps.
Launch only through `run_worker.py`; never hand-compose a provider command, and
never dump a whole worker log into this session. Never end your turn while a
worker runs: block on `run_worker.py wait`, and call it again on exit 3. Do not pass `--worktree` to the
worker.

## Implementer effort

Choose per task from the brief and the owned files. Do not ask the user per
task. Do not copy the session effort onto the implementer.

| Implementation | Effort |
| --- | --- |
| Clear local or mechanical change, straightforward integration | High |
| Changes to concurrency, races, locking, ordering, or shared state; auth, permission, secret, or sandbox boundaries; tangled side effects across subsystems | XHigh |

Architecture ambiguity is a ruling, not XHigh. File count, line count, and "to
be safe" are not triggers. When implementer effort increases, dispatch a fresh
worker.

## Checking a worker

Process exit 0 is not task completion. On top of waygent's check (trailer
commit, clean tree, fast check), read `report.md` and `run_worker.py status`
(the tools index), and record role compliance as PASS, FAIL, or UNVERIFIED.
A successful prohibited read (the plan, credentials, secrets) is FAIL even when
tests pass. Missing or incomplete tool evidence is UNVERIFIED, never PASS.
Neither permits a clean DONE. Give the reviewer the evidence and any
discrepancy with the worker report.

Filename-only listings inside the worktree and direct reads of repository
ignore/build/test configuration are allowed inspection, not scope deviations;
with no other deviation, `Scope deviations: none` is correct.

BLOCKED, NEEDS_CONTEXT, a missing report, or an unclear result is not DONE.
NEEDS_CONTEXT gets a ruling and a redispatch; it is not a failure. A report-only
correction needs no new commit. A later apology does not erase a recorded
violation.

Split each brief's checks into `Worker checks` and `Host checks`. Run a task's
Host checks before that task's review. When only the host can finish a check
and no code change is needed, run it here instead of calling the worker again.

## Timeouts and errors

Tell a stopped runner from a failed task. An attempt whose `state` is
`interrupted`, or whose record is `stale`, means the runner was stopped, not
that the worker failed. Resume its session (`session_id`, else
`session_id_in_log`) at the same effort, and record `task N: interrupted:`
rather than a failure; it does not use up waygent's one retry. With no session
ID, start a fresh worker told what is already done. A worker that exits by
itself, or is killed, with no trailer commit or a failed check is a task
failure: waygent's retry, a fresh worker at XHigh.

An attempt whose `error` is `the worker wrote no output for <N> seconds` hit
the idle timeout (`--idle-timeout`, default 900). Check the worktree for partial
changes, do not resume that session, and dispatch a fresh worker with a
continuation brief that names the previous `report.md` and the commits already
made. Grok writes nothing while it waits on a long command, and backgrounding
it does not keep an attempt alive; when a brief names a command expected to run
longer than the idle window, raise `--idle-timeout` above that command's
expected duration before launch.

A confirmed provider 402, or an auth or permission failure, ends the attempt:
record the condition that must change,
and do not re-run under the same condition. There is no automatic retry anywhere in these helpers. If the
worker needs a host-outside side effect (push, publish, shared-branch update),
stop and return BLOCKED. Do not copy host credentials or environment values
into a brief.

## Recording models

Record what actually ran, never what you meant to run. The session that
received `/sddx` or `$sddx` is the orchestrator; do not switch its model.

- Worker: `run.json` has `model` (requested), `reported_model` (what the
  worker's own stream said), and `configured_effort`.
- Native reviewer or orchestrator: `python3 "<skill-root>/scripts/observed_model.py"
  claude-code --agent-id <agentId>` (this session: `--session-id
  "$CLAUDE_CODE_SESSION_ID"`; Codex: `codex --thread-id <id>`) reads the
  host's own transcript. A session id taken from a file path is not yours.

Write them into waygent's progress lines:

    task N: done <sha7> impl=<backend>:<reported_model>/<effort> review=<clean|fixed K|skipped> reviewer=<model>/<effort> tests=<summary> role=<PASS|FAIL|UNVERIFIED>

Add `(requested)` after a value that no transcript or stream confirmed. The
`final:` line and retry lines carry `impl=` and `reviewer=` the same way.

## Current state

`progress.md` keeps waygent's lines. Directly under its header lines, keep one
block between `<!-- sddx:current:start -->` and `<!-- sddx:current:end -->`
and replace its contents before each dispatch and after each result.
`references/current-state.md` holds the template. A field that no longer
matches the evidence on disk (Git HEAD, the attempt directory) is a defect;
fix it before the next dispatch. Do not create any other state file.

## Hosts

| Item | Claude Code | Codex |
| --- | --- | --- |
| Invocation | `/sddx` | `$sddx` |
| Asking for a backend | AskUserQuestion | the question tool, else a short text question |
| Worker launch and status | the same product Python scripts | the same product Python scripts |
| Review | Agent tool, per waygent Models | `spawn_agent`, per waygent Models |

The supported OS is macOS. Do not add Windows transport. Refuse Windows at the product CLIs.

## Red flags

- Activating without `/sddx` or `$sddx`, or on `/waygent`
- Copying waygent into this file, or running without it
- A native implementer subagent, or the controller editing application code
- A brief without the plan's run-wide constraints, or the whole plan as a reference
- Hand-composing a provider command, or dumping a whole worker log
- Launching Grok CLI or Cursor Agent on any model other than Grok 4.7, or on a `-fast` variant
- Treating PATH `agent` as Cursor, or auto-failover when a backend is missing
- Auto-selecting the only available backend without confirmation
- Ending the turn while a worker runs
- Starting an attempt while the previous attempt's `pid_alive` is true, or stopping one with `pkill -f` or by signalling `run.json.pid` while its runner is alive
- Resuming a session whose attempt wrote no output
- Retrying after a confirmed 402 without a changed condition
- Implementer XHigh to be safe, or copying the session effort onto it
- A PASS without a tool trace, or a clean DONE after a prohibited read
- A model or effort in progress that nothing observed, without `(requested)`
- Worker git push, publish, or shared-branch update
