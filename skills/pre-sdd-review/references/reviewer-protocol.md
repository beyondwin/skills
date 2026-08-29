# Reviewer protocol

Reviewer mutation policy: read-only. The controlling agent applies document repairs.
Never edit application code, tests, configuration, accepted ADRs,
approved visual authority, generated artifacts, or any review input. Report
evidence and the smallest sufficient authority-preserving document correction;
never start SDD.

Review the resolved design, plan, binding references, and repository evidence.
Treat approved authority as controlling; repository reality can establish
feasibility, integration, or blast-radius conflicts but cannot authorize a
new product decision. Every finding must cite an exact repository-relative
path plus a heading or line.

## Finding vocabulary

Use only these severities:

- `BLOCKER`: SDD cannot safely start because authority, feasibility, ordering,
  or acceptance evidence is materially invalid or missing.
- `IMPORTANT`: SDD could start, but the documents permit a credible wrong
  implementation, avoidable rework, or an unverifiable acceptance claim.

Use only these classes: `authority-drift`, `repo-reality`, `coverage`,
`ordering`, and `verification-gap`.

Return each material finding in this complete record:

```text
ID: PSDR-001
Severity: BLOCKER | IMPORTANT
Class: authority-drift | repo-reality | coverage | ordering | verification-gap
Location: exact document path and heading or line
Evidence: repository or cross-document fact
Consequence: concrete implementation failure
Minimal document fix: smallest authority-preserving correction
```

Exclude style, taste, optional refactoring, generic best practice, and
speculative future work. Zero findings is valid; do not manufacture findings.

## Review passes

### Pass 1: authority trace

Map each approved decision and global constraint to the design section that
records it and the plan task that implements it. Detect authority drift,
silent narrowing, unsupported expansion, exploratory options treated as
accepted, and a plan `**Spec:**` reference that does not identify the reviewed
design.

### Pass 2: repository grounding

Verify named paths, symbols, commands, test runners, versions, actual
extension points, collisions, consumers, and claimed blast radius. Run only
safe read-only baseline checks needed to test a document claim. Preserve and
report pre-existing dirty state when it makes a claim unresolvable.

### Pass 3: cross-artifact consistency

Find design requirements without a plan task and plan work without design
authority. Check task order, producer/consumer interfaces, exact names, types,
paths, state transitions, migration order, destructive targets and safe
prerequisites. Reject placeholders, implied work, and steps that leave an
implementer to choose among materially different designs.

Apply these checks only when their observable trigger is present:

- When a plan or repair introduces or changes a state machine, trace each
  producer, transition, consumer, and failure state. Assertions over selected
  items must prove the `producer domain` and its `partition completeness`, not
  merely loop over one terminal subset. An empty domain is valid when the
  producer proves it is empty. Never require a nonzero approval or success
  count without approved authority.
- Conditional mutations must appear in the task's edit surface as an exact
  path or a bounded path pattern, together with the mutation condition and the
  exact verification command.
- For a new required type or schema field, search direct consumers and
  fixtures. Classify each as `modify`, `verified-no-change`, or `unresolved`.
  Only consumers that require a change belong in the edit surface.
- For a changed public/private boundary, trace the private producer, the
  public projection, serializer, reader, validator, and emitted-output
  rejection.

### Pass 4: verification falsification

For every planned acceptance check, name a concrete materially wrong
implementation that could still pass that check. Require the plan to close a
plausible counterexample. Distinguish static contract evidence, unit behavior
evidence, integration behavior evidence, browser/device behavior evidence,
and external-side-effect evidence; never claim that one evidence class proves
another.

### Pass 5: readiness verdict

Return only material findings and exactly one verdict:

- `READY`: no unresolved finding requires invention or lets a materially wrong
  implementation pass the planned evidence.
- `REVISE`: the documents contain a repairable material defect.
- `BLOCKED`: required authority, input, or repository evidence is unavailable
  and cannot safely be invented.

The controller, not the reviewer, decides whether a documented correction is
within the mutation allowlist and performs any repair. For scoped re-review,
read the final complete documents, evaluate the original findings afresh, and
use the repair-impact map to run a bounded regression over direct consumers
and adjacent task interfaces. Do not expand this into an unrelated full
review.
