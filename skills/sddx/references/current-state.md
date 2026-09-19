# Current state block

The Superpowers SDD ledger for the active plan is the only place that holds
the current state. This file owns the block template and nothing else.

## Placement

The ledger's first line is the plan identifier SDD already wrote:

    # SDD ledger — plan: <plan file path>

Keep that line exactly where it is, outside the block. Directly beneath it,
keep one block delimited by `<!-- sddx:current:start -->` and
`<!-- sddx:current:end -->`. Replace the contents of that block on each
update; never add a second block, and never move the identifier inside it.
Everything below the block — `Task <ID>: complete` lines, fix-round history,
review lines, rulings — is history and stays untouched.

## Template

```markdown
# SDD ledger — plan: docs/plans/storage.md
<!-- sddx:current:start -->
## Current state
Plan: docs/plans/storage.md
Next plan: none
Backend: cursor — explicit user change
Worktree: /workspace/project; HEAD: abc1234
Task: P1; fix round: 2; attempt: worker-attempts/P1-fix2
Worker session: cursor-session-example
Orchestrator: codex; model: inherited-unknown; effort: xhigh
Worker effort: high — local rename
Review host: codex; model: inherited; effort: inherited xhigh
Open findings: P1-review.md#remaining
Authorized scope: local implementation and verification
Host checks pending: browser smoke
Next action: collect browser evidence before another worker call
Evidence: worker-attempts/P1-fix2/run.json
<!-- sddx:current:end -->
```

The values above are a synthetic example. Fill in the real plan path,
worktree, HEAD, attempt path, and session ID for this run.

## Fields

- `Plan` — the active plan file. Exactly one plan is active at a time.
- `Next plan` — the link to the next plan in a stated order, or `none`.
- `Backend` — `cursor` or `grok`, and why it was chosen (argument, current
  state, answered question, or explicit user change).
- `Worktree` and `HEAD` — the worktree path and the commit the state describes.
- `Task`, `fix round`, `attempt` — the task ID, the current fix-round count,
  and the attempt directory of the latest run.
- `Worker session` — the confirmed provider session ID from `status` /
  `run.json`, including while `state` is `running`, or `none`. `status`
  offers `session_id_in_log` when the record holds none; an ID confirmed that
  way is recordable. Never record an unconfirmed ID, and never carry one
  across a backend change.
- `Orchestrator` — this run's host, the session model id or
  `inherited-unknown`, and the session effort. Written at the start of
  the run and updated only when the session itself changes.
- `Worker effort` — `high` or `xhigh` for the current task, with the
  reason. Independent of `Orchestrator` effort.
- `Review host`, `model`, `effort` — how reviews are actually dispatched, with
  any host limit. Written once and updated only when it changes.
- `Open findings` — a link to unresolved review findings, or `none`.
- `Authorized scope` — what the user has approved for this run, including the
  answer to the plan-scope question for any task the plan does not name. A
  standing "run to the end" covers the plan's tasks only.
- `Host checks pending` — host-only verification the worker cannot run, or
  `none`.
- `Next action` — the single next step.
- `Evidence` — the link to the current attempt's evidence, usually its
  `run.json`.

Keep the whole block at about thirty lines. Link a long open item to its
detail file rather than inlining it, but never drop the item from the block.

## Reading it back

On resume, read this block first and check it against the real Git HEAD, the
uncommitted changes, and the recorded attempt's `run.json` state before
acting. A `Backend:` line or a review line further down the ledger is history
from an earlier round, not the current fact. The block is the current fact.

`run.json` holds one attempt's process facts. This block holds user approval,
task completion, review, and the next plan. Do not sync them in both
directions, and do not create a second state or recovery file.
