---
name: pre-sdd-review
description: Use when an approved design spec and implementation plan already exist and must be reviewed, automatically improved, and re-reviewed against repository reality immediately before SDD. Do not use for creating specs or plans, reviewing code, implementing changes, proofreading, or release readiness.
license: Apache-2.0
compatibility: Requires a local Git repository, readable design and plan files, and Codex subagent support for independent review.
metadata:
  version: "1.2.0"
  updated_at: "2026-08-30"
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

One invocation reviews exactly one implementation plan. Resolve the design
path from that plan's `**Spec:**` field, then read its binding references:
accepted ADRs, other explicit decision records, and any user-approved visual
or product authority. Also resolve the repository root. If the plan has no
resolvable `**Spec:**` path, do not guess among nearby files: return `BLOCKED`.

If the input is ambiguous between multiple plans, ask for one exact plan when
the user is available; otherwise return `BLOCKED` instead of inventing an
aggregate verdict. A request naming several plans may be split into separate
invocations, but each verdict remains plan-local. Do not emit an aggregate
`READY`. If a later invocation changes a shared design, rerun every earlier
plan whose evidence depended on the previous design fingerprint.

Interpret conflicts in this order:

1. User-approved direction and referenced visual authority.
2. Accepted ADRs and other explicitly binding decision records.
3. The approved design specification.
4. The implementation plan.
5. Current repository reality.

When repository evidence conflicts with an approved product decision, preserve
the conflict. Never silently narrow, replace, or invent product intent.

## Capture freshness

Before review, compute and record the repository-relative design and plan
paths and their SHA-256 hashes; Git `HEAD` (or `unborn`); and whether the
worktree is clean or dirty. Record the review timestamp and final verdict in
the final report.

Any content change to the resolved design or plan invalidates an earlier
`READY` verdict. A Git change elsewhere requires a new review when it changes
a path, command, interface, or blast-radius claim used as review evidence.

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

## Default mode: review -> repair documents -> scoped re-review

The default controller state machine is:

```text
resolve plan -> resolve plan **Spec:** -> read binding references
-> hash design and plan -> record HEAD and dirty state
-> fresh read-only review -> controller deduplication
-> authority-preserving document repair -> original closure review
-> conditional bounded repair-impact regression -> optional second repair
-> fresh original closure review + conditional bounded repair-impact regression
-> READY | REVISE | BLOCKED
```

After the first review, repair only findings that have an
authority-preserving document correction.

If a repair changes a schema, type, interface, state transition, conditional
mutation surface, cross-task producer/consumer contract, verification meaning,
or public/private boundary, create a compact `repair-impact map` before
re-review. Record the modified claim; changed symbol, state, path, or command;
direct consumers and adjacent task interfaces; and each disposition as
`modify`, `verified-no-change`, or `unresolved`. Include one plausible
verification counterexample. Ordinary scalar corrections that trigger none of
these conditions do not require the map.

Give a fresh reviewer the final repaired documents, original findings, and any
repair-impact map. It first checks original finding closure, then performs a
bounded repair-impact regression over the mapped consumers and adjacent
interfaces. This is not a new full review.

An optional second repair is allowed only after that re-review finds another
repairable material defect. Before the final repair, deduplicate the remaining
findings, complete any triggered impact map, and confirm that no unresolved
authority choice is hidden in the repair. It must be followed by another fresh
closure and repair-impact re-review before the final verdict. At most two repair passes
are permitted. If a material issue remains after the second repair pass, return
`REVISE` with its evidence; do not downgrade it to finish the loop.

## Review-only mode

`review-only` is explicit. Make no file changes, use the same fresh read-only
review and controller deduplication, and return the first review's verdict.

## Repair rules

The controlling agent may edit only the resolved design specification and the
resolved implementation plan. Ordinary evidence-backed corrections within that
closed two-document boundary do not require an approval checkpoint.

Any correction that changes approved product intent is forbidden and returns
`BLOCKED`. The mutation allowlist excludes accepted ADRs, approved visual authority,
application code, tests, configuration, generated artifacts, and unrelated documentation.
Do not introduce a new feature, dependency, host claim, or product decision while
repairing documents.

## Verdict and handoff

Return `READY` only when no unresolved finding requires invention or permits a
materially wrong implementation to pass the planned evidence. Return `REVISE`
for a material repairable document defect, including one still material after
the second pass. Return `BLOCKED` when required authority, input, or
repository evidence is unavailable, unresolvable, or would require a new
product decision.

For final `REVISE` or `BLOCKED`, include an `unresolved handoff packet`: the
unresolved finding, why it escaped an earlier pass when known, the bounded
next document scope, whether new authority or evidence is required, and the
next invocation scope. New authority implies `BLOCKED`, never `REVISE`. This
packet does not authorize a third repair or certify its suggested scope as
complete.

Include a compact pass receipt in the final report: input and final document
hashes, pass number, finding IDs/classes, triggered repair-impact categories,
changed document hashes, and verdict. Do not persist user documents or full
model responses merely to create the receipt.

For `READY`, print the exact resolved design and plan paths and their final
fingerprints, together with the freshness record. Do not start SDD unless the outer request explicitly asks for implementation. In that combined request,
hand the SDD worker the final repaired documents, not the pre-review copies.

## Do not use this skill for

Do not use this skill to create designs or plans, implement or edit application
code, review a source diff, perform release readiness or security review,
proofread, publish a release, or make an accepted product decision.
