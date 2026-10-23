# First-image visual direction, 2026-10-23

Status: complete. The proposed change is not adopted; image-workbench remains 2.1.7.
The original protocol below was frozen before all eight calls.


## Outcome

The Grok-only candidate did **not** improve first-image quality. Two reviewers
agreed on one candidate win and two losses; the environment preference disagreed.
Mean craft was 4.296875/5 ordinary versus 4.25/5 candidate (difference -0.046875;
request-level paired standard error 0.142921). This fails the frozen improvement
threshold and is not evidence of a general performance difference.

| New request | Ordinary craft | Candidate craft | Pairwise finding | Critical compliance |
| --- | ---: | ---: | --- | --- |
| Speaker product photo | 4.4375 | 4.25 | Ordinary preferred by both | Ordinary pass; candidate low view unverified by both |
| Snail editorial illustration | 4.0625 | 4.3125 | Candidate preferred by both | Both pass |
| Sea-cave environment | 4.25 | 4.375 | Reviewers disagree | Both pass |
| Utensil still life | 4.4375 | 4.0625 | Ordinary preferred by both | Both pass |

The snail's darker body separated more clearly from the pot. That single improvement
is not a transferable rule: the generated appendix did not explicitly prescribe the
successful colour separation, so it cannot establish the cause. Ordinary utensils
had gentler lighting, more even spacing and less distracting surface detail. The
speaker candidate looked down onto the grille; its requested low view remained
uncertain. The cave comparison reflects different preferences for painterly
asymmetry and a quieter layered central scene. Preserve that disagreement.

All eight original files were copied unchanged, reopened and handed off by Grok.
Both reviewers verified full original-condition compliance for 4/4 ordinary files
and 3/4 candidate files; the remaining candidate is uncertain, not proven invalid.
There were no false rejections of agreed-valid images. Candidate self-report did
not resolve the speaker-view concern. Actual source count and full-visibility
errors were absent in the four-utensil pair; this does not measure better detection.

The prompt change was actually exercised: each candidate preserved the complete
original brief as an exact prefix and appended two visual-direction sentences.
The specific speaker and utensil requests still received repetitive direction;
zero-addition behavior on an already resolved brief was not demonstrated. Ordinary
Grok freely developed its own prompts under the same task and one-call cap.
The comparison does not isolate the appendix from other existing skill rules.

The candidate is kept only in private experimental evidence. No product rule,
version, user guide, or smoke record is changed. There is no corrective retest or
new sample after these results. A successful isolated image does not justify
shipping a rule that fails its overall adoption criterion.

[Sanitized scores and fingerprints](results.json) retain both reviewers' scores.
The local gallery contains all eight images, not a selected best pair.

## Question and intervention

Can a small first-prompt change improve the actual first image in an autonomous
Grok workflow, with the same image budget as ordinary Grok? Prior broad rewriting
[regressed craft and compliance](../2026-10-image-quality/README.md), while the
latest [review repair](../2026-10-image-fresh-transfer/README.md) only tied ordinary
review and used Codex. Neither establishes the requested benefit.

Pin one candidate before seeing images or the independently authored briefs.
Preserve the entire original drawing brief and complete at most two consequential
open visual choices for the intended use. A choice describes a visible composition,
spatial arrangement, material-revealing light, or medium-specific treatment. Leave
already specified choices alone; add no subjects, props, text, or new style. No new
review stage, scorer, runtime script, image backend, or default image call is added.
The existing read-only/authorization, correction and final-file contracts remain.
The candidate changes SKILL.md and its Safe Inference reference consistently.

## Frozen comparison

An independent agent authors four natural synthetic requests without reading the
candidate or previous experiments: product photography, editorial illustration,
environment, and a modest multi-object still life. Include a short open brief and
a specific treatment guardrail. Exclude prior development subjects. Full briefs,
inputs, candidate manifest and protocol are hashed privately before any provider
call. No request or candidate revision is allowed after generation starts.

Each request has two fresh Grok sessions, one ordinary and one candidate. Both get
the same brief, project purpose, supported canvas, destination convention, tools,
model/effort, turn/time cap and **one image_gen call**. Ordinary Grok may write its
own prompt; do not cripple it by forcing verbatim transmission. Only the candidate
has native image-workbench installed and explicitly invoked. Grok writes its own
prompt, generates, inspects and hands off without Codex supplying art direction or
correcting its decisions. Other models may evaluate the completed pixels only.

Reuse the existing isolated-home runner: pinned CLI 1.0.67, requested grok-4.7/high,
maximum 16 turns and 600 seconds, no memory, web, subagents, MCP, or shared state;
at most two host processes concurrently. Alternate arm ordering. Audit actual model,
tool inputs, generated/final bytes, native skill loading and credential cleanup.
No retries, edits, replacement samples or second candidate. Eight image calls are
the complete quality budget. Failed or missing results remain in the denominator.

## Evaluation and adoption rule

Randomize anonymous image identifiers; reviewers see the full original brief and
pixels, not arm labels, generated prompts or host verdicts. Evaluate every original
returned image and its final delivery independently. The candidate's added direction
is never an extra user requirement. Keep critical compliance, observable craft,
self-review accuracy and final handoff distinct; uncertain conditions are not passes.

Two independent model reviewers score four craft dimensions on 1–5:
geometry/artifacts; material/light or medium execution; composition/readability;
and specificity/coherence for the intended use. A 3 is usable with visible defects,
4 is polished with minor limitations, 5 is exceptional on that dimension. Each
reviewer gives a pairwise preference with visible reasons or a tie. Preserve
reviewer disagreements; do not adjudicate them toward the candidate.

Adopt only if the frozen candidate satisfies all of these on these four requests:

- At least three agreed pairwise wins and no agreed loss; disagreement is a tie.
- Mean paired craft improvement at least 0.5/5 and greater than two standard errors
  across the four request-level differences, not across dimensions or reviewers.
- No critical-compliance regression on any request, no lower usable-final count,
  and no new false rejection of a candidate both reviewers find compliant.
- Every run respects the one-call budget; the claimed Grok-only path and actual
  prompt preservation are supported by the native records.

These are exploratory adoption thresholds, not statistical proof of general
superiority, human taste, deterministic causation or repeatability. There is no
seed pairing. Report all observations even when the adoption rule fails. Do not
raise the budget, tune to the four requests, weaken the rule or add samples to
obtain a favorable result. If adopted, reuse a successful candidate generation for
output smoke and add only the three required image-free host probes, then run
product-scoped and full provider-free verification before committing.

## Execution evidence and limits

Actual orchestration was Grok CLI 1.0.67, `grok-4.7-build/high`: eight sessions,
eight `image_gen` calls, 45 turns and 436.068 summed session seconds. Maximum
concurrency was two. No image edit, retry, Codex live process or other generation
model was invoked. Reported orchestration cost was $0.188819; image billing and
reviewer cost are unknown, and summed time is not elapsed time or a speed claim.

Native discovery and full skill-body injection were confirmed for all candidates.
The reused parser initially returned false because native expansion removed one
trailing newline. An independent exact comparison confirmed all 180 body lines
and complete task arguments; original parser outputs remain in the private record.
The normalized body hash is
`4f05a93e8a4801729a927224349af75fe082e321a07ac773e2110717f75e7360`.
The final native audit hash is
`c0be0238df9a01b17c36fc92205ef7a687f022a6b58c3850a177695646e6ad37`.

All eight runs preserved input/payload hashes, respected their budgets, used the
same original task, reopened byte-identical project copies and removed temporary
authentication. Config settings remained intact; Grok appended marketplace
metadata. Actual reads/calls were checked; isolation is not an OS sandbox claim.
All output canvas values match (1248x832 landscape, 1024x1024 square, 832x1248 portrait).

All four candidate sessions omitted the skill-mandated `inspect_asset.py` execution.
The auditor separately inspected every output successfully, but this does not count
as autonomous host compliance or a passing output smoke. This additional contract
failure is recorded without adding review instructions to the candidate.

The original case-author could not be resumed for judging because of the agent
thread limit. Reviewer A was therefore the primary author, who knew the intervention
but had not seen arm mapping, prompts, verdicts or the other score. Reviewer B
independently inspected the anonymous packet. Both saved immutable scores before
unblinding. This is blinded arm identification, not blinded study authorship or
human ground truth. No disagreement was re-scored to improve the result.

Only repository evidence documents change. JSON validation, independent score/SE
recalculation, evidence hashes, changed relative links, byte hashes of all eight
gallery copies and `git diff --check` passed. The gallery was opened and visually
checked; a separate read-only claims review found no material issue. Product files
are unchanged, so no provider-free product suite or live smoke was rerun. Generated
media, full prompts, raw receipts, candidate payload and authentication stay outside Git.
