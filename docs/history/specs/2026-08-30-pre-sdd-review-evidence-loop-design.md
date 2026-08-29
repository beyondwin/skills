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
and Windows. `PRE_SDD_REVIEW_HOME` is the only supported override. The
override must be non-empty and absolute after user expansion. Before any
mutation, the CLI canonicalizes it so the same existing symlink alias selects
the same root from every working directory; it rejects a relative value and
symlinked configuration, identity, run, receipt, export root, or candidate
export entries. Every mutable descendant must resolve inside the canonical
evidence root. Client- or
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
  --client cursor \
  --mode default
```

The CLI reads the loaded `SKILL.md`, `references/reviewer-protocol.md`, and
`release.toml`. It records their declared versions and SHA-256 fingerprints,
but not the absolute skill-root path. This exposes drift when two clients use
different copies under the same nominal skill version.

`pre-sdd-review-evidence --version` emits one canonical JSON object containing
`cli_version`, `schema_version`, and `skill_name`. A skill copy is compatible
only when the command reports `skill_name=pre-sdd-review`, schema `1`, and CLI
major version `1`; an unavailable, malformed, or incompatible response is a
visible non-recording reason and never triggers installation.

The exact bytes for version `1.0.0` are
`{"cli_version":"1.0.0","schema_version":1,"skill_name":"pre-sdd-review"}\n`.
`--version` accepts no other command or semantic arguments, performs no
evidence-home discovery or mutation, and emits no additional key or stderr.

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

The field grammar is exact. A field occupies one physical Markdown line and
has `**Spec:**`, optional horizontal whitespace, then either one non-whitespace
plain path token or one balanced single-backtick inline-code path, followed
only by optional horizontal whitespace. The extractor unwraps the inline-code
form before path resolution. It rejects an empty value, more than one field,
multiple path tokens, trailing prose, multiline or fenced-code values,
unbalanced or nested backticks, and any value that fails the path rules below.
A plain relative value is repository-root-relative; only a value beginning
`./` is plan-directory-relative.

`start` requires `--mode default|review-only` and stores that intended mode
only in the private pending record; a later `finish-review` mode must match it.
Every created pending run returns exactly `status="started"`, `run_id`,
`resolution_status`, and nullable `plan_path` and `design_path`; failed target
resolution still uses `status="started"` because the run was durably created.
The private pending record also stores a domain-separated HMAC
`start_locator_binding` of the canonical directory used as the Git-discovery
anchor. The canonical locator and binding are never copied to a final receipt
or emitted in command output or errors.

#### Finish review

The agent supplies the bounded semantic result through command arguments or
JSON on standard input:

```bash
pre-sdd-review-evidence finish-review \
  --run-id <run-id> \
  --repo . \
  --verdict READY \
  --mode default \
  --execution full \
  --reviewer-count 2 \
  --fresh-reviewer true \
  --read-only-enforced true \
  --conditional-trigger data-boundary \
  --review-passes 2 \
  --repair-passes 1
```

`finish-review` reloads the pending state. For every status with a repository
identity, it discovers the Git root from the required `--repo` locator,
recomputes its HMAC repository ID, and rejects a wrong repository before
resolving only the relative plan and design paths recorded in the pending
state. For `not-git-repository`, the required `--repo` locator must resolve to
the same canonical non-Git directory and reproduce the private pending-only
`start_locator_binding`; a different locator or a locator that now resolves to
a Git repository fails closed. A matching locator finalizes the blocked review
with all repository, Git, path, and hash fields still null. It then recomputes
available final document and Git facts,
validates the supplied findings, writes canonical bytes to a temporary
file in the run directory, publishes it with the atomic no-replace primitive
defined below, and removes the
pending file. Existing `review.json` files are never overwritten. An exact
idempotent retry returns the existing receipt hash; a conflicting retry fails.
The repository locator is used only for this invocation and is never persisted
or echoed in an error.

`finish-review` accepts either the documented scalar arguments plus repeatable
`--finding-json` objects, or one exact equivalent object through
`--from-stdin`; mixed forms are rejected. `start` returns `status`, `run_id`,
`resolution_status`, and the nullable repository-relative `plan_path` and
`design_path`. The exact successful value of `status` is `started`.

The finish semantic object is flat and has exactly `mode`, `execution`,
`reviewer_count`, `fresh_reviewer`, `read_only_enforced`, nullable
`conditional_trigger`, `degraded_reasons`, `verdict`, nullable `block_reason`,
`review_passes`, `repair_passes`, `findings`, and nullable `token_usage`.
Argument form maps these one-to-one to `--mode`, `--execution`,
`--reviewer-count`, `--fresh-reviewer true|false`,
`--read-only-enforced true|false`, optional `--conditional-trigger`, repeatable
`--degraded-reason`, `--verdict`, optional `--block-reason`,
`--review-passes`, `--repair-passes`, repeatable `--finding-json`, and optional
`--token-usage-json`. Optional scalar fields default to null and repeatable
fields default to empty arrays; every other flag is required. The protocol
example's `--protocol full` is the spelling `--execution full` in the final
CLI. A frozen-clock normalization fixture proves argument and stdin forms
produce identical semantic objects before deterministic facts are merged.

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
  --repo . \
  --client claude-code \
  --status implementation-completed \
  --basis verified-repository-evidence \
  --confidence high
```

As with finalization, `record-outcome` requires a current repository locator,
verifies its HMAC repository ID, and resolves the recorded relative plan path
before validating the current plan hash. It accepts equivalent bounded
argument and `--from-stdin` forms and rejects mixed input. The CLI validates
enumerations, receipt relationship, and logical combinations before creating
the outcome. For example,
`false-ready` is possible only when the original verdict was `READY` and a
material escaped finding was recorded.

The outcome semantic object has exactly `recorder`, `status`, `replan_count`,
`evaluated_finding_ids`, `escaped_findings`, `disputed_findings`,
`prevented_rework`, `basis`, and `confidence`. `recorder` has the exact client
fields defined below. Argument form maps these to required `--client`, optional
`--client-version`/`--model`, required `--status`, optional `--replan-count`
(default `0`), repeatable `--evaluated-finding`,
`--escaped-finding-json`, `--disputed-finding-json`, and
`--prevented-rework-json`, plus required `--basis` and `--confidence`.
Repeatable fields default to empty arrays. Repository identity and
`plan_hash_matched=true` are computed facts and are accepted from neither
input form. A normalization fixture proves canonical parity.

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

`skill` records the skill name, matching declared/release versions,
`SKILL.md`, reviewer-protocol, and `release.toml` fingerprints, CLI version,
and schema version. `client` records the client identifier plus nullable client
and model versions.

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

`result` records completion, verdict, block reason when applicable, a nullable
completion reason, review and repair pass counts, and an array of bounded
findings. A completed review uses the existing verdicts `READY`, `REVISE`, or
`BLOCKED`. An abandoned run has a null verdict and an explicit completion
reason.

Each finding contains:

```json
{
  "id": "PSDR-001",
  "severity": "IMPORTANT",
  "class": "verification-gap",
  "pattern_key": "build-only-acceptance",
  "consequence_category": "escaped-material-defect",
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

#### Exact schema 1 contract

All objects reject unknown keys. All strings are UTF-8, single-line, free of
control characters, and bounded as stated below. SHA-256 values are 64
lowercase hexadecimal characters; Git object IDs are `unborn` or 40/64
lowercase hexadecimal characters; times use UTC RFC 3339 with a `Z` suffix;
and run IDs are canonical lowercase UUIDs. Paths and evidence references are
at most 500 characters, locators 200, client/model/provenance values 100, and
`pattern_key` 80 characters matching `[a-z0-9][a-z0-9._-]*`.
Finding IDs match `PSDR-[0-9]{3,}`, and a non-null block reason is a bounded
100-character reason code using the same lowercase slug alphabet.

| Object | Exact fields |
| --- | --- |
| `skill` | `name`, `declared_version`, `release_version`, `skill_sha256`, `reviewer_protocol_sha256`, `release_manifest_sha256`, `cli_version`, `schema_version` |
| `client` | `id`, nullable `version`, nullable `model` |
| `protocol` | `mode`, `execution`, `reviewer_count`, `fresh_reviewer`, `read_only_enforced`, nullable `conditional_trigger`, `degraded_reasons` |
| `target` | nullable `repo_id`, nullable `initial_head`, nullable `initial_dirty`, nullable `plan_path`, nullable `plan_initial_sha256`, nullable `design_path`, nullable `design_initial_sha256`, `resolution_status` |
| `result` | `completion`, nullable `verdict`, nullable `block_reason`, nullable `completion_reason`, `review_passes`, `repair_passes`, `findings` |
| `freshness` | nullable `final_head`, nullable `final_dirty`, nullable `plan_final_sha256`, nullable `design_final_sha256` |
| `metrics` | `elapsed_ms`, `recorder_elapsed_ms`, `reviewer_count`, `review_passes`, `repair_passes`, nullable `token_usage` |
| `token_usage` | `input`, `output`, `total`, `provenance` |

Client IDs and resolution statuses are the exact values already listed in
this design. Modes are `default` and `review-only`. Protocol execution is
`full`, `degraded`, `blocked`, or `unknown`. Conditional triggers are null or
`runtime-removal`, `schema-migration`, `auth-boundary`, `data-boundary`, or
`external-side-effect`. Degraded reasons are deduplicated values from
`fresh-reviewer-unavailable`, `read-only-unavailable`,
`conditional-reviewer-unavailable`, `host-capability-unknown`, and `other`.
Completion is `completed` or `abandoned`. A non-null `completion_reason`
matches the literal grammar `[a-z0-9][a-z0-9._-]{0,99}`; `block_reason` uses
the same grammar.

Each finding has exactly `id`, `severity`, `class`, `pattern_key`,
`consequence_category`, `status`, `location`, `evidence_refs`, `consequence`,
`minimal_fix`, and nullable `repair_pass`. `location` has exactly `path` and
`locator`. Consequence categories are `escaped-material-defect`,
`avoidable-rework`, `false-block`, `protocol-degradation`,
`input-resolution-failure`, and `other`. Finding IDs are unique in one review;
lists are deduplicated by exact canonical value while preserving first-seen
order.

Schema validation enforces these relationships:

- `skill.name` is `pre-sdd-review`; declared and release versions are equal;
  embedded CLI/schema versions equal the running recorder.
- `protocol.execution=full` requires a fresh reviewer, enforced read-only
  behavior, no degraded reason, one reviewer normally, and two reviewers when
  a conditional trigger is present. `degraded` requires at least one reason.
- `result.completion=abandoned` requires a null verdict, null block reason, a
  non-null completion reason, zero review/repair passes, and no findings.
  `completed` requires one verdict, a null completion reason, and at least one
  review pass.
- `READY` permits only `repaired` findings. `REVISE` requires at least one
  `unresolved` finding. `BLOCKED` requires a block reason. Repair passes are 0
  through 2; review passes are 0 through 3; a non-null finding repair pass is
  within the recorded range.
- Resolution nullability is exact:
  - `resolved`: repository/Git facts, both relative paths, and all document
    hashes are non-null.
  - `plan-missing`: repository/Git facts and a safe normalized relative plan
    path are non-null; all document hashes and design fields are null.
  - `spec-field-missing` or `spec-path-invalid`: repository/Git facts plus the
    plan path/hash are non-null; design path/hash are null.
  - `design-missing`: repository/Git facts, plan path/hash, and a safe relative
    design path are non-null; the design hash is null.
  - `outside-repository`: repository/Git facts are non-null. An offending plan
    path makes every path/hash null; an offending Spec value retains only the
    already validated plan path/hash. The offending value is never retained.
  - `not-git-repository`: repository/Git facts and every path/hash are null.
  For completed reviews, final freshness mirrors the same availability after
  recomputation; it never fabricates a repository ID, Git state, path, or hash.
  Canonically abandoned reviews instead use the all-null freshness projection
  defined below because `abandon` accepts no repository locator.
- Mirrored counts use three exact pairwise invariants:
  `protocol.reviewer_count == metrics.reviewer_count`,
  `result.review_passes == metrics.review_passes`, and
  `result.repair_passes == metrics.repair_passes`. Durations and token counts
  are non-negative, token totals equal input plus output, and token provenance
  is non-empty when token usage exists.

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
    "evaluated_finding_ids": [],
    "escaped_findings": [],
    "disputed_findings": [],
    "prevented_rework": []
  },
  "assessment": {
    "label": "good",
    "basis": "verified-repository-evidence",
    "confidence": "high"
  }
}
```

Schema 1 terminal downstream statuses are `sdd-completed`,
`implementation-completed`, `implementation-abandoned`, and `cancelled`.
Confidence is `low`, `medium`, or `high`. `plan_hash_matched` must be true to
create an outcome; a stale plan is reported as a command failure, not written
as a false value.

The outcome top level has exactly `schema_version`, `record_type`, `run_id`,
`recorded_at`, `recorder`, `downstream`, and `assessment`. `recorder` has
exactly `client`, nullable `version`, and nullable `model`, using the same
client and bounded-string rules as the review receipt.

`downstream` has exactly `status`, `plan_hash_matched`, `replan_count`,
`evaluated_finding_ids`, `escaped_findings`, `disputed_findings`, and
`prevented_rework`. Evaluated IDs refer to findings in the immutable review.
Every disputed or prevented-rework ID must also be evaluated. Escaped findings
have exactly `severity`, `class`, `pattern_key`, `consequence_category`, and
`basis`; disputed findings have exactly `finding_id`, `class`, `pattern_key`,
`consequence_category`, and `basis`; prevention records have exactly
`finding_id`, `pattern_key`, `consequence_category`, and `basis`. IDs and
structured records are unique, and `replan_count` is a non-negative integer.
These fields let reporting calculate evaluated denominators and stable pattern
groups without parsing consequence prose.

Disputed and prevention records must copy the referenced immutable finding's
class, pattern key, and consequence category exactly. A prevention record may
reference only a finding whose review-time status is `repaired`; an unresolved
or authority-blocked finding cannot become prevented rework. The validation
suite includes both mismatch and unresolved-finding counterexamples.

`assessment` has exactly `label`, `basis`, and `confidence`. The recorder
derives `false-ready` from a `READY` review plus a material escaped finding;
`noisy` from a disputed material finding; `prevented-rework` from a prevention
record; `good` only for a completed downstream status with no escaped or
disputed material finding; `abandoned` only for an abandoned/cancelled status;
and otherwise `inconclusive`. The mixed-result precedence below applies after
the abandoned-status rule.

For `false-ready`, `noisy`, and `prevented-rework`, assessment basis is derived
from the independently sufficient triggering records using this trust order:
`verified-repository-evidence`, `user-reported`, `agent-observed`,
`agent-inferred`, then `unknown`; the strongest available sufficient record is
used, and a caller-supplied different basis is rejected. For `good`,
`inconclusive`, and `abandoned`, there is no triggering finding record, so the
bounded recorder observation supplies the basis without promotion. Confidence
remains an explicit observation and never changes the basis.

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

The CLI removes exact duplicate list values by their canonical JSON bytes,
preserving first-seen order, before rejecting an oversized record. It never
merges distinct findings or truncates a finding into an ambiguous or malformed
record. Standard-input and on-disk reads are bounded to the applicable hard
limit plus one byte before JSON decoding so an oversized or corrupt file
cannot force an unbounded allocation.

One shared bounded binary/JSON reader owns that rule. Pending, review,
outcome, config, scan, doctor, resolve, summary, candidate, and prune paths
must call it; direct `read_bytes()` or an unbounded `read()` of an evidence
record is forbidden. Scanners report an oversized record as corrupt and
continue within their documented exclusion policy.

Forbidden persisted content includes:

- absolute repository and skill paths;
- fields dedicated to document, ADR, code, or test bodies, plus multiline or
  control-character-bearing values in bounded semantic prose;
- prompts and full model responses;
- provider transcripts;
- environment-variable values and credentials;
- arbitrary command output; and
- data outside the approved receipt fields.

The validator can prove the closed field set, bounds, path rules, and obvious
credential/absolute-path rejection. The controller remains responsible for
paraphrasing bounded `consequence` and `minimal_fix` values rather than placing
source excerpts in them; the CLI does not make an impossible claim that an
arbitrary short prose value can be identified as copied source content.

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

Identity initialization is create-only and race-safe without a persistent
global lock:

1. Validate that the root and any existing identity entries are private
   regular files/directories, never symlinks.
2. When neither file exists, generate a candidate key and create
   `identity.key` with exclusive creation and owner-only mode. Exactly one
   concurrent initializer wins; losers discard their candidates and read the
   winning key.
3. Derive the config fingerprint from that exact key. Derive `created_at`
   deterministically from the winning key file's initial modification time, then
   publish matching canonical `config.json` create-only.
4. A valid key-only state is recoverable by creating the matching config
   without replacing the key. Config-only, malformed, wrong-length,
   mismatched, or symlinked states fail closed. No state regenerates or
   replaces an existing key automatically.
5. Flush each new file and its containing directory before reporting setup
   success.

Concurrent first starts must all observe the same key fingerprint and derive
the same repository ID. Existing receipts remain readable when identity
validation fails: direct receipt loading, `show`, pending classification,
`summary`, `candidates`, and `prune --dry-run` validate only the bounded
receipt bytes they need.
Identity-dependent mutation and repository-matching commands (`start`,
`finish-review`, `resolve`, `record-outcome`, and confirmed `prune`) fail
closed, while `doctor` reports the identity fault. Backing up the complete
evidence root preserves identity continuity.

### 9. Atomicity, concurrency, and interruption

Each run owns its directory. There is no shared append-only JSONL file and no
long-lived global write lock. Files are written to private sibling temporary
paths and flushed, then published with an atomic no-replace operation. The
reference operation hard-links the temporary file to the absent final name,
handles `FileExistsError` as an idempotent/conflicting retry, flushes the
directory, and removes the temporary name. A platform/filesystem without a
safe no-replace primitive fails with `atomic-create-unsupported`; it never
falls back to `os.replace()` or another overwriting rename. Per-run locks
serialize cooperating transitions but are not the immutability guarantee.

Pending creation is the bounded exception to the sibling-file shape because
pending bytes contain `start_locator_binding`. `start` creates a private
`runs/.staging-<run-id>/` directory, writes and flushes its only record as
`.pending.json`, then atomically renames that staging directory to the absent
`runs/YYYY/MM/<run-id>/` destination and flushes the parent directories. It
never writes a sibling pending temp file and never writes the raw canonical
locator. A crash after pending fsync but before directory publication may
leave exactly that private staging directory; no normal run scan treats it as
a run.

Before any later evidence-home mutation, internal recovery scans only exact
`.staging-<canonical-uuid>` names. A private, symlink-free staging directory
containing one bounded, schema-valid `.pending.json` is promoted to its exact
absent final run path. If that path already contains byte-identical pending
state, recovery removes the staging container after validation; any conflict,
extra entry, corruption, or unsafe path is left unchanged and reported by
`doctor`. This promotion/cleanup completes an interrupted create-only write;
it is not receipt pruning. Read-only commands never mutate staging state and
never project its binding or intended-mode values.

If `finish-review` or `abandon` crashes after final receipt publication but
before pending unlink, the terminal receipt is authoritative and public scans
ignore the coexisting pending record. An exact idempotent retry validates the
existing final bytes, removes `.pending.json` and matching private temp/lock
artifacts, flushes the run directory, and returns the existing receipt hash. A
conflicting retry changes nothing. This reconciliation is identical for both
terminal transitions; it can never rewrite the final receipt.

Pending-age classifications are:

```text
0 to 24 hours: active candidate
over 24 hours: interrupted candidate
over 7 days: stale pending
```

`pre-sdd-review-evidence pending` reports them. It does not delete or mutate
them. The explicit `abandon` command converts a pending run into a durable
review record with null verdict, `abandoned` completion, and a bounded reason
such as `client-interrupted`. Its input is exactly `abandon --run-id <id>
--reason <slug>`; it maps the slug to `result.completion_reason`. An exact
idempotent retry returns `{"status":"abandoned","run_id":<id>,"sha256":<hash>}`;
a different reason is a conflicting retry. The durable receipt contains no
private start-locator binding.

The abandoned `review.json` projection is canonical rather than supplied by
the caller:

- top-level schema/record/run IDs, `started_at`, `skill`, `client`, and
  `target` come unchanged from validated pending state; `completed_at` is the
  abandon clock;
- `protocol` is exactly the pending intended `mode`, `execution="unknown"`,
  `reviewer_count=0`, `fresh_reviewer=false`, `read_only_enforced=false`,
  `conditional_trigger=null`, and an empty `degraded_reasons` list;
- `result` is exactly `completion="abandoned"`, `verdict=null`,
  `block_reason=null`, the caller's validated `completion_reason`, zero review
  and repair passes, and no findings;
- every `freshness` field is null because abandon has no repository locator
  from which to recompute final facts;
- `metrics.elapsed_ms` is the non-negative wall-clock interval from
  `started_at`, `recorder_elapsed_ms` is the measured abandon-command time,
  reviewer/review/repair counts are zero, and `token_usage=null`.

An abandoned receipt is the sole exception to resolution-based final
freshness availability: its nulls mean not recomputed, never fabricated. The
canonical locator is invocation-local, has no pending field, and is discarded
immediately after deriving the HMAC binding; it is never persisted anywhere.
The private `intended_mode`, `start_locator_binding`, and every other
pending-only key are excluded from the exact final schema. Only the private
`.pending.json` may contain the binding, and either successful
`finish-review` or `abandon` removes that file after create-only publication.
Public `start`, `pending`, `doctor`, scan/error, final receipt, export,
summary, and candidate projections never include pending-only key names or
values.

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
pre-sdd-review-evidence prune --older-than 730d \
  --confirm-selection <selection-digest> --from-stdin
```

Reviews without outcomes are excluded unless the user supplies a separate
explicit include flag. Dry-run reports exact run IDs, record fingerprints,
selection options, counts, and a SHA-256 digest of that canonical selection.
Confirmation supplies the exact previewed selection object on standard input
and its digest. The CLI locks those run IDs in sorted order, revalidates every
fingerprint and eligibility condition, and deletes only that listed set; any
change aborts the entire operation. Newly eligible runs that were absent from
the preview are never added implicitly.

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
change. Finding `pattern_key`, protocol `degraded_reasons`, outcome
`prevented_rework`, `evaluated_finding_ids`, and structured consequence
categories are the only grouping inputs; the CLI never clusters free prose.
Candidates use one discriminated schema:

- common fields: `schema_version`, `candidate_id`, `kind`,
  `source_run_count`, `group`, and `required_synthetic_files`;
- `kind=finding-pattern`: `group` has exactly `finding_class`, `pattern_key`,
  and `consequence_category`;
- `kind=degraded-reason`: `group` has exactly `client` and
  `degraded_reason`; and
- `kind=resolution-failure`: `group` has exactly `resolution_status`.

Candidate IDs are SHA-256 hashes of the canonical tuple `(schema_version,
kind, group)`. No sentinel finding values are used for non-finding candidates.

`candidates export` creates exactly one new
`exports/<candidate-id>/` directory containing `candidate.json`, `design.md`,
`plan.md`, `repository.json`, and `expected.json`. The JSON metadata records
only the common fields and the kind-specific `group`. The four fixture files contain fixed blank
section/object templates; `plan.md` contains only the relative
`**Spec:** ./design.md` link and blank task headings. Export is create-only and
never copies receipt prose or source document content.

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
identity-state-invalid
wrong-repository
invalid-evidence-home
atomic-create-unsupported
selection-changed
incompatible-cli
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
Path-rendering and `.cmd` unit tests on a non-Windows host prove only portable
construction. Native Windows CLI portability remains `not_measured` until the
evidence and installer stages pass under Python 3.11 on a native Windows
runner; no closeout converts the portable profile into that claim.

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
        ├── __main__.py
        ├── cli.py
        ├── schema.py
        ├── storage.py
        ├── repository.py
        └── reporting.py

tests/products/pre-sdd-review/
├── cases.json
├── test_contract.py
├── evidence/
│   ├── __init__.py
│   ├── support.py
│   ├── test_cli.py
│   ├── test_schema.py
│   ├── test_storage.py
│   ├── test_repository.py
│   ├── test_outcome.py
│   ├── test_reporting.py
│   └── test_install.py
└── fixtures/
    ├── existing review fixtures
    └── evidence lifecycle fixtures
```

The CLI is divided by responsibility instead of becoming one large script.
The release payload and product-contract allowlist must be updated explicitly;
the current eight-file payload contract cannot be bypassed by appending an
unverified runtime tree.

The installer uses the same explicit runtime-file manifest as the product and
archive checks. It copies only listed regular files, rejects symlinks and
unexpected package entries, and verifies release, CLI, and schema identities
by parsing data and literal constants without importing the supplied package
before writing a launcher. It never recursively stages or executes an
arbitrary caller-supplied package directory during validation.

## Verification design

### Provider-free schema tests

Tests cover required and unknown fields, enumerations, nullable boundaries,
timestamps, SHA-256 syntax, path traversal, absolute paths, forbidden fields,
size boundaries, and logically invalid verdict/outcome combinations.
An AST-backed payload contract rejects network-capable imports, provider SDK
identifiers, shell execution, and non-Git subprocess executables from the
runtime package.

### Repository and privacy tests

Synthetic repositories cover valid and missing `**Spec:**` fields, missing
plans and designs, dirty state, document changes, outside-repository paths,
symlink escapes, stable local HMAC identity, and absence of absolute roots or
fixture body content in receipts and logs.

Concurrent empty-root setup additionally proves one winning identity key,
matching config fingerprint, and identical repository IDs across all starts.
Finalization and outcome tests run from a second repository and a changed
skill copy to prove wrong-checkout rejection and complete skill fingerprint
capture.

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

Native Windows execution is a separate optional evidence row. When no native
runner is authorized or available, provider-free implementation work can
close with that row explicitly open as `not_measured`, but cannot claim
Windows CLI portability as satisfied.

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
7. Receipts, logs, and exports reject prohibited raw-body fields, multiline
   source bodies, credential-shaped values, absolute paths, prompts, and full
   model responses; bounded semantic prose remains a controller responsibility.
8. Summary and candidate generation require no model or network call and keep
   verified, reported, inferred, full, degraded, and unmeasured results
   distinct.
9. No log directly modifies the skill; every improvement passes through a
   reviewed synthetic regression fixture and the complete existing suite.
10. CLI portability claims and semantic review-host support claims remain
    separate and evidence-backed; native Windows stays `not_measured` until a
    native Python 3.11 run passes.
