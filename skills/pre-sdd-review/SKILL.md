---
name: pre-sdd-review
description: Use when an approved design spec and implementation plan already exist and must be reviewed, automatically improved, and re-reviewed against repository reality immediately before SDD. Do not use for creating specs or plans, reviewing code, implementing changes, proofreading, or release readiness.
license: Apache-2.0
compatibility: Requires a local Git repository, readable design and plan files, and Codex subagent support for independent review.
metadata:
  version: "5.0.0"
  updated_at: "2026-09-19"
---

# Pre-SDD Review

Review an approved design and its implementation plan against each other and
repository reality before SDD. This is a readiness gate: repository reality is
evidence about feasibility and blast radius, never authority to replace an
approved product decision.

## Hard gate

Use this skill only when an approved design specification and implementation
plan exist, implementation has not started (or the user explicitly requests a
document reset before resuming), and the purpose is readiness review before
SDD or plan execution. Explicit `$pre-sdd-review` invocation is preferred;
implicit activation requires that purpose to be unambiguous.

Do not activate for writing an initial design or plan, code or pull-request
review, release verification, proofreading, or general documentation
improvement.

## Resolve authoritative inputs

One verdict-bearing invocation reviews exactly one implementation plan.
Resolve the design path from that plan's `**Spec:**` field, then read its
binding references: accepted ADRs, other explicit decision records, and any
user-approved visual or product authority. Also resolve the repository root.
If the plan has no resolvable `**Spec:**` path, do not guess among nearby
files: return `BLOCKED`.

If the input is ambiguous between multiple plans, ask for one exact plan when
the user is available; otherwise return `BLOCKED` instead of inventing an
aggregate verdict. A request naming several plans is split into separate
verdict-bearing invocations, but each verdict remains plan-local. Before the
first of those invocations, run the pre-pass below once. That pre-pass freezes
document hashes as H0 and Git HEAD as H_git0. Discoveries of different plans
may overlap. Repairs do not overlap. Do not emit an aggregate `READY`. A
preceding plan's repair that changes a shared design marks every dependent
plan dirty in this campaign; do not open a new campaign for that
invalidation.

Interpret conflicts in this order:

1. User-approved direction and referenced visual authority.
2. Accepted ADRs and other explicitly binding decision records.
3. The approved design specification.
4. The implementation plan.
5. Repository reality at this plan's turn.

A plan's turn is the repository plus every preceding plan in the fixed order,
not whatever `HEAD` happens to be. When preceding plans exist, that baseline
exists nowhere on disk and must be reconstructed from them.

When repository evidence conflicts with an approved product decision, preserve
the conflict. Never silently narrow, replace, or invent product intent.

If the plan explicitly identifies a required implementation base branch, ref,
or commit, resolve it before dispatching any reviewer. Verify the current
checkout with `git merge-base --is-ancestor <required-base> HEAD`. If the base
does not resolve or is not an ancestor of `HEAD`, preserve the mismatch and
return `BLOCKED`; do not review or repair against a different checkout.

## Pre-pass: shared-file ledger

Run this once, before the first verdict-bearing invocation, when the outer
request names two or more plans or asks for it explicitly. It emits no verdict.

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
no intake repair. Report confirmed candidates as findings only.

This pre-pass is not a recorded run. The recorder binds one run to one plan and
to a verdict, and this pass has neither. The ledger reaches evidence through
each plan's own `start`.

## Capture freshness

Before review, compute and record the repository-relative design and plan
paths and their SHA-256 hashes; Git `HEAD` (or `unborn`); and whether the
worktree is clean or dirty. Record the review timestamp and final verdict in
the final report. Also record the baseline: `HEAD` alone when no plan
precedes this one, or `HEAD` with the ordered list of preceding plans when
they do. Record the ledger's repository-relative path and SHA-256 when a
ledger exists.

Any content change to the resolved design or plan invalidates an earlier
`READY` verdict. A Git change elsewhere requires a new review when it changes
a path, command, interface, or blast-radius claim used as review evidence.

When preceding plans exist, carry that list and their paths in the reviewer
instruction and require a baseline-reconstruction statement on the response's
first line. That statement is the reviewer's own report and is not machine
checked. Its value is making the baseline explicit so the reviewer does not
quietly fall back to `HEAD`; it does not prove the reconstruction happened.

The pre-pass records H_git0 with H0. If HEAD moves off H_git0 before verdicts,
do not return READY against that freeze. Abandon in-flight runs with
`input-changed`. A new freeze needs an outer request. Do not narrow
`head_changed_during_review` to files the plan named.

## Optional local evidence

Run `python3 "<skill-root>/evidence/evidence.py" --version` from the actual
loaded skill root without installing anything. Parse its canonical JSON and
record only when `skill_name=pre-sdd-review` and `schema=4`. When compatible,
run `summary --repo <repo display name>` before `start` and locate this plan in
`runs` and `chains`. Close any `pending` run for this plan before anything
else: a pending run can outlive the invocation that opened it and be mistaken
for a new round. If the latest completed verdict for that plan is `REVISE` or
`BLOCKED`, `show` that run. Never reuse a handoff whose `execution` is
`blocked` or `degraded`: a `blocked` run dispatched no reviewer, so re-run the
input gates (`**Spec:**` resolution and the required implementation base) and
call `start` if they pass; a `degraded` run's handoff is never reusable, so
call `start` for a fresh full review. For a `full` run, reuse the prior handoff
without a new review only when `plan.sha_end` and `design.sha_end` match the
current documents, `git.head_end` matches the current `HEAD`, and the outer
request does not ask for a re-review or name changed authority or repository
evidence. Otherwise call `start` before semantic review with the skill root,
the repository, the primary plan, the design path resolved from the plan's
`**Spec:**` field, the host client id, the host-reported model string (or
`unknown`), and the mode.
If `**Spec:**` cannot be resolved, omit `--design` and return `BLOCKED`; the
recorder does not parse `**Spec:**`. Keep the returned `run_id`
controller-local and out of user documents. The same lifecycle applies to
default and `review-only` mode.

After the verdict and any repairs are final, call `finish` once with the
current repository locator and the review facts on stdin, then print exactly
one `Evidence:` line: `Evidence: recorded; run_id=<run-id>` or
`Evidence: not_recorded; reason=<code>`. An unavailable, malformed,
incompatible, or permission-failing recorder must continue the review and
never changes the semantic verdict. If the invocation ends before `finish`,
call `abandon` with one of `user-cancelled`, `input-changed`, `scope-changed`,
`input-format-fixed`, or `other`; never leave a run pending. If the same `repo`
display name and plan path are `pending`, close that run with `other` or
`input-changed` before a new `start`.

A schema 2 pending run is `historical-unbound` and read-only. Preserve it and
start a new run if recording is still wanted; never infer a checkout identity
for a historical record. A schema 3 pending run is not writable either, but it
accepts `abandon` so an in-flight run survives the upgrade.

Recording an `outcome` is not a controller duty. After SDD or implementation
ends, the user or the SDD worker may record one label (`good`, `false-ready`,
`noisy`, `abandoned`) for the run. Never store a full reviewer response or
source body in evidence; use bounded paraphrases only.

A finding record carries `id`, `severity`, `class`, `pattern`, `status`,
`source`, `repair_pass`, `location` (`path`, `locator`), `evidence`,
`consequence`, and `fix`. `evidence` is a list of repository-relative paths,
not prose. Pass the ledger path with `--ledger` and each preceding plan with a
repeated `--prior-plan` on `start`.

## Select reviewers

Dispatch one fresh, independent, read-only reviewer using the
[reviewer protocol](references/reviewer-protocol.md). A second fresh reviewer
is conditional, not routine: dispatch one focused reviewer only for framework
or runtime removal; schema migration or data deletion; authentication,
authorization, or security boundaries; public/private data-boundary changes;
or external side effects such as publishing, billing, messaging, or production
mutations. It examines only the triggered risk class.

The controller deduplicates all findings by evidence and consequence before
repair. Reviewers never edit files.

If a reviewer returns a summary, or a record missing any PSDR field, ask that
reviewer once for the complete records, naming only the missing fields. Do not
name suspected findings, paths, symbols, or fixes in that request. Never
accept a summary as findings.

Across the entire invocation, use at most two review roles: one primary role
and, when triggered, one focused risk role. A fresh re-review may replace the
agent in either role, but it does not add a review role or broaden the
triggered risk class. Evidence `reviewer_count` records these logical roles,
not cumulative fresh agent calls. If a fresh independent primary reviewer
cannot be obtained, return `BLOCKED`. If the host can supply only k fresh
agents, run discovery in waves of k. Do not reuse an agent across plans to
fill a wave. Do not use the controlling agent as a
substitute independent primary and do not run a short degraded round in its
place. When only the focused risk role cannot be obtained, the run is
`execution=degraded`; its handoff is never reusable. Never reuse one agent
across invocations that review different plans: that is not reuse, it is loss
of independence. Evidence `reviewers` counts distinct agents obtained for the
logical roles, not intended roles. A reused role is `execution=degraded`.

## Default mode: review -> repair documents -> scoped re-review

One invocation has one discovery stage, at most two repair passes, and a
terminal scoped closure. The default controller state machine is:

```text
resolve plan -> resolve plan **Spec:** -> read binding references
-> verify required implementation base -> hash design and plan
-> record HEAD and dirty state
-> fresh read-only review -> controller deduplication
-> authority-preserving document repair -> original closure review
-> conditional bounded repair-impact regression -> optional second repair
-> fresh original closure review + conditional bounded repair-impact regression
-> READY | REVISE | BLOCKED
```

When the outer request names two or more plans, after the pre-pass:

1. Discovery in host-sized waves of fresh agents. No verdict.
2. Serial repair in execution order. Update dirty from each delta.
3. Closure only for repaired or dirty plans, in parallel up to the host cap.
4. At most one more serial repair + closure per plan. Then plan-local verdicts.

Dirty is controller-local campaign state, not a record field and not worktree
dirty. After repairing plan i, Δ is the union of changed resolved design,
plan, and ledger fingerprints; repair-impact map symbols, paths, commands,
and consumers; and paths cited by repaired findings. Plan j is dirty when i
precedes j and either Δ intersects j's read set or a shared design j depends
on changed. j's read set is the resolved design, plan, and ledger paths and
hashes, `Files:` paths, preceding-plan paths, and discovery-record `evidence`
paths. Paths not in `Files:` are not in this dirty set; those holes are
machine-checked.

Discoveries of different plans may overlap.

After the first review, repair only findings that have an
authority-preserving document correction. If the first review has zero findings and the plan is not dirty, skip repair and closure
and return `READY` unless that plan is dirty. A dirty plan still takes scoped closure.
`repair_passes` counts only passes that produced at least one `repaired` finding.
A repair consumes no pass when both hold: the `repair-impact map` is empty
because no structural trigger fired, and the closure reviewer confirmed the
repair has no consumer. The controller's own confirmation does not count.
Because the second condition is the closure reviewer's, pass accounting settles
after that round's closure review, never at the moment of repair. Record such a
repair with `repair_pass: 0`. Group them into one pass.

Closure disposition is `closed`, `partially-closed`, or `open`, recorded as
`repaired`, `partially-closed`, and `unresolved` respectively. Record the
remainder of a partial closure as the original record's remaining sites, never
as a new ID, so repair passes track defects rather than the sites a defect is
scattered across. A finding still `partially-closed` at the end counts as
unresolved for the verdict and forces `REVISE`. A record's `repair_pass` is the
pass that last changed its status.

A new invocation does not copy a previous finding's `repair_pass`. Unresolved
handoff findings use `repair_pass` null.

If a repair changes a schema, type, interface, state transition, conditional
mutation surface, cross-task producer/consumer contract, verification meaning,
or public/private boundary, create a compact `repair-impact map` before
re-review. Record the modified claim; changed symbol, state, path, or command;
direct consumers and adjacent task interfaces; and each disposition as
`modify`, `verified-no-change`, or `unresolved`. Include one plausible
verification counterexample. Ordinary scalar corrections that trigger none of
these conditions do not require the map.

The closure instruction must include the repair diff of the resolved design,
plan, and ledger, even when the repair-impact map is empty.
Give a fresh reviewer the final repaired documents, original findings, and any
repair-impact map. It first checks original finding closure, then performs a
bounded repair-impact regression over the mapped consumers and adjacent
interfaces. This is not a new full review.

During scoped re-review, a material finding is eligible for the current repair
only when its source is an original finding or a direct mapped repair impact.
Keep an unmapped material finding visible, but do not widen the current repair.
A finding whose `class` and pattern match an original record is not unmapped,
even at a different location. It shows the original record's Location was
incomplete: widen that Location and repair it inside the same pass. Only a new
defect shape is unmapped.
End the invocation, include it in the unresolved handoff, and apply the existing
verdict rules: `BLOCKED` when new authority, input, or repository evidence is
required; otherwise `REVISE`.

An optional second repair is allowed only when that re-review finds another
eligible repairable material defect. Before it, deduplicate remaining findings,
complete any triggered impact map, and confirm that the repair hides no
unresolved authority choice. Then run one final fresh closure and repair-impact
re-review. At most two repair passes are permitted. If a material issue remains,
return `REVISE` with its evidence; do not downgrade it to finish the loop.

## Review-only mode

`review-only` is explicit. Make no file changes, use the same fresh read-only
review and controller deduplication, and return the first review's verdict.

Named multi-plan `review-only` may overlap discoveries. It still makes no
file changes and returns each plan's first-review verdict. There is no
repair epoch and no dirty set.

## Repair rules

The controlling agent may edit only the resolved design specification, the
resolved implementation plan, and the resolved shared-file ledger. Ordinary
evidence-backed corrections within that closed document boundary do not
require an approval checkpoint.

Any correction that changes approved product intent is forbidden and returns
`BLOCKED`. The mutation allowlist excludes accepted ADRs, approved visual authority,
application code, tests, configuration, generated artifacts, and unrelated documentation.
Do not introduce a new feature, dependency, host claim, or product decision while
repairing documents.

Authority-preserving repairs require no user checkpoint. When one or more
unresolved items require user authority, return one consolidated user
checkpoint with the exact decisions needed; do not split them into repeated
approval requests.

### Machine checks

Run these in the pre-pass over every plan at once, and again over the
repaired documents before dispatching the closure reviewer, attaching the
second run's results to the `repair-impact map`.

1. A declared count against the counted one: a task's stated passing count
   against its actual tests, a closed list's stated membership against its
   members.
2. The argument count and order at every site that builds the same constructor.
3. A literal against the constraint that receives it: length, range, enum.
4. An identifier embedded in a number or a name, at every site that carries it:
   a migration file's number against the number in the test that checks it.
5. Every face of a closed list, updated together: schema enums, exact-match key
   arrays, tests that count members.
6. Every backticked repository path in the plan exists at that plan's turn.
   Exclude paths any plan in the chain lists under `Create:`. Excluding only
   the current plan's `Create:` yields false positives.

These emit candidates. A candidate is not a defect until the repository
confirms it. Raising an unconfirmed candidate makes the gate spend a round trip
on a defect that is not there.

## Verdict and handoff

Return `READY` only when no unresolved finding requires invention or permits a
materially wrong implementation to pass the planned evidence. Return `REVISE`
for a material repairable document defect, including one still material after
the second pass. Return `BLOCKED` when required authority, input, or
repository evidence is unavailable, unresolvable, or would require a new
product decision, or when an independent primary reviewer cannot be obtained.
Record that run as `execution=blocked` and name the cause in `block_reason`; a
`BLOCKED` run with a null `block_reason` is an anomaly.

For final `REVISE` or `BLOCKED`, include an `unresolved handoff packet`: the
unresolved finding, why it escaped an earlier pass when known, the bounded
next document scope, whether new authority or evidence is required, and the
next invocation scope. New authority implies `BLOCKED`, never `REVISE`. This
packet does not authorize a third repair or certify its suggested scope as
complete.

Do not automatically start another invocation after `REVISE` or `BLOCKED`.
A later invocation requires an explicit outer request or changed document,
authority, or repository evidence. When none changed, reuse the prior handoff
instead of repeating the same review, subject to the reuse rule above: never
for an `execution=blocked` or `degraded` run, and for a `full` run only when
the documents, `HEAD`, and the request are all unchanged.

Include a compact pass receipt in the final report: input and final document
hashes, pass number, finding IDs/classes, triggered repair-impact categories,
changed document hashes, and verdict. Do not persist user documents or full
model responses merely to create the receipt.

For `READY`, print the exact resolved design and plan paths and their final
fingerprints, together with the freshness record. Print the `anomalies` list
that `finish` returned for this run as `Anomalies: <names>`, or
`Anomalies: none` when it is empty. When the recorder was not used or
`finish` failed, print `Anomalies: not_recorded`. Do not look this run up in
a windowed `summary`. Anomalies do not change the verdict. Do not start SDD unless the outer request explicitly asks for implementation. In that combined request,
hand the SDD worker the final repaired documents, not the pre-review copies.

## Do not use this skill for

Do not use this skill to create designs or plans, implement or edit application
code, review a source diff, perform release readiness or security review,
proofread, publish a release, or make an accepted product decision.

## Red flags

- Resume a reviewer by naming findings, paths, symbols, or fixes
- Start a new review when documents, `HEAD`, and the request are all unchanged since a `full` REVISE or BLOCKED run
- Reuse a handoff from an `execution=blocked` run, or reuse any handoff on document hashes alone
- Dispatch a second reviewer, or record `reviewers: 2`, with no risk trigger
- Return or accept a finding summary instead of complete PSDR records
- Print `READY` without the `Anomalies:` line from `finish`
- Commit before `finish`
- Cite `repo-reality` with only the reviewed design or plan paths
- Put source text in an evidence paraphrase
- Claim that a test covers something without locating that test
- Apply a textual repair without asserting the match is unique
- Reuse one reviewer across invocations that review different plans
- Reuse a handoff from a `degraded` run
- Overlap repairs of two plans on one host
- Reuse a reviewer to fill a discovery wave
- Print READY after HEAD moved from the freeze
- Skip closure for a dirty plan with zero discovery findings
