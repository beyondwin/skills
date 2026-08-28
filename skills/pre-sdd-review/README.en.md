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

### Contract

- `primary-input`: `plan-primary`, `spec-resolves-design`
- `editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`
- `review-only`: `no-mutation`
- `repair-flow`: `review-repair-scoped-re-review`
- `repair-passes`: `at-most-two`
- `verdicts`: `READY`, `REVISE`, `BLOCKED`
- `second-reviewer`: `conditional-only`
- `risk-triggers`: `framework-runtime-removal`, `schema-data-deletion`, `auth-security-boundary`, `data-boundary-change`, `external-side-effects`
- `freshness`: `fingerprints`, `content-change-invalidates`
- `sdd`: `outer-request-implementation-only`

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

## Verification

Provider-free verification proves package, instruction, and fixture contracts
only. It does not prove live review quality or equivalent runtime support on
another host. Optional live checks are local and explicit, may be billable,
and are never required by CI.

## Update and remove

Before updating or removing, inspect the exact installed target. The version
source is `release.toml`; `SKILL.md` `metadata.version` is a verified copy.
Do not delete a parent `skills` directory or a home directory.

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [Testing](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [Compatibility](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [Release](../../docs/maintainers/products/pre-sdd-review/release.md)
