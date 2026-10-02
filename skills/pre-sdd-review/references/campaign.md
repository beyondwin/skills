# Campaign rules

A campaign is one outer request that names two or more plans. A single-plan
run skips this file. Every rule in `SKILL.md` still applies to each plan; this
file adds only what changes when several plans share one request.

## Split and order

A request naming several plans is split into separate verdict-bearing
invocations, each with its own plan-local verdict. Run the pre-pass below once
before the first of them. Discoveries of different plans may overlap. Repairs
do not overlap. Do not emit an aggregate `READY`. A repair that changes a
shared design marks every other plan that depends on it stale in this
campaign, before or after it in the order; do not open a new campaign for that
invalidation.

## Pre-pass: shared-file ledger

Run it once, before the first verdict-bearing invocation, when the outer
request names two or more plans or asks for it explicitly. It emits no
verdict.

1. Fix the execution order. Take it from the user or derive it from the plans'
   stated prerequisites. If it cannot be fixed, stop and ask: without an order
   there is no baseline.
2. Build the ledger. Scrape each plan's `Files:` backticked paths and invert
   them into one row per path. If a plan has no `Files:` section, stop and ask;
   never derive the paths from task edit surfaces.
3. Sweep the rows that two or more plans touch.
4. Run the machine checks over every plan at once.
5. Steps 3 and 4 emit candidates, not findings. A candidate becomes a defect
   only when the repository confirms it.
6. Record `HEAD` as the campaign freeze.

The controlling agent does all of this. Dispatch no reviewer: a reviewer here
would be a third review role outside any plan's invocation. The next
invocation's fresh discovery review is the independent check on these repairs.

Hand the confirmed candidates to the controller, never to a reviewer. Repair
them before dispatching any reviewer, so the reviewer still arrives told
nothing. Those repairs precede review, so they consume no repair pass; record
them with `repair_pass: 0` and `source` `ledger-pass` or `machine-check`.

The ledger is derived evidence, never authority. When it disagrees with a
plan's `Files:`, the plan wins and the ledger is rebuilt. Its default path is
`docs/superpowers/ledgers/YYYY-MM-DD-<campaign>.md`; a user preference wins.

Under `review-only`, keep the ledger controller-local, write no file, and make
no intake repair. Report confirmed candidates as findings; they count as
unresolved findings for the verdict.

This pre-pass is not a recorded run. The recorder binds one run to one plan and
to a verdict, and this pass has neither. The ledger reaches evidence through
each plan's own `start`.

## Discovery waves

If the host can supply only k fresh agents, run discovery in waves of k. Do
not reuse an agent across plans to fill a wave; that is loss of independence
(`agent-reused-across-plans`), not reuse. Do not bind a later `READY` to a
preceding plan.

## Campaign schedule

After the pre-pass:

1. Discovery in host-sized waves of fresh agents. Discoveries of different plans may overlap. No verdict.
2. Serial repair in execution order. Update stale plans from each delta.
3. Closure only for repaired or stale plans, in parallel up to the host cap.
4. At most one more serial repair + closure per plan, plus the residual pass. Then plan-local verdicts.

A preceding plan that is `BLOCKED` does not stop later discovery. Do not bind
a later `READY` to a preceding plan.

Stale is controller-local campaign state, not a record field and not the
worktree's dirty flag. After repairing plan i, Δ is the union of changed
resolved design, plan, and ledger fingerprints; repair-impact map symbols,
paths, commands, and consumers; and paths cited by repaired findings. Plan j
is stale when i precedes j and Δ intersects j's read set. Plan j is also
stale when a shared design j depends on changed, whichever of i and j comes
first: that design is j's authority, so the change voids j's earlier review.
j's read set is the resolved design, plan, and ledger paths and hashes,
`Files:` paths, preceding-plan paths, and discovery-record `evidence` paths.
A stale plan takes its scoped closure after the repair that made it stale and
before its verdict. A plan made stale after its last permitted closure returns
`REVISE`, and its handoff names the changed document.
Paths not in `Files:` are not in this stale set; those holes are machine-checked.

## Review-only

Campaign `review-only` may overlap discoveries. It still makes no file
changes and returns each plan's first-review verdict. There is no repair and
no stale set.
