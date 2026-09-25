# Pre-SDD Review

[한국어](README.md)

## Purpose

Right before SDD (plan execution), check that an approved design and its
implementation plan agree with each other and can run in the repository as it
is now. The default flow is **review -> repair documents -> scoped re-review**.
It asks one question: can an implementer follow the plan without inventing a
missing product decision?

The plan path is primary. The design is the document the plan's `**Spec:**`
field points to, the resolved design specification. If that path cannot be
resolved, the skill returns `BLOCKED` instead of guessing among nearby files.

- A verdict-bearing invocation reviews one plan; results for several plans are
  never merged into one `READY`.
- When the outer request names two or more plans or asks for it explicitly, a
  verdict-less shared-file ledger pre-pass runs once before the first
  verdict-bearing invocation. The ledger lists the files several plans touch.
- If a plan names a required base (branch, ref, or commit) that cannot be
  resolved or is not an ancestor of the current `HEAD`, it is `BLOCKED` before
  review.

## When to use and not use

- Use it when an approved design and implementation plan already exist and SDD
  or plan execution is next.
- Do not use it to write a first design or plan, review code or a pull
  request, check release readiness, or proofread documents.
- The skill does not start SDD unless the request includes implementation.

## Supported hosts

pre-sdd-review: Codex supported; other hosts not_measured.

Codex is the only supported host today. Other hosts have not been checked. See
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

In Codex, pass the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

The optional evidence recorder is not installed separately. Run it from the
skill folder.

```bash
python3 "<skill-root>/evidence/evidence.py" --version
```

Other install steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-codex.md).

## First call

Pass the design and plan paths.

```text
$pre-sdd-review docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

Even when you pass a design path, the plan's `**Spec:**` field decides which
design is reviewed.

Use `review-only` only when you want the first verdict without document
repair; the example is under Expected result.

## Expected result

### One run

1. A fresh read-only reviewer finds problems (findings), each with evidence.
2. The controller repairs only the resolved design specification, the
   implementation plan, and the shared-file ledger. A fresh reviewer then
   re-checks only what changed (closure). Closure requires the repair diff.
3. There are at most two repair passes. If afterward no more than two original
   `IMPORTANT` findings remain, each fixable at one site, the same call repairs
   them once more and re-checks only those.

If the first review finds nothing, the skill skips repair and returns `READY`.
But if an earlier plan's repair changed files this plan reads, closure still
runs even with zero findings.

The ledger is derived evidence, not authority: when it disagrees with a plan's
`Files:`, the plan wins and the ledger is rebuilt. A repair that changes a
schema, type, state transition, conditional mutation, task interface,
verification meaning, or data boundary records its direct consumers and
adjacent tasks for the re-review. Wording and scalar fixes do not need that
impact map.

`review-only` changes nothing and returns the first verdict.

```text
$pre-sdd-review review-only docs/history/specs/<design>.md docs/history/plans/<plan>.md
```

### Verdicts

- `READY`: implementation can start without inventing a missing decision.
- `REVISE`: a material, repairable document defect remains.
- `BLOCKED`: required input, authority, or repository evidence is missing, or
  a new product decision is needed.

A run whose last action was a repair is never `READY`, and an open `BLOCKER`
makes it `BLOCKED`. A `READY` report prints the final document paths and
fingerprints (SHA-256), plus the observation anomalies that `finish` returned
as an `Anomalies:` line. Anomalies do not change the verdict. Repairs that keep
product intent are applied without asking; only decisions that need the user
are asked, all at once.

### Next run

The skill never re-runs itself after `REVISE` or `BLOCKED`. When you call it again:

| Since the last verdict | This call |
| --- | --- |
| Documents, `HEAD`, and request all unchanged | No new review; the previous handoff (remaining-problem list) is reused |
| It was `REVISE`, or `BLOCKED` on a user decision the documents now record, and only the design, plan, or ledger changed | Continues from closure with no new discovery. Needs a recorded run for this plan |
| `BLOCKED` on a user decision still unanswered | No reviewer; shows the same question again and prints `Evidence: not_recorded; reason=previous-decision-checkpoint` |
| Anything else (other files changed, full re-review asked, no record) | A fresh review from the start |

Only a `full` run's handoff, or that of a `degraded` run whose only reason is
`focused-role-not-obtained`, is reused; any other `degraded` or `blocked`
run's handoff is never reused. A `degraded` run is one that could not get a
fresh reviewer for every role, or reused one. After three `BLOCKED` runs in a
row on new user decisions, the design is sent back to settle the remaining
decisions at once.

### Several plans and extra reviewers

Discoveries of split plans may overlap; repairs do not. A preceding `BLOCKED`
plan does not stop later discovery. If `HEAD` moves off the one recorded at
the start, no `READY` is returned against it.

A focused second reviewer is added only for risky changes, and only in a call
that runs discovery: runtime removal, schema migration or data deletion,
authentication or security boundaries, public/private data-boundary changes,
or external side effects such as publishing, billing, messaging, or production
mutation. A reviewer is never reused for another plan.

Changing either document invalidates its fingerprints and any earlier `READY`,
so it needs a new review. A Git change outside the documents does the same
when it alters evidence for a path, command, interface, or blast-radius claim.

### Optional recorder

Compatibility is a handshake match: `skill_name=pre-sdd-review` and `schema=4`,
exactly. See the [evidence README](evidence/README.md) for the canonical
line's exact bytes.

- With a compatible recorder, the controller reads `summary` for this plan's
  past runs, calls `start` before review and `finish` after the final verdict,
  and prints `Evidence: recorded; run_id=<run-id>`. The `run_id` stays out of
  user documents.
- An unfinished run for the same plan, or a call that ends early, is closed
  with `abandon`.
- If the recorder is missing, incompatible, or denied by permissions, review
  continues and prints `Evidence: not_recorded; reason=<code>`. The verdict
  does not change.

Records stay local under `~/.pre-sdd-review/`. Local file storage is not a
signed audit log. `outcome` (a label added after SDD) and `summary` are in the
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
