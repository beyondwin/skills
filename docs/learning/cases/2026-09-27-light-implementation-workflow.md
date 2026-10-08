# How much orchestration should an implementation skill add?

Decision date: 2026-09-27, with revisions through 2026-10-07.
Recorded on: 2026-10-09. Related work: waygent.
Outcome: a lightweight workflow was built, evaluated, and revised; later retired.
Evidence basis: retrospective synthesis of committed research and product changes.

## Starting problem

The [design and evaluation record](../../research/2026-09-waygent-eval/README.md)
links the design to an agent-workflow comparison, the user's earlier workflow
comparison, and independent model proposals. The aim reflected in those sources
was to retain useful implementation and review structure with less orchestration
overhead. This is a synthesis of the record, not a verbatim statement of intent.

## Conditions

The research's inclusion table explicitly attributes tests-first implementation
and a review per task without re-review to user requirements. Its measured tasks
and models bound the conclusions; the simple initial job did not represent every
large implementation plan. Progress recovery and a main agent's judgment about
review findings mattered alongside hidden-test scores.

## Alternatives and choice

- Plain execution provided the baseline and nearly matched structured workflows
  on the initial task, while retaining a particular hidden defect.
- Final-review-only was measured as cheaper at similar quality on that task.
  The default still retained review per task, as requested. Measurement and product
  preference therefore supported different parts of the final choice.
- The selected design used a fresh implementer per task, a short brief plus shared
  guide, one review and fix, and a final full review.
- Per-task report files, re-review loops, parallel implementers, and repeated human
  confirmations were left out. These are recorded exclusions, not missing features
  inferred from the final code.

## Implementation approach

The [initial implementation](https://github.com/beyondwin/skills/commit/6a99573fdc991076a7b2dc3649241f0cdc8a2414)
used progress records and commit trailers for resume, and one written cause and
retry for failure. Later revisions changed record placement and model routing;
the [routing record](../../research/2026-09-waygent-eval/model-routing.md) owns that
history. These historical mechanisms are not instructions to run the retired skill.

## Observed result

The research reports 22 initial runs across 13 condition-model cells on one job,
followed by separate app and routing studies. It records both gains and limits:
finding a defect did not ensure the main agent accepted and fixed it, and the
cheaper final-only result was bounded to the measured task.

One later [decision probe and resulting change](https://github.com/beyondwin/skills/commit/3c4cf9ac02a426bd399538d602970dd80784503f)
is particularly reusable. Added wording failed to stop incorrect reversals of a
correct ruling; stronger wording also parked a correct task. The rule was dropped
and the remaining failure mode acknowledged. Full measurements stay in the
[results](../../research/2026-09-waygent-eval/results.md), not duplicated here.
No experiment was rerun for this reconstruction.

## Disposition

The skill was removed on 2026-10-09. Its creation and measured revisions do not
establish why the user later removed it. That separate question is recorded in
the [retirement case](2026-10-09-retire-workflow-skills.md). Research, fixtures, and
design lessons remain; this record does not recommend reinstalling it.

## Reusable lesson

Inferred now: evaluate orchestration components separately and retain the reason
for each choice, including preferences that a small benchmark cannot settle.
A stricter instruction must be checked for newly blocked correct work as well as
the failure it targets. See [the insight](../insights.md#more-procedure-needs-a-specific-benefit).
