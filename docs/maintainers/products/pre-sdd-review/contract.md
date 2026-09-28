# pre-sdd-review contract

This document sets when Pre-SDD Review turns on, which documents win a
conflict, how reviewers stay isolated, and how far the skill may edit
documents. It also sets the rules for findings, freshness, verdicts, and the
SDD handoff.

This is a normative document. Terms used here:

- controller: the agent that runs the skill and edits the documents.
- run: one execution recorded by the recorder.
- ledger: the shared-file ledger, the list of files several plans touch.
- dirty: a plan that needs closure again because a preceding plan's repair
  changed something it reads.

## Activation and input resolution

Activate only when an approved design specification and an implementation
plan both exist and the question is readiness right before SDD or plan
execution. Do not use it to write a first design or plan, for code review,
release readiness, proofreading, or general document work.

Inputs resolve in this order:

- one implementation plan path;
- the resolved design specification that the plan's `**Spec:**` field points
  to;
- explicitly bound references, the repository root, and the current Git state.

If the `**Spec:**` path is missing or cannot be resolved, return `BLOCKED`. Do
not guess among nearby files.

A verdict-bearing invocation reviews exactly one implementation plan.

- If it is unclear which plan, ask for the exact plan path. If none is given,
  return `BLOCKED`.
- Split plans get separate verdicts; never build one aggregate `READY`. A later
  plan's `READY` is not tied to an earlier plan.
- Discoveries may overlap; repairs do not. A preceding `BLOCKED` plan does not
  stop later plans' discovery.
- If a preceding plan's repair changes a shared design, mark every dependent
  plan dirty in this campaign. That invalidation does not open a new campaign.

If a plan names a required implementation base (`branch`, `ref`, or
`commit`), check before dispatching any reviewer that the required base is an
ancestor of `HEAD` with `git merge-base --is-ancestor <required-base> HEAD`. If
the base cannot be resolved or is not an ancestor of `HEAD`, record the
mismatch and return `BLOCKED`. Never review or edit a different checkout on
your own.

## Authority

Conflicts resolve in this order.

### Authority order

1. User-approved direction and referenced visual authority.
2. Accepted ADRs and other explicitly binding decision records.
3. The approved design specification.
4. The implementation plan.
5. Repository reality at this plan's turn.

Repository reality is evidence of feasibility and blast radius; it never
replaces an approved product decision. A plan's turn is the repository plus
every plan before it in the settled execution order, not whatever `HEAD` is at
the moment. If a repair needs a new product decision, keep the conflict and
return `BLOCKED`.

## Reviewer isolation and editable paths

The default reviewer is a freshly dispatched, independent `read-only`
reviewer. Reviewers report evidence and the smallest authority-preserving fix;
only the controller edits documents. Only the paths below may be edited, and
no feature, dependency, host claim, or product decision may be added.

If no independent fresh reviewer is available, the controller does not stand
in for the independent primary reviewer. Evidence `reviewers` counts the agents
actually obtained for logical roles, not the number of roles intended.

### Editable paths

1. resolved design specification.
2. resolved implementation plan.
3. resolved shared-file ledger.

The ledger is derived evidence, not authority, so the five authority levels
stay as they are. When the ledger disagrees with a plan's `Files:`, the plan
wins and the ledger is rebuilt.

### Excluded surfaces

- `accepted ADRs`
- `approved visual authority`
- `application code`
- `tests`
- `configuration`
- `generated artifacts`
- `unrelated documentation`

## Ledger pre-pass

When the outer request names two or more plans, or asks for this pass
explicitly, it runs once before the first verdict-bearing invocation.

- It gives no verdict. Its output is the ledger, the settled execution order,
  and repository-confirmed defect candidates.
- The controller does all of it; no reviewer is dispatched.
- Confirmed candidates are repaired before any reviewer is dispatched. These
  are pre-review repairs, so they do not count as a repair pass and are
  recorded as `repair_pass: 0`.
- In `review-only`, the ledger is not written to a file and these repairs are
  not made.
- This pass is not recorded as a run.

If a plan has no `Files:` section, stop and ask. Do not derive it from a
task's edit scope.

### Ledger shape

- Header: creation time, the target plans with each plan's SHA-256, and the
  settled execution order.
- Body: one row per path. `| path | plans touching this path (in execution order) |`
- List every path, including paths only one plan touches. The sweep targets
  rows with two or more plans.
- The default location is `docs/superpowers/ledgers/YYYY-MM-DD-<campaign>.md`;
  a user preference wins.

## Review passes and findings

The protocol runs exactly `five passes`.

### Review passes

1. authority trace;
2. repository grounding;
3. cross-artifact consistency;
4. verification falsification;
5. readiness verdict.

A finding records an ID, severity, class, exact document location, evidence,
concrete consequence, and the smallest document fix. Zero findings is a valid
result. Severities and classes come only from these lists.

### Severities

- `BLOCKER`
- `IMPORTANT`

### Finding classes

- `authority-drift`
- `repo-reality`
- `coverage`
- `ordering`
- `verification-gap`

### Conditional risk triggers

The second reviewer is `conditional only`, never routine. This list is the
only reason to dispatch a second reviewer.

- `framework or runtime removal`
- `schema migration or data deletion`
- `authentication, authorization, or security boundaries`
- `public/private data-boundary changes`
- `external side effects such as publishing, billing, messaging, or production mutations`

An invocation has at most two review roles: one primary role and, when a
trigger applies, one focused risk role. A new re-review may change the agent,
but never adds a role or widens the risk class. Evidence `reviewers` (0-2) is
neither a cumulative call count nor the intended role count; it counts the
distinct agents actually obtained for logical roles. A `full` run must record 2
with a trigger and 1 without; anything else is observed as
`full_reviewer_count_mismatch`.

### Degraded reasons

- `primary-role-not-obtained`
- `focused-role-not-obtained`
- `agent-reused-within-invocation`
- `agent-reused-across-plans`
- `other`

If no independent primary reviewer is available, return `BLOCKED`; do not
substitute a short degraded round. The focused risk role is dispatched only in
an invocation that runs discovery. If it is not dispatched or not obtained,
record `degraded` with `focused-role-not-obtained`. That reason alone does not
bar handoff reuse or continuation. A `degraded` handoff with any other reason
is not reused. One agent is never reused for another plan's invocation.

## Default flow, verdicts, and freshness

An invocation is one discovery stage (none in a continuation), at most two
repairs, one small residual pass, and a scoped re-review.

- If the first review has zero findings, skip repair and closure and return
  `READY`, but only when the plan is not dirty. A dirty plan still takes scoped
  closure with zero findings.
- Closure requires the repair diff of the design, plan, and ledger.
- If the `HEAD` frozen at the start moves, no `READY` is returned against that
  freeze.

Dirty is controller-local campaign state. It is neither a record field nor the
worktree's dirty state. After repairing plan i, the change set Δ is the union
of the changed resolved design, plan, and ledger fingerprints; the symbols,
paths, commands, and consumers in the impact table; and the paths cited by the
repaired findings. If i precedes plan j and Δ overlaps j's read set, or a
shared design j depends on changed, j is dirty. j's read set is the resolved
design, plan, and ledger paths and hashes, the `Files:` paths, the preceding
plan paths, and the `evidence` paths of its finding records. Paths not in
`Files:` are not in this dirty set; the machine check catches that gap.

Repair accounting:

- `repair_passes` counts every repair pass the controller applied. A new
  invocation does not copy an earlier finding's `repair_pass`.
- `repaired` is used only for records a closure reviewer closed.
- If the last action was a repair, never return `READY`.
- A finding left `partially-closed` counts as unresolved and forces `REVISE`;
  if it is a `BLOCKER`, the verdict is `BLOCKED`.

When a repair changes a schema, type, interface, state transition,
conditional mutation surface, cross-task contract, verification meaning, or
public/private boundary, the controller writes a short impact table. It lists
the changed claim, the changed symbols, states, paths, or commands, the direct
consumers, adjacent task interfaces, a `modify | verified-no-change | unresolved`
disposition, and a verification counterexample. Plain value or wording fixes
outside that list need no table.

The fresh reviewer gets the final repaired documents, the original findings,
and the impact table, and checks first that the original findings are
resolved, then for bounded impact regressions. There are at most two repair
passes. After the second closure, if no more than two `IMPORTANT` original
records remain, each fixable at one site, and the impact table is empty,
repair only those IDs once more and have one fresh closure reviewer check only
those IDs. If a new defect shape appears there, end the invocation. If a
material problem remains after the last pass, do not lower its severity.
`review-only` changes no file and returns the first review's verdict.

In a scoped re-review, only an original finding or a direct mapped repair
impact is repaired now. An unmapped material finding found in the final
documents is not dropped, but it is not repaired now either: end the
invocation, record it in the handoff, and apply the existing verdict rules.

### Verdicts

- `READY`: no remaining problem has to be guessed, and the planned evidence would not let a wrong implementation pass.
- `REVISE`: a material, repairable document defect remains.
- `BLOCKED`: required input, authority, or repository evidence is missing, a
  new product decision is needed, or no independent primary reviewer is
  available. An open `BLOCKER` forces `BLOCKED`.

The final report states the freshness list and invalidation rule below as
written.

### Freshness

- repository-relative design path and SHA-256
- repository-relative plan path and SHA-256
- Git `HEAD` (or `unborn`)
- worktree was clean or dirty
- review timestamp
- final verdict
- baseline: `HEAD`, or `HEAD` plus the list of preceding plans
- ledger: repository-relative path and SHA-256 (omitted when there is none)
- Any content change to either resolved document invalidates `READY`.

The final report also carries a short pass summary: input and final document
hashes, pass numbers, finding IDs and classes, impact triggers, changed
document hashes, and the verdict.

- Copy the observation anomalies (`anomalies`) returned by `finish` onto the
  `Anomalies:` line as they are. Print `none` when empty, and `not_recorded`
  when the recorder was not used or `finish` failed. Do not look this run up
  in a windowed `summary`. Anomalies do not change the verdict.
- `REVISE` and `BLOCKED` return a handoff packet with the unresolved findings
  and the next scope. If new authority is needed, the verdict is `BLOCKED`.

If a reviewer returns only a summary without complete PSDR records, ask that
reviewer once for the complete records, naming only the missing fields. Never
re-ask with answers filled in, such as suspected findings, paths, symbols, or
fixes. A summary is never accepted as a finding.

### Next invocation

Authority-preserving repairs are made without asking. When user authority is
needed, bundle the needed decisions into one approval request. Never re-invoke
automatically after `REVISE` or `BLOCKED`. A later call follows these rules.

- Handoff reuse: from a reusable run (`full`, or `degraded` whose only reason
  is `focused-role-not-obtained`), reuse the handoff only when documents,
  `HEAD`, and the request are all unchanged. Handoffs of other `degraded` runs
  and of `blocked` runs are never reused.
- Continuation: if the last run was a reusable `REVISE`, or `BLOCKED` on a user
  decision the documents now record, and `git diff --name-only <head_end> HEAD`
  shows only the design, plan, and ledger, and the user did not ask for a full
  re-review, start from closure with no discovery. Without a recorded run for
  this plan there is no continuation; run full discovery.
  - Reading an earlier run's recorded findings as open records is not handoff
    reuse; the continuation re-checks them.
  - Carried records keep their `id`, `severity`, and `class`. If closure finds
    a remainder with a different severity or class, close or keep the carried
    record on its own terms and write the remainder as a new record with a new
    ID.
- Decision still pending: if the last run was `BLOCKED` on a user decision the
  authority documents do not yet record, dispatch no reviewer, make no repair,
  and show the same checkpoint again. Do not call `start`; print
  `Evidence: not_recorded; reason=previous-decision-checkpoint`. Other plans
  continue.
- Repeated blocks: if three consecutive runs of the same plan are `BLOCKED` on
  new product decisions, the handoff sends the design back to settle the
  remaining decisions at once, and says the next call waits on them. Without a
  chain of consecutive runs for that plan, report the known count and do not
  stop.

## Optional recorder contract

The recorder is an optional contract. It does not change the authority order,
the reviewer protocol, the editable paths, or the verdict rules. The
controller uses it in this order.

1. From the loaded skill root, run
   `python3 "<skill-root>/evidence/evidence.py" --version`. Record only when
   the handshake is exactly `skill_name=pre-sdd-review` and `schema=4`. The
   canonical line is
   `{"cli_version":"6.0.0","schema":4,"skill_name":"pre-sdd-review"}` followed
   by one LF.
2. If compatible, run `summary --repo <display name>` before `start` and find
   the plan in `runs` and `chains`. If the same `repo` display name and plan
   path are `pending`, `abandon` that run. If the plan's last completed verdict
   is `REVISE` or `BLOCKED`, `show` it.
3. The last run's `execution` decides the next step.
   - When `execution` is `blocked`, never reuse its handoff. If that run was
     `BLOCKED` on a user decision the authority documents do not yet record,
     skip the input gate recheck and follow the "Decision still pending" rule
     above (Verdict and handoff in `SKILL.md`). Once the decision is recorded,
     continue when the continuation conditions hold; otherwise run discovery.
     Any other `blocked` run rechecks the input gates and then calls `start`.
   - When `execution` is `degraded` with any reason besides
     `focused-role-not-obtained`, do not reuse the handoff; `start` a fresh
     full review.
   - For a reusable run, reuse the earlier handoff only when document hashes,
     `git.head_end`, and the request are all the same.
4. When not reusing, call `start` before the semantic review and call `finish`
   once after the verdict and repairs are done.
5. There is exactly one `Evidence:` line. If the recorder is missing or fails,
   report `Evidence: not_recorded; reason=<code>`; that failure does not change
   `READY`, `REVISE`, or `BLOCKED`.

Schema compatibility:

- The recorder reads and writes schema 4 only. `start` always creates a
  checkout-bound schema 4 run.
- Schema 2 and 3 files written by recorders before 6.0.0 are not read,
  migrated, or closed. `show`, `finish`, `abandon`, and `outcome` refuse them
  with `schema-unsupported` and leave the file unchanged. `summary` skips them
  and counts them in `unsupported_records`.
- Old files never block `start`. To clear them, delete the
  `runs/<run-id>.json` files whose top-level `schema` is 2 or 3.

The controller resolves the design path from the plan's `**Spec:**` and passes
it as `--design`. If it cannot be resolved, omit `--design` and return
`BLOCKED`. The recorder does not parse `**Spec:**`. When a run ends before
`finish`, the `abandon` reason is one of `user-cancelled`, `input-changed`,
`scope-changed`, `input-format-fixed`, or `other`. The `run_id` is
controller-local and stays out of the reviewed documents.

A schema 4 finding carries `source` (`reviewer`, `ledger-pass`, or
`machine-check`) and `repair_pass`. `repair_pass` is `null` or 0..3: `0` is a
pre-pass ledger or machine-check repair, and `null` is a finding this
invocation did not repair. A finding without `source`, or `degraded_reasons`
outside the fixed vocabulary, is `schema-invalid`. `finding.evidence` is a list
of repository-relative paths, not prose.

The recorder owns paths, hashes, Git facts, validation, atomic file
replacement, and aggregation under `~/.pre-sdd-review/runs/`. Semantic
findings, repairs, protocol observations, and verdicts belong only to the
reviewer and the controller. Records hold only repository-relative paths,
directory names, `repo_key`, hashes, enum values, integers, timestamps, and
short paraphrases. They never hold source text, absolute paths, prompts,
provider transcripts, command output, environment values, credentials, the
salt, or identity path material. Local files are not a signed audit log.

The evidence home keeps `.identity-salt` as private local 32-byte state and
uses `.identity.lock` and `locks/<run-id>.lock` for mutations. When a command
releases a lock, it deletes that lock file. The normalized checkout root and
Git directory go only into the HMAC; records keep only the derived `repo_key`
and the `repo` display name. A moved checkout, a clone, another worktree, a lost
salt, or a different evidence home is not the original binding. Locks need
supported OS locking. Read-only `show`, `summary`, and `--version` need no
locking. Windows is not supported.

`show` validates a record and returns its original bytes. `summary` reports
`invalid_records` and `unsupported_records` from a full scan before filtering.
`--repo` filters only on the `repo` display name, and `--last` picks valid
ordered records. `counts.verdict` includes every completed verdict seen, and
`normal_verdict` and `anomalous_verdict` split them by observation. These are
local observations, not a model quality measure or a signed audit claim.

Input shape, enum and count ranges, record size, required fields, and path
limits are always validated. The semantic review follows the existing verdict,
reviewer, finding, and repair rules. A structurally valid deviation is kept as
an observation in `anomalies`; evidence never rewrites a verdict or becomes
authority to change anything.

`outcome` is not the controller's job. After SDD or implementation, a person or
the SDD worker leaves one label (`good`, `false-ready`, `noisy`, `abandoned`)
and an optional note. `false-ready` requires a `READY` verdict, and a label may
be recorded again. `summary` is JSON for agents: counts, cost, per-plan chains,
repeated finding patterns, and anomalies, each tagged with its `run_id`. These
values never auto-edit the skill, export fixtures, or rank clients or models.

## Files to change together

Never put a behavior change in only one file.

- Authority order, verdicts, repair limits, reviewer roles:
  `skills/pre-sdd-review/SKILL.md`, `references/reviewer-protocol.md`, this
  contract, `tests/products/pre-sdd-review/cases.json`, and the product READMEs.
- Recorder commands and schema 4: `skills/pre-sdd-review/evidence/evidence.py`,
  `evidence/README.md`, `tests/products/pre-sdd-review/evidence/`.
- Host support: `products.toml`, `compatibility.md`, the public guides, and the
  matching tests. This work does not widen host support.

## Not added

These are explicitly not added:

- closure-only input schema
- evidence probe cache

In this version, invalidation is handled by the controller-local dirty set.

## Handoff

On `READY`, print the exact paths and final fingerprints of the resolved design
and plan. In a review-then-implement flow, hand the SDD worker the final
documents, not a pre-repair copy.

### SDD handoff

Do not start SDD unless the outer request explicitly asks for implementation.

### Contract

- `primary-input`: `plan-primary`, `spec-resolves-design`
- `plan-cardinality`: `one-plan-per-verdict-bearing-invocation`, `no-aggregate-ready`
- `editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`, `resolved-shared-file-ledger`
- `ledger`: `pre-pass-no-verdict`, `derived-not-authority`
- `baseline`: `plan-turn-reality`
- `review-only`: `no-mutation`
- `repair-flow`: `review-repair-bounded-impact-re-review`
- `repair-impact`: `structural-trigger-only`, `direct-consumers`
- `repair-passes`: `at-most-two`, `residual-pass-once`, `applied-passes-counted`
- `verdicts`: `READY`, `REVISE`, `BLOCKED`
- `second-reviewer`: `conditional-only`, `no-cross-plan-reuse`
- `risk-triggers`: `framework-runtime-removal`, `schema-data-deletion`, `auth-security-boundary`, `data-boundary-change`, `external-side-effects`
- `freshness`: `fingerprints`, `content-change-invalidates`
- `required-base`: `pre-dispatch-ancestor-check`
- `handoff`: `unresolved-packet`, `reusable-execution-only`
- `continuation`: `docs-only-diff`, `closure-first`, `recorded-run-required`
- `sdd`: `outer-request-implementation-only`
- `evidence`: `optional`, `non-blocking`, `controller-local-run-id`
- `campaign-scheduler`: `discoveries-may-overlap`, `repairs-do-not-overlap`
