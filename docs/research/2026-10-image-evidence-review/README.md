# Evidence-based image review redesign

Started: 2026-10-23. Status: development in progress; no improvement claim yet.

The [preceding repair](../2026-10-image-review-repair/README.md) retained
correction-condition preservation but failed to improve count, occlusion and
false-rejection errors. The user requested a redesigned review method, actual
Grok comparisons, further improvement until useful, and incremental commits.
The [decision case](../../learning/cases/2026-10-23-image-evidence-review.md)
records the alternatives and adoption decision.

## Direction and target

The skill must change acceptance decisions, not merely lengthen prompts or make
more image calls. Separate three responsibilities: interpret the original
requirements, record what the image shows, and decide whether that evidence
violates a requirement. Required counts and complete visibility remain different.
Object parts, background surfaces and independent props must not be conflated.
Every rejection needs a requirement and localized image evidence; an unresolved
critical condition remains unverified, not an invented failure or pass.

Candidate A uses an instance inventory before count comparison, an explicit
foreground-boundary check, and a check of the benign interpretation before a
candidate is rejected. Aesthetic ranking happens only among eligible candidates.
It adds no provider, helper, compulsory second agent, or image-generation budget.
The previous crop-heavy variants are not revived.

## Comparison fixed before candidate results

The control is the complete 2.1.5 product at commit `6e9eef6`. Both arms use a
frozen complete payload, isolated fresh Grok homes, the same CLI 1.0.67 executable,
requested `grok-4.7/high`, identical original requirements, anonymous source
images, report contract and budget. Actual model and effort come from native
history. No generation is allowed in review sessions. Input and delivered image
hashes, payload integrity, normal completion and credential cleanup are checked.

The 22 images from the prior historical and transfer comparisons are now all
development data. They are grouped by scene while preserving selection pools;
each session has at most 30 turns and 900 seconds. Candidate development needs
at least 20/22 correct eligibility decisions, fewer count and occlusion errors,
no increase in false accepts or false rejects, and no regression in pool
decisions. All-failing pools must be held. Missing results and unresolved labels
do not earn correct decisions; rejecting or holding a known valid candidate is
a false rejection. Each revision and failed result is retained.

Clarified before the first completed development verdict: the count domain
includes total-object counts and required visible-part counts; both subtypes
are also reported separately. If the concurrent control makes zero errors in a
stratum, the candidate must retain zero errors there. Improvement below zero is
impossible, and a ceiling tie is not described as improvement. The other gates
remain unchanged.

After a development candidate is frozen, generate 24 new originals across four
scene families, with one image call each and no corrective retry. Each family
includes three intended valid variations and three intended contrasts: incorrect
count, required-visibility failure, and a prohibited independent object. Intent
is not ground truth. Two independent reviewers see anonymous originals and
original acceptance conditions, without source prompts, version labels, prior
verdicts or expected defects. Their agreement defines clear labels; disagreements
remain separately reported, with all originals retained in the denominator.

The locked control and candidate review the same new images in two fresh
repetitions with equal budgets and counterbalanced arm order. Repetitions are
not independent images. Report each repetition, agreement, all candidate
decisions, false accepts, false rejects, count/visibility/extra-object strata,
all-failing and eligible selection pools, calls, turns, time and reported cost.
Reported orchestration cost may omit image billing.

The prospective fresh-image target is at least 90% correct on clear labels in
each repetition, no increase in either false accepts or false rejects or in any
defect stratum, and at least two net additional correctly classified unique images
against the control in each repetition. Both normal-candidate retention and
failure detection must improve somewhere across development and fresh images.
Unverified cases cannot supply an improvement. Report paired discordances and
an exact paired test; a small effect is not statistical or general superiority.
If the holdout informs another revision, it becomes development data and a new
untouched comparison is required. Do not reuse it as an independent final test.

Finally rerun the original generation tasks under the original two-image-call
limit. Inspect every generated original with blinded reviewers, preserve
correction conditions, and require no loss in usable delivery or increase in
unnecessary corrections versus the control. Successful review is distinct from
better aesthetics; a quality tie cannot be called an aesthetic win.

## Evidence and verification boundary

Private prompts, generated images, native histories, isolated homes and raw
provider receipts stay outside Git in `/tmp/image-workbench-review-20261023`.
Only aggregate methods, results and safe decision records are committed.
Offline contracts establish packaging and authorization behavior, not visual
accuracy. Product and full repository checks follow the final runtime change;
they are separate from the live comparisons above.
