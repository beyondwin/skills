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

Install the optional CLI from an inspected skill copy only when you want local
receipts. `--bin-dir` must be an existing directory already intended for
`PATH`. Inspect the exact target first, and never pipe a remote script into a
shell.

```bash
ls -ld "$HOME/.local/bin"
python3 skills/pre-sdd-review/evidence/install.py --bin-dir "$HOME/.local/bin"
pre-sdd-review-evidence --version
```

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

In default mode, a fresh read-only reviewer returns evidence-backed findings,
the controller repairs only the resolved design specification and implementation
plan, and a scoped re-review checks the changed surface.
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

A focused second reviewer is conditional, not routine: runtime removal, schema
migration or data deletion, authentication or security boundaries,
public/private data-boundary changes, or external side effects such as
publishing, billing, messaging, or production mutation. Changing either
document invalidates its fingerprints and requires re-review. Repository
changes do the same when they alter evidence for a path, command, interface, or
blast-radius claim. A new product decision is always `BLOCKED`.

When a compatible local CLI is present, the controller calls `start` before
semantic review, calls `finish-review` after the final verdict, and prints
`Evidence: recorded; run_id=<run-id>`. If the CLI is unavailable, incompatible,
or denied by permissions, review continues and it prints
`Evidence: not_recorded; reason=<code>`. The local `run_id` is handed off only
for an explicitly combined SDD request, and `record-outcome` is used only when
downstream work reaches a terminal state.

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
- `handoff`: `unresolved-packet`
- `sdd`: `outer-request-implementation-only`
- `evidence`: `optional`, `non-blocking`, `controller-local-run-id`

## Safety and privacy

Reviewers are read-only. Automatic mutation is limited to the two resolved
documents in the `Contract` above. Accepted ADRs, visual authority,
application code, tests, configuration, generated artifacts, and unrelated
documentation require a separate product decision.

Receipts stay local under `~/.pre-sdd-review/` by default. Even bounded reasons
and findings must not contain source text, paths, prompts, transcripts, or
credentials; use a short paraphrase. Provider-free fixtures must not store user
documents or full model responses.

Create-only storage provides atomicity and consistency for cooperating local
clients, not a signed audit log resistant to malicious local tampering.
Structured downstream observations, assessment basis, and confidence are
observer-supplied. The CLI derives `good`, `false-ready`, `noisy`, and
`prevented-rework` deterministically from those observations. The inputs and
labels are self-improvement evidence, not objective or audit-grade proof.

Before `record-outcome`, represent every known dispute and uncertainty honestly
in the single structured outcome input. Put finding disputes in
`disputed_findings`. Confidence and assessment basis do not alter the
deterministic label. `inconclusive` occurs only when the structured downstream
observations reach the approved derivation fallback. After the create-only
outcome is recorded, schema 1 cannot correct or amend it.

## Operations and limits

The command surface is `start`, `finish-review`, `abandon`, `show`, `pending`,
`doctor`, `resolve`, `record-outcome`, `summary`, `candidates`, and `prune`.
For exact arguments, size limits, recovery, backup, and deletion procedures,
use each `--help` and the [evidence CLI guide](evidence/README.md). Candidate
thresholds are inspection heuristics, not authority for automatic skill
mutation, automatic quality judgment, or client/model ranking.

Before updating or removing anything, inspect the exact installed target. The
version source is `release.toml`; `SKILL.md` `metadata.version` is a verified
copy. Removing the launcher does not delete receipts. Back up the whole
evidence root to preserve identity, and delete receipts only through a reviewed
`prune --dry-run` followed by explicit confirmation of the same selection.

## Supported hosts and verification

pre-sdd-review: Codex supported; other hosts not_measured.

Only Codex has measured support for isolated read-only review and repository
inspection. Provider-free verification proves package, instruction, and
fixture contracts, not live review quality. Optional live checks are explicit,
local, potentially billable, and never required by CI.

The shared CLI has verified the current native macOS path and provider-free
portable construction. Linux and native Windows remain `not_measured` until
the evidence and installer stages actually pass under Python 3.11+ on those
systems. Wrapper tests elsewhere do not imply native support.

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [Testing](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [Compatibility](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [Release](../../docs/maintainers/products/pre-sdd-review/release.md)
