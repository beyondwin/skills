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

## Dispatch contract

The controlling agent writes the instruction. These items are not optional, and
the two instructions differ: a discovery reviewer must arrive told nothing.

### Discovery dispatch

- The baseline: the ordered preceding plans and their paths, with a required
  reconstruction statement on the response's first line.
- The shared-file ledger's path and SHA-256, when one exists.
- An instruction to read a large plan task by task rather than whole.
- The four recurring defect shapes named in Pass 3.
- The output format.

Never carry an earlier round's findings into a discovery instruction.

### Closure dispatch

Everything above, plus:

- The earlier round's PSDR records verbatim. A controller summary is not
  accepted: closure is checked by matching the original Location and Evidence,
  which a summary cannot carry.
- The `repair-impact map`.
- The machine-check results.
- An explicit slot listing the tasks that no record yet points at.

The rule against naming findings, paths, symbols, or fixes when resuming a
reviewer applies only to re-asking an incomplete record for its missing fields.
It does not restrict the closure dispatch above.

## Finding vocabulary

Use only these severities:

- `BLOCKER`: the minimal document fix needs authority, input, or repository
  evidence outside the two reviewed documents, or a new product decision.
  Left unresolved, it forces `BLOCKED`.
- `IMPORTANT`: the minimal document fix is an authority-preserving edit within
  the two reviewed documents. Left unresolved, it forces `REVISE`.

Severity follows the minimal document fix, not the size of the defect.

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
A finding that omits any of these fields is incomplete. Do not return a
summary in place of the records.

Never put source text, prompts, or command output in Evidence paraphrases.

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
report pre-existing dirty state when it makes a claim unresolvable. A
`repo-reality` finding must cite at least one repository path that is neither
the reviewed design nor the reviewed plan.

### Pass 3: cross-artifact consistency

Find design requirements without a plan task and plan work without design
authority. Check task order, producer/consumer interfaces, exact names, types,
paths, state transitions, migration order, destructive targets and safe
prerequisites. Reject placeholders, implied work, and steps that leave an
implementer to choose among materially different designs.

Check these four by name. They recur across plans and languages.

- **An addendum folded into the tasks only halfway.** A revisions or
  final-checks section states a requirement while the task's code block keeps
  the old shape. Two tasks then build the same record with different arity and
  neither reconciliation compiles.
- **Verification that exists in prose but not in code.** "That test covers
  this" where the test is absent or does not look at it. A concurrency
  requirement with no stated method passes with sequential calls.
- **A line number used as a location.** A preceding plan inserting above shifts
  every number below. When the symbol name is already given, the number carries
  only misinformation.
- **A closed list updated on one side only.** Schema enums, exact-match key
  arrays, zod enums, tests that count members. Each plan adds its own entry and
  one omission leaves the published document rejecting its own schema.

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

When a plan asserts a constraint built from several conjuncts, require a table,
not prose: one variant per conjunct removed, each rejection case checked
against each variant. A prose judgement caught three of six conjuncts where the
table caught all six.

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

Detection still covers the final complete documents, but current-repair
eligibility does not. A material finding is eligible only when its source is an
original finding or a direct mapped repair impact. Report any unmapped
material finding without repairing it, end the current invocation, and apply
the existing verdict rules through the unresolved handoff.
