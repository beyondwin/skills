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

## Supported hosts

pre-sdd-review: Codex supported; other hosts not_measured.

Codex is the measured host today. Other hosts are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

In Codex, pass the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

The local evidence recorder is not installed.

```bash
python3 "<skill-root>/evidence/evidence.py" --version
```

Shared install steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-codex.md).

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

Receipts stay local under `~/.pre-sdd-review/`. Local file storage is not a
signed audit log. `outcome` and `summary` are in the
[evidence README](evidence/README.md).

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/pre-sdd-review/release.md)
- [evidence README](evidence/README.md)
