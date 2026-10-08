# How should decision context survive completed work?

Decision date: 2026-10-09. Recorded on: 2026-10-09.
Related work: repository documentation and verification.
Outcome: minimal recording workflow adopted; ongoing usefulness unmeasured.
Evidence basis: the user requested durable insight from creation, implementation,
choices, and deletion, and approved this approach in the current task. This is a
summary of the approved scope, not a published raw conversation.

## Starting problem

Working plans were deleted on completion, while changes remained recoverable in
Git. Research and skill practices already held valuable evidence, but readers
needed a way to find intent, rejected choices, and retirement reasons across them.
The recent retirement case demonstrates a specific missing reason, not proof that
all prior work lacked records.

## Conditions

Keep the system lightweight and in the repository. Preserve existing work and
current product boundaries. Internal documents are English. No new skill, service,
provider call, or legacy runtime is needed. Historical facts, later interpretation,
and personal preferences must remain distinguishable.

## Alternatives and choice

- Git and changelogs alone: inexpensive, but require knowing which revision to
  inspect and do not ensure intent or outcomes are written down.
- Repository case records with evidence links: selected so reasoning can be
  reviewed beside changes and survive product deletion.
- An external notes system as the primary record: left out to avoid separating
  decision history from code and verification. Later publication can reuse cases.

Start with Markdown and the existing link checker. Defer a schema, dashboards,
automatic reason inference, and missing-case enforcement until actual use shows
a need. No additional approval procedure is introduced.

## Implementation approach

The [learning index and workflow](../README.md) owns when and how to record a case.
Three historical cases cover an interaction change, workflow design, and retirement.
This fourth case records the adoption decision itself. AGENTS.md connects recording
to normal work; history cleanup first preserves significant decisions. Documentation
indexes and the contribution guide provide discovery paths. The existing Markdown
collector includes nested learning documents in provider-free link checks.

## Observed result

Initial reconstruction recovered explicit design trade-offs for two cases and a
documented absence of rationale in the reviewed retirement commits. It did not
recover the user's private deletion reasoning. No live model quality claim follows
from the checks below.

Verification on 2026-10-09:

- Local public-document suite: 65 tests passed, including a regression that detects
  a broken link in a nested learning case and passes after the target is supplied.
- All 11 historical commit/file citations resolved against local Git objects.
  Current documentation links and `git diff --check` passed.
- `python3 scripts/verify.py` passed on macOS with Python 3.14.7 in a disposable
  clone containing tracked files plus this change, staged for index-based package
  checks: 641 unit tests, 35 Korean and 32 image cases, mutation checks, a provider-free
  live-runner dry-run, and compilation. No provider calls ran.
- The original checkout's full command stopped before tests because ignored `.pyc`
  files kept five retired product directories present. Those files and an unrelated
  untracked research folder were left untouched; the disposable clone excluded them.
- A stock macOS Python 3.9 helper-test attempt could not import the existing registry
  module because it requires `tomllib`. This does not establish Python 3.9 execution
  support. No installed product runtime changed.

The full run preceded the final documentation-only scope clarification and this
verification note. The final focused document/governance suite passed 80 tests;
code and test bytes match the full-run snapshot.

## Disposition

Adopt the small workflow and review its usefulness after the next three significant
tasks, as described in the [review criteria](../README.md#review-and-verification).
There is no scheduled background job. Simplify recording if it is repeatedly deferred;
add tooling only for observed retrieval or consistency problems.

## Reusable lesson

Hypothesis to assess in subsequent work: a short case attached to normal task closure
can preserve usable reasoning without retaining every plan or conversation. This
is an approved process choice, not yet a measured skill-writing rule.
