# Pre-SDD Review

[한국어](README.md)

## Purpose

Review an approved design and implementation plan against each other and
repository reality immediately before SDD or plan execution. The default flow
is **review -> repair documents -> scoped re-review**: a readiness gate that
checks whether an implementer can proceed without inventing a product decision.

The plan path is primary. The skill resolves the resolved design specification
from that plan's `**Spec:**` field. If the `**Spec:**` path cannot be resolved,
it returns `BLOCKED` instead of guessing among nearby documents.

One invocation reviews one implementation plan. If several plans are named and
the target is unclear, the result is `BLOCKED`. Separate plan-local reviews
never imply an aggregate `READY`.

## When to use and not use

Use this only when an approved design specification and implementation plan
already exist and need a readiness review before SDD or plan execution.

Do not use it to write the initial design or plan, review implementation code
or a pull request, verify a release, proofread, or generally improve
documentation. The skill does not start SDD unless the outer request includes
implementation.

## Supported hosts

pre-sdd-review: Codex supported; other hosts not_measured.

Only Codex has measured support for isolated read-only review and repository
inspection. A portable Markdown package is not evidence that another host has
the same runtime behavior.

## Install

Install from the public GitHub path with `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

Do not replace an existing install without first checking the exact target.

To keep local receipts, install the optional CLI separately from an inspected
skill copy. `--bin-dir` must be an existing directory already intended for
`PATH`; inspect that exact target with `ls -ld` before running the installer.
Never pipe a remote script into a shell.

```bash
ls -ld "$HOME/.local/bin"
python3 skills/pre-sdd-review/evidence/install.py --bin-dir "$HOME/.local/bin"
pre-sdd-review-evidence --version
```

Codex, Claude Code, Cursor, and Grok all call the same
`pre-sdd-review-evidence` command when it is available. CLI portability and
semantic review-host support are separate contracts.

## First call

Pass the plan path as the primary input and name the design document as well:

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

Use `review-only` only when you want the first review verdict without repair;
its invocation is in Expected result.

During resolution, the plan path is primary and its `**Spec:**` field selects
the resolved design specification. A separately supplied design path does not
override that authority.

## Expected result

In default mode, a fresh read-only reviewer returns evidence-backed findings,
then the controller obtains a scoped re-review. `review-only` changes nothing
and returns the first review verdict.

If a repair changes a schema, type, state transition, conditional mutation,
task interface, verification meaning, or data boundary, the controller records
that impact for direct consumers and adjacent tasks. The next reviewer checks
that original findings closed and that this bounded impact still holds.
Wording or scalar value corrections skip this map.

There are at most two repair passes. The final verdict is one of:

- `READY`: no unresolved issue requires invention or permits a materially
  wrong implementation to pass planned evidence.
- `REVISE`: a material, repairable document defect remains.
- `BLOCKED`: required input, authority, or repository evidence is unavailable.

A focused second reviewer is conditional, not routine: framework or runtime
removal; schema migration or data deletion; authentication, authorization, or
security boundaries; public/private data-boundary changes; or external side
effects such as publishing, billing, messaging, or production mutations.
Changing either document invalidates its fingerprints and requires re-review.
A repository change also requires re-review when it changes evidence for a
path, command, interface, or blast-radius claim.

`REVISE` and `BLOCKED` return a short packet of unresolved findings and the
next document scope. A new product decision is always `BLOCKED`.

When a compatible local CLI is present, the controller calls `start` before
semantic review, calls `finish-review` after the final verdict, and prints one
`Evidence: recorded; run_id=<run-id>` line. If the command is unavailable,
incompatible, or denied by permissions, the verdict continues unchanged and
the controller prints `Evidence: not_recorded; reason=<code>`. It hands the
local `run_id` only to an explicitly combined SDD request and uses
`record-outcome` only when downstream work reaches a terminal status. The same
evidence lifecycle applies in default and `review-only` mode.

The complete local command surface is `start`, `finish-review`, `abandon`,
`show`, `pending`, `doctor`, `resolve`, `record-outcome`, `summary`,
`candidates`, and `prune`. Follow each `--help` and the
[evidence CLI guide](evidence/README.md) for exact arguments.

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

```text
$pre-sdd-review review-only docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

## Safety and privacy

Reviewers are read-only. The `Contract` list in Expected result is the sole
automatic-mutation authority. Accepted ADRs, approved visual authority,
application code, tests, configuration, generated artifacts, and unrelated
documentation require a separate product decision. A correction that needs a
new approved product decision returns `BLOCKED`.

Provider-free fixtures must not store user documents, private prompts, or full
model responses.

Receipts remain local under `~/.pre-sdd-review/`; only a non-empty absolute
`PRE_SDD_REVIEW_HOME` may override it. `review.json` has a 16 KiB soft and
32 KiB hard limit, `outcome.json` has a 4 KiB soft and 8 KiB hard limit, and a
completed run has a 40 KiB hard limit. Even bounded reasons and findings must
not contain source text, paths, prompts, transcripts, or credentials; use a
short paraphrase.

Create-only storage provides atomicity and consistency for cooperating local
clients, not a signed audit log resistant to malicious local tampering.
Structured downstream observations, assessment basis, and confidence are
observer-supplied. The CLI derives `good`, `false-ready`, `noisy`, and
`prevented-rework` deterministically from those observations. These inputs and
derived labels are self-improvement evidence, not objective or audit-grade
proof. Before `record-outcome`, encode every known dispute and uncertainty in
the single outcome input. Use `disputed_findings` for finding disputes; encode
uncertainty in the observations, basis, and confidence so the derived
assessment remains `inconclusive`. After the create-only outcome is recorded,
schema 1 cannot correct or amend it. An erroneous recorded outcome is an
uncorrectable residual risk, not a correction path. Candidate thresholds are
inspection heuristics, not authority for automatic skill mutation, automatic
quality judgment, or client/model ranking.

## Verification

Provider-free verification proves package, instruction, and fixture contracts
only. It does not prove live review quality or equivalent runtime support on
another host. Optional live checks are local and explicit, may be billable,
and are never required by CI.

The shared CLI has measured the current native macOS path and provider-free
portable construction only. Linux and native Windows remain `not_measured`
until the evidence and installer stages actually pass under Python 3.11 on
those systems; wrapper tests elsewhere do not imply native support.

## Update and remove

Before updating or removing, inspect the exact installed target. The version
source is `release.toml`; `SKILL.md` `metadata.version` is a verified copy.
Do not delete a parent `skills` directory or a home directory.

Before removing the CLI launcher, inspect `command -v
pre-sdd-review-evidence` and the exact file. Removing the launcher does not
delete receipts. To preserve repository identity, back up the whole evidence
root including `identity.key` and `config.json`. Receipt removal is a separate
operation: inspect `prune --dry-run`, then explicitly confirm the same
selection.

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [Testing](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [Compatibility](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [Release](../../docs/maintainers/products/pre-sdd-review/release.md)
