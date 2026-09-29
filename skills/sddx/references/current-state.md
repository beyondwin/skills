# Current state block

waygent's `progress.md` for the active plan is the only place that holds the
run's state. This file owns the SDDx block template and nothing else.

## Placement

`progress.md` opens with waygent's header lines (`plan:`, `branch:`, `start:`,
`model:`). Directly beneath them, keep one block delimited by
`<!-- sddx:current:start -->` and `<!-- sddx:current:end -->`. Replace the
contents of that block on each update; never add a second block. Everything
below it — waygent's `task N: ...` lines, `final:`, rulings — is history and
is appended as waygent says.

## Template

```markdown
plan: docs/plans/storage.md
branch: waygent/storage
start: 1a2b3c4
model: claude-opus-5-5/high
<!-- sddx:current:start -->
Backend: grok — argument
Orchestrator: claude-code; model: claude-opus-5-5; effort: high (observed)
Task: 3 of 5; step: fix; attempt: attempts/task-3-fix
Worker session: grok-session-example
Worker effort: high — local parser change
Open findings: reviews/task-3.md
Authorized scope: plan tasks only
Host checks pending: none
Next plan: none
Next action: wait for attempts/task-3-fix, then check as waygent step 3
<!-- sddx:current:end -->
task 1: start base=1a2b3c4
task 1: done 5d6e7f8 impl=grok:grok-4.7/high review=clean reviewer=claude-opus-5-5/high tests=12 passed role=PASS
```

The values above are a synthetic example. Fill in the real ones.

## Fields

- `Backend` — `cursor` or `grok`, and why (argument, current state, answered
  question, or explicit user change).
- `Orchestrator` — this session's host, model, and effort, read with
  `observed_model.py --session-id` where the host allows; otherwise the value
  you know, marked `(requested)` or `inherited-unknown`. Written at the start.
- `Task`, `step`, `attempt` — the task number, where it is (`implement`,
  `review`, `fix`, `retry`, `final`), and the latest attempt directory under
  `$P`.
- `Worker session` — the confirmed `session_id` from `status`, or `none`.
  Never an unconfirmed ID, and never one carried across a backend change.
- `Worker effort` — `high` or `xhigh` for the current attempt, with the reason.
- `Open findings` — a link to unresolved review findings, or `none`.
- `Authorized scope` — what the user approved, including any answer to the
  plan-scope question.
- `Host checks pending` — host-only checks still owed, or `none`.
- `Next plan` — the next plan in a stated order, or `none`.
- `Next action` — the single next step.

Keep the block under about fifteen lines. Link a long item to its file rather
than inlining it, but never drop it.

## Reading it back

On resume, follow waygent's resume rules first (Git trailers are the truth),
then check this block against Git HEAD, uncommitted changes, and the recorded
attempt's `run_worker.py status` before acting. Do not start an attempt while
the previous one's `pid_alive` is true. `run.json` holds one attempt's process
facts; this block holds the run's. Do not sync them both ways, and do not
create a second state file.
