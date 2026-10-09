# 0.5.0 personal-use decision, frozen before calls

## Decision change

The earlier four-of-six preference rule is retained as a failed experiment, not
lowered or relabeled a pass. It was the implementing assistant's proxy for personal
readability, not a user-selected requirement. The user now explicitly requests
familiar everyday technical language and delegates the practical quality judgment
to the implementing assistant. Model preference has not established superiority;
that earlier objective remains unfulfilled.

0.5.0 is a separate personal configuration decision. Selection of a personal writing
style can be justified without claiming it is generally better than a competent
baseline. The rubric must describe this reader explicitly, rather than letting a
reviewer assume an on-call engineer already knows every operations term. Previous
comparisons and rejected versions remain visible; none are rescored under this rule.

## Changes and test

Add a short connected Korean prose example that selects the facts needed to answer
the question. Distinguish descriptive English in notes from identifiers that must
be copied. Check residual English prose before returning. Correct the style example's
source assumption to explicitly establish the disabled state. Preserve the 0.4.3
meaning guards and operational names beside their explanations.

Run all eight known development cases with Codex, Opus and Grok. These are not new
holdouts. Then audit each draft without showing version or skill instructions:
Codex audits Opus drafts; Opus audits Codex/Grok drafts. Grok remains a writer in
this study. The reviewer assignment is fixed before calls. Different providers do
not turn a model audit into human validation.

Personal acceptance requires all eight source comparisons to have no material error
and no unresolved blocking reading obstacle, followed by three native regressions
and one native installed smoke with the exact payload. The implementing assistant
must independently read all outputs and adjudicate reviewer claims against the source.
Preserve all raw judgments, including false positives and minor awkwardness. Do not
replace votes in an old comparison. A confirmed material error rejects this candidate.

Maximum 20 calls: 8 writes, 8 audits, 3 native regressions, 1 installed smoke. No
automatic retry. Do not install before writer/audit/regression acceptance. Back up
0.2.2, install only this personal skill and restore the backup on smoke failure.
Report this as a personal usability acceptance, never a passed comparative criterion,
statistical superiority, measured vocabulary frequency or human comprehension gain.
