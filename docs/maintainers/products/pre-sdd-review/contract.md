# pre-sdd-review contract

This document owns activation, authority, reviewer isolation, document repair,
findings, freshness, verdicts, and the SDD handoff for Pre-SDD Review.

## Activation and input resolution

Activate only when an approved design specification and implementation plan
exist and the request is a readiness review immediately before SDD or plan
execution. Do not activate for initial design or plan writing, source-diff
review, release readiness, proofreading, or general documentation work.

Resolve one implementation plan path first. Resolve the resolved design
specification from that plan's `**Spec:**` field, then its explicitly binding
references, the repository root, and current Git state. A missing or
unresolvable `**Spec:**` path is `BLOCKED`; never guess among nearby files.

## Authority order

Interpret conflicts in this order:

### Authority order

1. User-approved direction and referenced visual authority.
2. Accepted ADRs and other explicitly binding decision records.
3. The approved design specification.
4. The implementation plan.
5. Current repository reality.

Repository reality is feasibility and blast-radius evidence, not authority to
replace an approved product decision. If repair would need a new product
decision, preserve the conflict and return `BLOCKED`.

## Reviewer isolation and repair allowlist

The normal reviewer is fresh, independent, and read-only. It reports evidence
and the smallest authority-preserving correction; the controller owns all
repairs and does not let a reviewer mutate documents.

The bounded lists below are the sole mutation authority. Never add a feature,
dependency, host claim, or product decision while fixing the documents.

### Editable paths

1. resolved design specification.
2. resolved implementation plan.

### Excluded surfaces

- `accepted ADRs`
- `approved visual authority`
- `application code`
- `tests`
- `configuration`
- `generated artifacts`
- `unrelated documentation`

## Review passes and findings

The protocol has five passes:

### Review passes

1. authority trace;
2. repository grounding;
3. cross-artifact consistency;
4. verification falsification;
5. readiness verdict.

Use only two severities: `BLOCKER` and `IMPORTANT`. Use only five finding
classes: `authority-drift`, `repo-reality`, `coverage`, `ordering`, and
`verification-gap`. A finding records its ID, severity, class, exact document
location, evidence, concrete consequence, and smallest document fix. Zero
findings is valid.

### Severities

- `BLOCKER`
- `IMPORTANT`

### Finding classes

- `authority-drift`
- `repo-reality`
- `coverage`
- `ordering`
- `verification-gap`

The bounded trigger list below owns the second-review rule.

### Conditional risk triggers

A second reviewer is conditional only, never routine.

- `framework or runtime removal`
- `schema migration or data deletion`
- `authentication, authorization, or security boundaries`
- `public/private data-boundary changes`
- `external side effects such as publishing, billing, messaging, or production mutations`

## Default flow, verdicts, and freshness

Default mode is review, repair documents, and scoped re-review. It permits at
most two repair passes; after the second pass, an unresolved material issue
remains `REVISE` rather than being downgraded. `review-only` changes no files
and returns the first review verdict.

### Verdicts

- `READY`: no unresolved finding requires invention or permits a materially wrong implementation to pass planned evidence.
- `REVISE`: a repairable material document defect remains.
- `BLOCKED`: required input, authority, or repository evidence is unavailable or would require a new product decision.

The bounded freshness list below owns the final record and invalidation rule.

### Freshness

- repository-relative design path and SHA-256
- repository-relative plan path and SHA-256
- Git `HEAD` (or `unborn`)
- worktree was clean or dirty
- review timestamp
- final verdict
- Any content change to either resolved document invalidates `READY`.

## Handoff

For `READY`, print the exact resolved design and plan paths with final
fingerprints. In the combined flow, pass the final repaired documents to the
SDD worker rather than the pre-review copies.

### SDD handoff

Do not start SDD unless the outer request explicitly asks for implementation.
