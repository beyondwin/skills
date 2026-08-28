# Pre-SDD Review Skill Design

**Status:** Approved on 2026-08-29

**Scope:** Add `pre-sdd-review` as a fourth independent product. The skill
reviews an approved design specification and its implementation plan against
each other and against repository reality immediately before
`superpowers:subagent-driven-development`. Its default behavior is to review,
repair the documents, and re-review them.

**Out of scope:** Writing the first design or plan, changing application code,
reviewing an implementation diff, invoking SDD without an explicit outer
request, editing accepted product decisions, publishing a release, catalog
adoption, and support claims for unmeasured hosts.

## Context

The Superpowers workflow already performs useful local checks while writing a
design and plan. Brainstorming checks its own design for ambiguity and
contradiction, while writing-plans checks spec coverage, placeholders, and
interface consistency. SDD later reviews each implementation task for spec
compliance and code quality.

The remaining gap is between those stages. A document can be internally
consistent while still being wrong about the repository: a path may not exist,
an extension point may be inferred, a removal may have a wider blast radius,
or a weak test may allow an incorrect implementation to pass. Asking several
agents to look for “every blind spot” can expose some of these problems, but it
also produces overlapping findings, stylistic noise, and manufactured issues
when no finding quota or authority model is defined.

`pre-sdd-review` is therefore a narrow readiness gate rather than another
general review framework. It asks whether an SDD worker can execute the plan
without inventing an unrecorded decision and whether the planned evidence can
reject a materially wrong implementation.

## Goals

1. Trace every binding design decision into an executable plan task.
2. Verify paths, commands, extension points, collisions, blast radius, and
   baseline assumptions against the current repository.
3. Find omissions, contradictions, ordering errors, and verification gaps
   without generating stylistic or optional findings.
4. Make review, document repair, and scoped re-review the default invocation.
5. Keep independent reviewers read-only and give document mutations to the
   controlling agent.
6. Produce a stable `READY`, `REVISE`, or `BLOCKED` handoff with document and
   repository fingerprints.
7. Integrate as a registered, independently installable product without
   modifying cached or upstream Superpowers files.

## Non-goals

- Do not replace `superpowers:brainstorming` or `superpowers:writing-plans`.
- Do not start implementation or edit source code.
- Do not perform code review, security review, release readiness, prose polish,
  or general architecture ideation.
- Do not turn repository reality into product authority. Existing code may
  reveal a conflict but cannot silently override an approved decision.
- Do not require a minimum number of findings.
- Do not add a runtime script that pretends semantic document review is a
  deterministic parser problem.
- Do not add the product to the immutable `v2.0.0` catalog or publish it.

## Product identity

| Surface | Value |
| --- | --- |
| Product ID | `pre-sdd-review` |
| Display name | `Pre-SDD Review` |
| Directory | `skills/pre-sdd-review/` |
| Frontmatter `name` | `pre-sdd-review` |
| First public target | `1.0.0` |
| Tag prefix | `pre-sdd-review-v` |
| Supported host at launch | `codex` |
| Explicit invocation | `$pre-sdd-review` |

Other hosts remain `not_measured`. A portable Markdown package shape is not
evidence that another host can provide isolated subagent review or the same
repository inspection behavior.

## Activation boundary

Use the skill only when all of these are true:

- an approved design specification exists;
- an implementation plan exists;
- implementation has not started, or the user explicitly asks to reset the
  review against documents before resuming;
- the requested purpose is readiness review before SDD or plan execution.

Do not activate it for initial design writing, initial plan writing, a source
diff, a pull request, release verification, proofreading, or a general request
to improve documentation.

Explicit invocation is the recommended entry point. Implicit activation is
allowed only when the request clearly says that existing design and
implementation-plan documents must be reviewed before SDD.

## Inputs and resolution

The invocation must resolve:

1. one implementation plan path;
2. the design path named by the plan's `**Spec:**` field;
3. accepted ADRs and other authorities explicitly referenced by those files;
4. the repository root and current Git `HEAD`;
5. any user-approved visual or product authority named in the documents.

If the plan has no resolvable `**Spec:**` path, the result is `BLOCKED`; the
skill does not guess among nearby files. Missing optional context is reported
only when it prevents a material readiness decision.

## Authority order

Conflicts are interpreted in this order:

1. the user's approved direction and referenced visual authority;
2. accepted ADRs and other explicitly binding decision records;
3. the approved design specification;
4. the implementation plan, which must argue from the design;
5. current repository reality.

Repository reality is evidence about feasibility, integration, and blast
radius. It is not permission to narrow or replace an approved product decision.
When a repair would require a new product decision, the skill preserves the
conflict and returns `BLOCKED` instead of inventing authority.

## Default workflow

Calling `$pre-sdd-review` defaults to automatic improvement:

```text
resolve inputs and fingerprints
  -> dispatch one fresh read-only reviewer
  -> synthesize BLOCKER and IMPORTANT findings
  -> repair only the design and implementation-plan documents
  -> send the changed sections and original findings for scoped re-review
  -> repeat once when an evidence-backed document defect remains
  -> emit READY, REVISE, or BLOCKED
```

The default permits at most two repair passes. This prevents an open-ended
review loop while allowing the controller to fix interacting document defects.
If a material issue remains after the second repair pass, return `REVISE` with
the unresolved evidence. Do not lower its severity merely to finish.

The user may explicitly request `review-only`. In that mode no file is changed
and the first review directly produces a verdict.

## Mutation boundary

Independent reviewers are always read-only. They report evidence and the
smallest sufficient document correction but never edit files.

In default automatic-improvement mode, the controlling agent may edit only:

- the resolved design specification;
- the resolved implementation plan;
- a directly referenced proposed decision record when the document explicitly
  delegates that non-product decision to the plan.

Accepted ADRs, user-approved visual authority, application code, tests,
configuration, generated artifacts, and unrelated documentation are not
auto-edited. A repair must preserve approved scope and may not introduce a new
feature, dependency, host claim, or product decision.

## Review protocol

### Pass 1: authority trace

- Map every approved decision and global constraint to the design section that
  records it and the plan task that implements it.
- Detect authority drift, silent narrowing, unsupported expansion, and a plan
  that treats an exploratory option as accepted.
- Confirm that the plan's `**Spec:**` points to the reviewed design.

### Pass 2: repository grounding

- Verify named paths, symbols, commands, test runners, and versions.
- Inspect the actual extension point instead of assuming one from a filename.
- Search for collisions and consumers of moved, removed, or renamed surfaces.
- Compare the described blast radius with repository references.
- Run only safe, read-only baseline checks necessary to test a document claim.
- Preserve pre-existing dirty state and report when it makes a claim
  unresolvable.

### Pass 3: cross-artifact consistency

- Find design requirements with no plan task and plan work with no design
  authority.
- Check task order, producer/consumer interfaces, exact names, types, paths,
  state transitions, and migration order.
- Check that destructive or irreversible steps have precise targets and safe
  prerequisites.
- Reject placeholders, implied work, and steps that require an implementer to
  choose among materially different designs.

### Pass 4: verification falsification

- For each acceptance claim, construct at least one materially wrong
  implementation that the proposed test might still accept.
- Require the plan to close that gap when the counterexample is plausible.
- Distinguish static contract evidence, unit behavior, integration behavior,
  browser/device behavior, and external side effects.
- Never claim that one evidence class proves another.

### Pass 5: readiness verdict

The reviewer returns only material findings and one verdict:

- `READY`: no unresolved finding requires invention or permits a materially
  wrong implementation to pass the planned evidence;
- `REVISE`: the documents contain a repairable material defect;
- `BLOCKED`: required authority, input, or repository evidence is unavailable
  and cannot safely be invented.

Zero findings is valid. The reviewer must not manufacture findings to satisfy a
quota.

## Conditional second reviewer

One fresh reviewer is the default. A second focused risk reviewer is dispatched
only when the documents include one of these conditions:

- framework or runtime removal;
- schema migration or data deletion;
- authentication, authorization, or security boundaries;
- public/private data-boundary changes;
- external side effects such as publishing, billing, messaging, or production
  mutations.

The second reviewer examines only the triggered risk class. It does not repeat
the complete review. The controller deduplicates findings by evidence and
consequence before repair.

## Finding contract

Only two severities are allowed:

- `BLOCKER`: SDD cannot safely start because authority, feasibility, ordering,
  or acceptance evidence is materially invalid or missing.
- `IMPORTANT`: SDD could start, but the current documents create a credible
  wrong implementation, avoidable rework, or unverifiable acceptance claim.

Each finding has this shape:

```text
ID: PSDR-001
Severity: BLOCKER | IMPORTANT
Class: authority-drift | repo-reality | coverage | ordering | verification-gap
Location: exact document path and heading or line
Evidence: repository or cross-document fact
Consequence: concrete implementation failure
Minimal document fix: smallest authority-preserving correction
```

Style, taste, optional refactoring, generic best practice, and speculative
future work are excluded.

## Freshness contract

Every final report records:

- repository-relative design path and SHA-256;
- repository-relative plan path and SHA-256;
- Git `HEAD`, or `unborn` when no commit exists;
- whether the worktree was clean or dirty at review time;
- review timestamp and final verdict.

Any content change to either document invalidates the earlier `READY` verdict.
A Git change outside those files does not automatically invalidate readiness,
but the review must be rerun when it changes a path, command, interface, or
blast-radius claim used as evidence.

## SDD handoff

`READY` prints the exact design and plan paths plus their fingerprints. The
skill stops there by default. It invokes SDD only when the outer user request
explicitly asks for review followed by implementation. In that combined flow,
the SDD worker must receive the final repaired files, not the pre-review copies.

## Package architecture

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
└── references/
    └── reviewer-protocol.md

tests/products/pre-sdd-review/
├── cases.json
├── test_contract.py
└── fixtures/
    ├── ready/
    ├── missing-coverage/
    ├── false-verification/
    └── runtime-removal/

docs/maintainers/products/pre-sdd-review/
├── contract.md
├── testing.md
├── compatibility.md
└── release.md
```

No runtime script is included in `1.0.0`. The skill performs semantic review
through repository inspection and fresh reviewer reasoning. Provider-free
tests validate package identity, activation boundaries, workflow instructions,
finding schema, fixtures, and documentation consistency; they do not claim to
measure live review quality.

## Repository integration

The product is registered in `products.toml` with Codex as its only measured
host and these stages:

```toml
verify_stages = ["product-contract", "pre-sdd-review-contract", "python-compile"]
```

The same change updates the root product lists, Korean and English user
installation/compatibility/safety/verification documentation, maintainer
navigation, repository contract tests, and verification-stage registration.
Registration does not add the product to the immutable catalog and does not
publish a release.

## Verification cases

The deterministic contract suite must include:

1. a complete design and plan that produce `READY` without manufactured
   findings;
2. a design requirement omitted from the plan;
3. a nonexistent path or command;
4. an inferred extension point or missed collision/blast radius;
5. a smoke test that accepts a materially wrong implementation;
6. a task-order or producer/consumer interface mismatch;
7. framework removal that activates the focused risk reviewer;
8. explicit `review-only` that forbids mutation;
9. default invocation that requires review, repair, and re-review;
10. near misses for initial spec writing, plan writing, code review, and release
    review;
11. a changed document hash that invalidates the prior result.

The product-level gate is:

```bash
python3 scripts/verify.py --skill pre-sdd-review
```

Repository closeout additionally requires:

```bash
python3 scripts/verify.py
git diff --check
```

## Success criteria

The design is satisfied when a user can invoke `$pre-sdd-review` with existing
design and implementation-plan documents and receive an evidence-backed,
automatically repaired, freshly re-reviewed readiness result; when the skill
cannot silently change approved authority or implementation code; when clean
documents can pass with zero findings; and when the repository verifies the
new product without claiming unmeasured live or cross-host behavior.
