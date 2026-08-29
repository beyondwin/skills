# Pre-SDD Review Evidence Loop Design

**Status:** Approved in chat on 2026-08-30; implementation has not started

**Scope:** Add a provider-neutral local evidence recorder and a bounded
outcome loop to `pre-sdd-review`. Codex, Claude Code, Cursor, and Grok use the
same `pre-sdd-review-evidence` command and the same user-local data root. The
recorder preserves compact review receipts, links later SDD or implementation
outcomes, computes deterministic quality summaries, and identifies sanitized
fixture candidates without automatically changing the skill.

**Out of scope:** Persisting user documents, prompts, code, credentials, or
full model responses; uploading evidence; adding a daemon or database;
automatically changing the skill from logs; ranking model hosts from unlike
real-project workloads; changing a review verdict because evidence recording
failed; and claiming review-workflow support for an unmeasured host.

## Context

`pre-sdd-review` 1.1.0 already emits a compact pass receipt. It records input
and final document fingerprints, pass and finding information, triggered
repair-impact categories, Git freshness, and the final verdict. Its
provider-free fixtures prove instruction and package contracts, while optional
live checks provide only bounded evidence about selected synthetic cases.

That evidence does not answer whether an actual `READY` remained valid during
SDD, whether a finding was later shown to be noise, or whether an automatic
document repair prevented rework. A final response is also transient: it
cannot support longitudinal comparisons across runs or clients unless a user
manually reconstructs earlier sessions.

Saving full conversations would create privacy, storage, and token costs
without producing a reliable evaluation signal. The missing capability is
instead a small, structured pair of records:

1. a review-time receipt containing facts and bounded findings; and
2. a later outcome receipt attached to the same review run.

The evidence recorder is deterministic local tooling. It does not perform
semantic review and never calls a model or network service. The skill and its
reviewers retain authority over findings, repairs, and verdicts.

## Goals

1. Give all supported or measured clients one stable command and one stable
   user-local data root.
2. Preserve enough structured review evidence to distinguish useful repairs,
   false `READY` verdicts, noisy findings, interrupted runs, and unmeasured
   outcomes.
3. Compute Git state, paths, hashes, timestamps, sizes, and repository identity
   in the CLI instead of trusting model-generated metadata.
4. Keep evidence recording non-blocking for the review verdict while making
   recording failure visible.
5. Prevent concurrent clients from overwriting or corrupting one another's
   runs.
6. Separate host protocol compliance from semantic review outcome so degraded
   runs are not compared with full runs as if they were equivalent.
7. Turn repeated, reviewed failures into synthetic fixture candidates without
   copying private source material or modifying the skill automatically.
8. Keep routine overhead to local file I/O and hashing; run aggregation and
   model-assisted improvement only on demand.

## Non-goals

- Do not replace the `pre-sdd-review` reviewer protocol or its authority order.
- Do not make the evidence CLI a semantic design or plan parser.
- Do not require evidence success for `READY`, `REVISE`, or `BLOCKED`.
- Do not add telemetry, remote synchronization, a background service, SQLite,
  or a hosted dashboard.
- Do not store raw design, plan, ADR, code, prompt, transcript, provider
  response, environment-variable value, or credential content.
- Do not infer exact token usage when a client does not expose a trustworthy
  value.
- Do not automatically delete long-lived completed receipts.
- Do not automatically install executables or modify a user's PATH.
- Do not equate CLI portability with full review-workflow support.
- Do not build a generic evidence platform for other skills in this version.

## Decisions

### 1. Product-specific identity

The recorder follows the skill identity instead of introducing a generic
`.skill-evidence` namespace.

| Surface | Value |
| --- | --- |
| Data root | `~/.pre-sdd-review/` |
| Override | `PRE_SDD_REVIEW_HOME` |
| CLI command | `pre-sdd-review-evidence` |
| Candidate skill version | `1.2.0` |
| Initial CLI version | `1.0.0` |
| Initial receipt schema | `1` |

The CLI resolves `~` with the current user's home directory on macOS, Linux,
and Windows. `PRE_SDD_REVIEW_HOME` is the only supported override. Client- or
vendor-specific roots such as `~/.codex/` and `~/.claude/` are forbidden.

The default layout is:

```text
~/.pre-sdd-review/
├── config.json
├── identity.key
├── runs/
│   └── YYYY/
│       └── MM/
│           └── <run-id>/
│               ├── review.json
│               └── outcome.json
└── exports/
```

`exports/` is empty unless the user explicitly requests an export. It is not
an implicit reporting or synchronization destination.

### 2. Responsibility boundary

The skill and agent own semantic decisions:

- authority interpretation;
- finding detection and classification;
- document repair;
- verdict selection;
- whether the reviewer protocol ran fully or in a degraded form; and
- bounded outcome observations not mechanically visible to the CLI.

The CLI owns deterministic facts and persistence:

- repository-root discovery;
- plan `**Spec:**` resolution for evidence capture;
- repository-relative path validation;
- Git `HEAD` and dirty-state capture;
- input and final SHA-256 fingerprints;
- UTC timestamps and elapsed duration;
- stable local repository identity;
- schema, enumeration, privacy, and size validation;
- atomic create-only writes;
- exact plan-hash lookup for downstream linking; and
- deterministic summary and candidate calculations.

The CLI never produces or changes a review verdict. The skill never writes an
evidence JSON file directly.

### 3. One shared local CLI

The canonical CLI implementation is bundled with the `pre-sdd-review`
product and uses only the Python standard library. An explicit installer puts
one `pre-sdd-review-evidence` launcher on the user's PATH. Installation is a
user action; invoking the skill does not modify PATH, shell profiles, or the
home directory outside the declared evidence root.

Each client invokes the same installed command. At review start it also passes
the root of the skill copy it actually loaded:

```bash
pre-sdd-review-evidence start \
  --skill-root /path/to/pre-sdd-review \
  --plan docs/plans/example.md \
  --client cursor
```

The CLI reads the loaded `SKILL.md`, `references/reviewer-protocol.md`, and
`release.toml`. It records their declared versions and SHA-256 fingerprints,
but not the absolute skill-root path. This exposes drift when two clients use
different copies under the same nominal skill version.

Supported client identifiers initially are:

```text
codex
claude-code
cursor
grok
other
unknown
```

An unavailable client or model version is stored as `null`; neither the agent
nor CLI invents it.

### 4. Review lifecycle

#### Start

`start` creates a unique run directory and a private `.pending.json`. It
captures the initial Git and document state and returns the `run_id` and
resolved repository-relative paths.

```text
pre-sdd-review-evidence start
  -> validate evidence root and skill copy
  -> create run ID and run directory exclusively
  -> locate repository root
  -> inspect the named plan and its Spec field
  -> capture hashes, Git state, client, and start time
  -> write .pending.json atomically
  -> return run ID
```

The plan remains the primary input. The CLI resolves the design from the
plan's `**Spec:**` field and does not let a separately supplied design path
override it.

#### Finish review

The agent supplies the bounded semantic result through command arguments or
JSON on standard input:

```bash
pre-sdd-review-evidence finish-review \
  --run-id <run-id> \
  --verdict READY \
  --mode default \
  --protocol full \
  --reviewer-count 2 \
  --review-passes 2 \
  --repair-passes 1
```

`finish-review` reloads the pending state, recomputes final document and Git
facts, validates the supplied findings, writes `review.json` to a temporary
file in the run directory, atomically renames it into place, and removes the
pending file. Existing `review.json` files are never overwritten. An exact
idempotent retry returns the existing receipt hash; a conflicting retry fails.

The final skill report includes one explicit line:

```text
Evidence: recorded; run_id=<run-id>
```

If recording fails, the report preserves the review verdict and exposes the
failure:

```text
Verdict: READY
Evidence: not_recorded; reason=evidence-home-unwritable
```

#### Resolve later

In a combined review-and-SDD flow, the final `run_id` is handed directly to
the downstream worker. A separate session may resolve a run from the current
repository and plan:

```bash
pre-sdd-review-evidence resolve --repo . --plan docs/plans/example.md
```

Resolution compares all of:

- locally derived `repo_id`;
- repository-relative plan path; and
- current plan SHA-256 against the receipt's final plan SHA-256.

One exact match returns its `run_id`. A changed hash returns `stale`. Multiple
exact matches return `ambiguous` and require the actual used `run_id`; the CLI
does not guess that the newest review was the handoff authority.

#### Record downstream outcome

`record-outcome` creates `outcome.json` without changing `review.json`:

```bash
pre-sdd-review-evidence record-outcome \
  --run-id <run-id> \
  --status implementation-completed \
  --basis verified-repository-evidence \
  --confidence high \
  --escaped-finding coverage
```

The CLI validates the current plan hash, enumerations, receipt relationship,
and logical combinations before creating the outcome. For example,
`false-ready` is possible only when the original verdict was `READY` and a
material escaped finding was recorded.

### 5. Review receipt schema

`review.json` is immutable and has these top-level fields:

```json
{
  "schema_version": 1,
  "record_type": "review",
  "run_id": "uuid",
  "started_at": "2026-08-30T10:00:00Z",
  "completed_at": "2026-08-30T10:04:12Z",
  "skill": {},
  "client": {},
  "protocol": {},
  "target": {},
  "result": {},
  "freshness": {},
  "metrics": {}
}
```

#### Skill and client

`skill` records the skill name, declared version, `SKILL.md` fingerprint,
reviewer-protocol fingerprint, CLI version, and schema version. `client`
records the client identifier plus nullable client and model versions.

#### Protocol

`protocol.mode` is `default` or `review-only`. `protocol.execution` is one of:

- `full`: required independent, fresh, read-only review and re-review behavior
  was available and executed;
- `degraded`: the review ran but one or more host capabilities were absent;
- `blocked`: host capability prevented the review workflow from running; or
- `unknown`: compliance could not be established.

The protocol record also includes reviewer count, whether a fresh reviewer was
used, whether read-only behavior was enforced, and any conditional reviewer
trigger. These values describe observed execution; they do not grant a host a
support claim.

#### Target and resolution status

`target` records `repo_id`, initial Git facts, plan and design relative paths,
and their initial fingerprints. It also records one resolution status:

```text
resolved
plan-missing
spec-field-missing
spec-path-invalid
design-missing
outside-repository
not-git-repository
```

When resolution fails safely, unavailable design fields are `null`. Unsafe or
outside-repository absolute paths are never persisted. This permits input
failures to become improvement evidence instead of disappearing before a run
is recorded.

#### Result and findings

`result` records completion, verdict, block reason when applicable, review and
repair pass counts, and an array of bounded findings. A completed review uses
the existing verdicts `READY`, `REVISE`, or `BLOCKED`. An abandoned run has a
null verdict and an explicit completion reason.

Each finding contains:

```json
{
  "id": "PSDR-001",
  "severity": "IMPORTANT",
  "class": "verification-gap",
  "status": "repaired",
  "location": {
    "path": "docs/plan.md",
    "locator": "Task 4 / Verification"
  },
  "evidence_refs": ["package.json#scripts.test"],
  "consequence": "A build-only check can accept wrong behavior.",
  "minimal_fix": "Add behavioral acceptance evidence.",
  "repair_pass": 1
}
```

Severity and class reuse the current skill contract. Finding status is one of:

```text
repaired
unresolved
blocked-by-authority
accepted-as-is
```

`consequence` and `minimal_fix` are each limited to 300 characters. Locations
and evidence references contain relative paths, headings, or symbol names,
never document or code excerpts.

A later dispute cannot mutate this review-time status. It belongs in
`outcome.downstream.disputed_findings`, where it records the finding ID, class,
and bounded downstream basis.

#### Freshness and metrics

`freshness` records final Git state and final design and plan fingerprints.
`metrics` records elapsed milliseconds, reviewer count, and pass counts.
Receipt size is calculated from the completed file at query time rather than
stored inside the receipt that determines that size. Token usage is optional
and accepted only when the client exposes a trustworthy measured value with
provenance.

### 6. Outcome receipt schema

`outcome.json` is a separate create-only record:

```json
{
  "schema_version": 1,
  "record_type": "outcome",
  "run_id": "uuid",
  "recorded_at": "2026-08-31T06:20:00Z",
  "recorder": {
    "client": "claude-code",
    "version": null,
    "model": null
  },
  "downstream": {
    "status": "implementation-completed",
    "plan_hash_matched": true,
    "replan_count": 0,
    "escaped_findings": [],
    "disputed_findings": []
  },
  "assessment": {
    "label": "good",
    "basis": "verified-repository-evidence",
    "confidence": "high"
  }
}
```

Assessment labels are:

```text
good
false-ready
noisy
prevented-rework
inconclusive
abandoned
```

Evidence bases are:

```text
verified-repository-evidence
user-reported
agent-observed
agent-inferred
unknown
```

The CLI derives the label from recorded facts whenever possible rather than
accepting an unsupported `good` claim. Precedence for a mixed run is
`false-ready`, `noisy`, `prevented-rework`, `good`, then `inconclusive`.
Detailed escaped and disputed findings remain available, so the primary label
does not erase mixed evidence. `agent-inferred` outcomes remain separate from
verified and user-reported evidence in summaries.

The initial schema records an outcome only after the downstream task reaches a
terminal status. It does not overwrite or silently amend an outcome later.
Outcome revision history is outside the initial scope; a future schema must add
an explicit append-only amendment contract before corrections are supported.

### 7. Size and privacy boundary

The limits are:

| Record | Soft target | Hard limit |
| --- | ---: | ---: |
| `review.json` | 16 KiB | 32 KiB |
| `outcome.json` | 4 KiB | 8 KiB |
| Completed run | 20 KiB | 40 KiB |

The CLI removes duplicate structured values before rejecting an oversized
record. It never truncates a finding into an ambiguous or malformed record.

Forbidden persisted content includes:

- absolute repository and skill paths;
- document, ADR, code, or test bodies;
- prompts and full model responses;
- provider transcripts;
- environment-variable values and credentials;
- arbitrary command output; and
- data outside the approved receipt fields.

Repository-relative paths use POSIX separators, may not contain `..`, and must
resolve inside the repository. The CLI rejects path and symlink escapes.

### 8. Local repository identity

The first successful setup creates:

```text
~/.pre-sdd-review/config.json
~/.pre-sdd-review/identity.key
```

`config.json` contains only its schema version, creation time, and a
fingerprint of the active identity key. `identity.key` contains 32 random
bytes; the key itself never appears in configuration or receipts.

The key is random, local, and readable only by the current user where the
platform exposes Unix-style permissions. The repository ID is an HMAC of the
canonical repository root with that local key. The root path and key are never
written to a receipt or transmitted.

When neither configuration nor key exists, the first successful setup creates
both. If configuration exists but the key disappears, the CLI fails with
`identity-key-missing` and does not generate a replacement automatically,
because a new key would prevent automatic matching with earlier runs. Existing
receipts remain readable. Backing up the complete evidence root preserves
identity continuity.

### 9. Atomicity, concurrency, and interruption

Each run owns its directory. There is no shared append-only JSONL file and no
global write lock. Files are written to private temporary paths in their final
directory and atomically renamed after validation and flush.

Pending-age classifications are:

```text
0 to 24 hours: active candidate
over 24 hours: interrupted candidate
over 7 days: stale pending
```

`pre-sdd-review-evidence pending` reports them. It does not delete or mutate
them. The explicit `abandon` command converts a pending run into a durable
review record with null verdict, `abandoned` completion, and a bounded reason
such as `client-interrupted`.

Corrupt records are reported and excluded from aggregate metrics. The CLI does
not delete or silently repair them. `doctor` checks data-root permissions,
identity continuity, receipt schemas, stale pending files, corruption, and
CLI/schema compatibility without making changes.

### 10. Retention and deletion

Completed review and outcome receipts are retained indefinitely by default.
Their bounded, content-free form makes automatic expiration unnecessary for
the initial version and preserves the longitudinal evidence the feature
exists to create.

Temporary write files older than 24 hours are cleanup candidates. Pending
runs, completed reviews without outcomes, and completed review/outcome pairs
are not automatically removed.

Deletion is explicit and previewed:

```bash
pre-sdd-review-evidence prune --older-than 730d --dry-run
pre-sdd-review-evidence prune --older-than 730d --confirm
```

Reviews without outcomes are excluded unless the user supplies a separate
explicit include flag. The command reports exact run IDs and record counts
before deletion.

### 11. Quality measures

`summary` scans validated completed records on demand. It does not invoke a
model or persist a background cache as the source of truth.

Primary measures are:

- outcome coverage: completed reviews with outcomes divided by completed
  reviews;
- false `READY`: observed `READY` runs with a material escaped finding divided
  by observed `READY` runs;
- noisy finding rate: later-disputed findings divided by findings with a
  downstream evaluation;
- prevented rework: repairs with concrete downstream prevention evidence;
- protocol compliance: full, degraded, blocked, and unknown counts by client;
  and
- operational overhead: duration, reviewer count, pass count, receipt size,
  and CLI duration.

Every rate prints its numerator and denominator. Missing outcomes are
`not_measured`, not successes. Small slices print counts and an insufficient
sample warning rather than a confident percentage interpretation.

Real-project outcomes are grouped by client, protocol execution, risk trigger,
finding class, and anonymous repository ID. They may identify operational
patterns but cannot rank clients because their workload mix differs.

Client comparisons require the same synthetic fixture, skill fingerprint,
schema, and expected behavior. Full and degraded protocol executions remain
separate.

### 12. Improvement candidates

`candidates` creates a human-review queue from structured evidence. It does not
edit the skill or tests.

Immediate candidates are:

- one false `READY`;
- one escaped `authority-drift` finding in downstream outcome evidence; or
- one originally material finding later disputed with verified or
  user-reported evidence.

Repeated-pattern candidates are:

- the same escaped finding class in at least two runs;
- the same finding pattern marked later-disputed in at least three runs;
- the same degraded client cause in at least three runs; or
- the same input-resolution failure in at least five runs.

Thresholds select items for inspection; they do not authorize an automatic
change. `candidates export` creates a blank synthetic-fixture template with
case metadata, finding class, consequence category, and required reproduction
fields. It never copies source document content.

Forbidden-data attempts and internally inconsistent `full` protocol claims are
rejected before a valid receipt exists. They are immediate CLI or test
failures, not candidate records reconstructed from data the recorder refused
to persist.

The improvement process is:

```text
inspect candidate receipts
  -> describe the failure without private content
  -> author a synthetic design, plan, and repository fixture
  -> reproduce the current failure
  -> design the smallest instruction or protocol correction
  -> run the complete existing fixture suite
  -> prove the new fixture closes
  -> update version and changelog
  -> rerun selected live client checks when their claim changes
```

### 13. Failure policy

Review-domain failures and evidence-system failures are distinct.

Review-domain failures such as a missing plan, missing `**Spec:**`, missing
design, unavailable authority, or unavailable repository evidence may produce
the existing `BLOCKED` verdict and are recorded when possible.

Evidence-system failures use stable reason codes such as:

```text
cli-unavailable
evidence-home-unwritable
schema-invalid
record-too-large
run-not-found
already-finalized
outcome-already-recorded
ambiguous-run
identity-key-missing
unsupported-schema-version
```

They never change the semantic verdict. Every failure is visible in the final
report. Logging silently disappearing is forbidden.

### 14. Host and support claims

Evidence CLI portability and semantic review support are separate matrices.
Provider-free CLI tests may support an operating-system claim. A successful
CLI invocation inside Claude Code, Cursor, or Grok does not prove those hosts
can provide an independent fresh read-only reviewer or equivalent semantic
quality.

Every live run records protocol execution as full, degraded, blocked, or
unknown. The current Codex support claim remains unchanged until host-specific
evidence justifies a documented update. Unmeasured hosts remain
`not_measured`; degraded runs are useful observations, not full support proof.

## Package architecture

The implementation plan may refine filenames while preserving these
boundaries:

```text
skills/pre-sdd-review/
├── SKILL.md
├── README.md
├── README.en.md
├── CHANGELOG.md
├── release.toml
├── LICENSE.txt
├── agents/
│   └── openai.yaml
├── references/
│   └── reviewer-protocol.md
└── evidence/
    ├── README.md
    ├── install.py
    └── pre_sdd_review_evidence/
        ├── __init__.py
        ├── cli.py
        ├── schema.py
        ├── storage.py
        ├── repository.py
        └── reporting.py

tests/products/pre-sdd-review/
├── cases.json
├── test_contract.py
├── evidence/
│   ├── test_cli.py
│   ├── test_schema.py
│   ├── test_storage.py
│   ├── test_repository.py
│   └── test_reporting.py
└── fixtures/
    ├── existing review fixtures
    └── evidence lifecycle fixtures
```

The CLI is divided by responsibility instead of becoming one large script.
The release payload and product-contract allowlist must be updated explicitly;
the current eight-file payload contract cannot be bypassed by appending an
unverified runtime tree.

## Verification design

### Provider-free schema tests

Tests cover required and unknown fields, enumerations, nullable boundaries,
timestamps, SHA-256 syntax, path traversal, absolute paths, forbidden fields,
size boundaries, and logically invalid verdict/outcome combinations.

### Repository and privacy tests

Synthetic repositories cover valid and missing `**Spec:**` fields, missing
plans and designs, dirty state, document changes, outside-repository paths,
symlink escapes, stable local HMAC identity, and absence of absolute roots or
fixture body content in receipts and logs.

### Lifecycle tests

The provider-free matrix covers:

```text
start -> finish-review
start -> interrupted -> abandon
start -> finish-review -> record-outcome
start -> finish-review -> stale plan
start -> finish-review -> ambiguous resolve
idempotent retry
conflicting retry
duplicate outcome
corrupt record
unsupported schema
```

### Concurrency tests

Multiple processes create and finish independent runs concurrently. Tests
prove unique run directories, no overwrites, no partial JSON exposure, no
global-lock dependency, and aggregation of completed validated records only.

### Deterministic reporting tests

Fixed receipts prove outcome coverage, false-`READY` denominators, noisy
finding counts, prevented-rework evidence, protocol separation, exclusion of
inconclusive results, small-sample warnings, and candidate thresholds.

### Optional live client matrix

CI never requires billable model calls. Explicit local checks use only the
existing synthetic review fixtures and record fixture ID, client, fingerprints,
protocol level, verdict, finding IDs/classes, and duration. Full responses are
not retained. Identical fixtures are run separately in Codex, Claude Code,
Cursor, and Grok as available; unavailable clients remain `not_measured`.

## Rollout

### Phase 1: recorder foundation

Implement the CLI, schema, storage root, identity, atomic writes, `doctor`,
`show`, `pending`, and provider-free tests. Do not yet change automatic skill
behavior.

### Phase 2: non-blocking skill integration

Teach `pre-sdd-review` to start and finish evidence when the compatible CLI is
available. Preserve all existing review behavior and report `not_recorded`
when evidence is unavailable. Record `review-only` as well as default mode.

### Phase 3: downstream outcomes

Add exact-hash `resolve`, `record-outcome`, and deterministic assessment.
Inspect the first ten outcomes for data quality only; do not use that small
initial set to claim a quality improvement.

### Phase 4: multi-client measurement

Run the same non-sensitive synthetic fixtures in available clients, record
full versus degraded protocol execution, and update support documentation only
to the level proved by the evidence.

### Phase 5: first improvement loop

Run `summary` and `candidates`, inspect any immediate or repeated candidate,
create a synthetic regression fixture, apply the smallest approved skill
change, and verify the complete provider-free suite plus any affected live
client checks.

## Success criteria

The design is satisfied when:

1. Codex, Claude Code, Cursor, and Grok can call the same installed
   `pre-sdd-review-evidence` command when available.
2. All clients use `~/.pre-sdd-review/` or the explicit
   `PRE_SDD_REVIEW_HOME` override.
3. A completed review creates one immutable, validated, content-bounded
   `review.json` with deterministic Git and fingerprint facts.
4. A later SDD or implementation run can link one exact review and create one
   bounded `outcome.json` without modifying the review receipt.
5. Missing or stale plans, ambiguous matches, interrupted runs, concurrent
   writers, and persistence errors have explicit safe behavior.
6. Evidence failure is visible but cannot change the original review verdict.
7. No receipt, test log, or export contains prohibited source content,
   credentials, absolute paths, prompts, or full model responses.
8. Summary and candidate generation require no model or network call and keep
   verified, reported, inferred, full, degraded, and unmeasured results
   distinct.
9. No log directly modifies the skill; every improvement passes through a
   reviewed synthetic regression fixture and the complete existing suite.
10. CLI portability claims and semantic review-host support claims remain
    separate and evidence-backed.
