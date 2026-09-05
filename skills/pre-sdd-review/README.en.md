# Pre-SDD Review

[한국어](README.md)

## Purpose

Review an approved design and implementation plan against each other and
repository reality immediately before SDD or plan execution. The default flow
is **review -> repair documents -> scoped re-review**. The question is whether
an implementer can proceed without inventing a missing product decision.

The plan path is primary. The skill resolves the design specification from the
plan's `**Spec:**` field. If that path cannot be resolved, it returns `BLOCKED`
instead of guessing among nearby files. One invocation reviews one plan;
separate plan-local reviews never imply an aggregate `READY`.

When a plan names a required implementation base branch, ref, or commit, the
controller checks that it is an ancestor of the current `HEAD` before reviewer
dispatch. An unresolved or non-ancestor base returns `BLOCKED` instead of
guessing another checkout.

## When to use and not use

Use this when an approved design specification and implementation plan already
exist and need a repository-grounded readiness review before SDD or plan
execution.

Do not use it to write an initial design or plan, review implementation code or
a pull request, verify a release, proofread, or generally improve documentation.
The skill does not start SDD unless the outer request includes implementation.

## Install

In Codex, pass the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

The local evidence recorder is not installed. Run `evidence/evidence.py` from
the skill folder with Python 3.11+. The controller uses the skill root it
already loaded.

```bash
python3 "<skill-root>/evidence/evidence.py" --version
```

Inspect the install folder before update or remove. Shared steps are in
[Installation](../../docs/users/en/installation.md).

## First call

Pass the plan path as the primary input and name the design document as well:

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

During resolution, the plan's `**Spec:**` field selects the resolved design
specification. A separately supplied design path does not override that
authority.

Use `review-only` only when you want the first verdict without document repair;
it changes nothing.

## Expected result

In default mode, a fresh read-only reviewer returns evidence-backed findings.
The controller repairs only the resolved design specification and implementation
plan, then a scoped re-review checks the changed surface.
`review-only` changes nothing and returns the first verdict.

```text
$pre-sdd-review review-only docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

When a structural repair affects a schema, type, state transition, conditional
mutation, task interface, verification meaning, or data boundary, the
controller records the direct consumers and adjacent tasks. Wording and scalar
corrections do not need that impact map.

There are at most two repair passes. The final verdict is one of:

- `READY`: implementation can start without inventing a missing decision.
- `REVISE`: a material, repairable document defect remains.
- `BLOCKED`: required input, authority, or repository evidence is unavailable.

One invocation ends after one discovery stage and its bounded re-reviews.
Authority-preserving repairs need no approval; only a real product decision
creates one consolidated checkpoint. The controller never automatically
repeats an invocation after `REVISE` or `BLOCKED`.

A focused second reviewer is conditional, not routine: runtime removal, schema
migration or data deletion, authentication or security boundaries,
public/private data-boundary changes, or external side effects such as
publishing, billing, messaging, or production mutation. Changing either
document invalidates its fingerprints and requires re-review. Repository
changes do the same when they alter evidence for a path, command, interface, or
blast-radius claim. A new product decision is always `BLOCKED`.

When a compatible local recorder is present, the controller calls `start`
before semantic review, calls `finish` after the final verdict, and prints
`Evidence: recorded; run_id=<run-id>`. If the recorder is unavailable,
incompatible, or denied by permissions, review continues and it prints
`Evidence: not_recorded; reason=<code>`. The controller passes the design path
it resolved from the plan's `**Spec:**` field; when it cannot, it omits the
design and ends with `BLOCKED`. An invocation that ends early closes its run
with `abandon`.

### Contract

- `primary-input`: `plan-primary`, `spec-resolves-design`
- `plan-cardinality`: `one-plan-per-invocation`, `no-aggregate-ready`
- `editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`
- `review-only`: `no-mutation`
- `repair-flow`: `review-repair-bounded-impact-re-review`
- `repair-impact`: `structural-trigger-only`, `direct-consumers`
- `repair-passes`: `at-most-two`
- `verdicts`: `READY`, `REVISE`, `BLOCKED`
- `second-reviewer`: `conditional-only`
- `risk-triggers`: `framework-runtime-removal`, `schema-data-deletion`, `auth-security-boundary`, `data-boundary-change`, `external-side-effects`
- `freshness`: `fingerprints`, `content-change-invalidates`
- `required-base`: `pre-dispatch-ancestor-check`
- `handoff`: `unresolved-packet`
- `sdd`: `outer-request-implementation-only`
- `evidence`: `optional`, `non-blocking`, `controller-local-run-id`

## Safety and privacy

Reviewers are read-only. Automatic mutation is limited to the two resolved
documents in the `Contract` above. Accepted ADRs, visual authority,
application code, tests, configuration, generated artifacts, and unrelated
documentation require a separate product decision.

Receipts stay local as `~/.pre-sdd-review/runs/<run-id>.json` (schema 2).
Records hold repository-relative paths, a directory name, hashes, enum values,
and short paraphrases only. Never put source text, absolute paths, prompts,
transcripts, or credentials in a record. The recorder does not detect secrets.

Local file storage is not a signed audit log resistant to malicious local
tampering. An `outcome` label (`good`, `false-ready`, `noisy`, `abandoned`) is
an observation recorded by a person or the SDD worker after SDD ends and may be
re-recorded to correct it. Labels are self-improvement evidence, not objective
or audit-grade proof.

Details are in [Safety and privacy](../../docs/users/en/safety-and-privacy.md).

## Operations and limits

The command surface is `start`, `finish`, `abandon`, `outcome`, `show`, and
`summary`. For exact arguments, the stdin shape, and size limits, use the
[evidence guide](evidence/README.md).

The log is written for agents. To look for improvements, have an agent run
`summary` and read `anomalies` and `chains` first. Every aggregate carries
`run_id` values so it can drop into `show --run-id`. There is no automatic
fixture selection, skill mutation, or client/model ranking.

The version source is `release.toml`; `SKILL.md` `metadata.version` is a
verified copy. The recorder ignores older `runs/<year>/<month>/` receipts.
Deleting a receipt is deleting its file.

## Supported hosts and verification

pre-sdd-review: Codex supported; other hosts not_measured.

Only Codex has measured support for isolated read-only review and repository
inspection. Other hosts are in [Compatibility](../../docs/users/en/compatibility.md).

Provider-free verification proves package, instruction, and fixture contracts,
not live review quality. Optional live checks are explicit, local, potentially
billable, and never required by CI. Details are in
[Verification](../../docs/users/en/verification.md).

The recorder uses only the Python 3.11+ standard library and is verified by
the provider-free suite on macOS. Linux and native Windows remain
`not_measured` until the evidence stage runs there.

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [Testing](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [Compatibility](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [Release](../../docs/maintainers/products/pre-sdd-review/release.md)
