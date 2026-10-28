# Fresh image review transfer, 2026-10-23

Historical study. `image-workbench` was retired on 2026-10-28; the versions,
commands, and support observations below describe the original study, not a
currently installable product. See the [retirement decision](../../learning/cases/2026-10-28-retire-image-workbench-and-simplify-repository.md).

Status: complete. Adopt only the observed premature-hold repair as **2.1.7**.
No advantage over ordinary review was established. The initial protocol compared
no skill with image-workbench 2.1.6 at commit `7587bb6` on four new synthetic
requests, not the three earlier development sources. No product change was presumed
necessary. The initial protocol and complete private requests were hashed before
generation; [sanitized results](results.json) preserve those fingerprints.

## Outcome

| Outcome | No skill | 2.1.6 fresh comparison | 2.1.7 development repair |
| --- | --- | --- | --- |
| Agreed-valid originals retained | 3/3 | 3/3 | 3/3 |
| False rejection of agreed-valid originals | 0/3 | 0/3 | 0/3 |
| Source count / occlusion failures available | 0 / 0 | 0 / 0 | same sources |
| Ambiguous feature correction / hold | 1 / 0 | 0 / 1 | 1 / 0 |
| Verified usable final delivery | 4/4 | 3/4 | 4/4 |
| Logical images used, including four shared originals | 5 | 4 | 5 |

Both ordinary review and 2.1.6 correctly excluded reflections from the fruit count
and retained the partly overlapping mug handle and fox paw. There is no measured
false-rejection reduction or count/occlusion detection gain on these sources.
For the disputed key image, ordinary review diagnosed malformed teeth and edited;
2.1.6 treated the ambiguity as a reason to stop. This is not rejection of a verified
valid source, and it is not an occlusion-detection failure.

The one 2.1.7 clarification made an authorized correction eligible without accepting
the unverified original. It preserved all three valid sources and corrected the key
with the complete original drawing base. Both final selectors chose their corrected
key plus the three original files. Direct and independent anonymous review passed
both key edits against the complete brief, with no observable quality winner. All
retained originals are byte-identical. The repair restores delivery from 3/4 to 4/4;
ordinary review already achieved 4/4. The post-fix sample is development evidence,
not a second unseen test. Four requests and model-only labels cannot establish
general superiority or eliminate overfitting concerns.

Actual expenditure was **six image calls**: four shared first images, one ordinary
edit and one candidate edit. Each workflow had the same two-call per-request cap;
unused calls were not spent. Nine Grok sessions (including three image-free host
checks) used 41 turns and 393.186 summed seconds. Five Codex sessions used 23
completed responses and 755.161 summed seconds before per-row rounding. No session
was retried or resumed; maximum concurrent host processes was two. Grok reported
$0.15690524 for orchestration only; image, Codex and independent-review costs are
unknown. These are not total price or speed claims.

Native records show Grok `grok-4.7-build/high` and Codex `gpt-6-astra/ultra`.
The image engine is not inferred from its orchestrator. Skill content was pinned
and injected into Codex; native activation is checked separately on Grok. All
source bytes, requests, tool prompts, final copies and isolated authentication
cleanup were audited. No raw receipts, prompts or generated media enter Git.

## Question and design

Does the current skill reduce count/visibility misjudgments and rejection of valid
candidates, and improve the final delivered image under an equal generation cap?
The four requests cover fruit count with reflections, complete key visibility,
identifiable mug handles, and visible paws on a fully framed toy animal. Full
briefs, file hashes, receipts and generated media are retained privately.

Each request receives one shared first image from Grok CLI using the exact
original brief. Sharing removes initial-image luck and is consistent with the
skill's unchanged-original first-prompt policy. This measures review/correction,
not an advantage in first-prompt generation. Each arm has the same logical cap:
one initial image plus one conditional correction. Actual maximum: four shared
initial calls and eight corrections. Do not spend unused calls to equalize usage.

Codex reviews each arm in one isolated session with identical briefs, images,
model/effort, tools, time and response limits. The no-skill arm receives no skill
content; the skill arm receives the complete pinned instructions and resources.
Neither common prompt includes prior results, expected verdicts or the other's
decisions. Historical README/CHANGELOG files exist in the full pin but actual
tool reads did not open them. Each reviewer
may retain, correct, or hold, and supplies the correction prompt if needed. Grok
CLI only renders that prompt. A final read-only pass per arm selects its actual
deliverable from its original and optional correction, with no remaining drawing
budget. All candidates and final selections count, including failures.

Both arms use Codex `gpt-6-astra/ultra`, at most 20 completed responses and 600
seconds per session; Grok drawing uses the pinned 1.0.67 CLI, `grok-4.7/high`, at
most 16 turns and 600 seconds per call. Actual model identity is read from native
records. Fresh isolated homes, disabled memory and two concurrent processes at
most follow repository rules. No retries, replacement samples or extra quality
sampling. Runtime failures are recorded, not silently replaced.

## Prospective scoring and stopping rule

Before reading arm verdicts, the primary and an independent reviewer inspect the
anonymous source images against the full original briefs. They also inspect all
final candidates without arm verdicts. Record disagreements and uncertainty;
these are model judgments, not human ground truth. A count needs directly located
instances, and full-outline visibility is distinct from identifiable parts.

Report count errors, missed occlusion, false acceptance, false rejection, unresolved
critical conditions, valid-candidate retention, actual image calls, and final usable
delivery over their eligible denominators. Keep aesthetic preference separate.
Final quality requires original critical requirements and no new condition loss;
a self-reported pass is insufficient. Compare paired outcomes, not inflated
per-condition totals or pooled old examples.

A descriptive gain requires fewer source decision errors, no new critical failure
or false rejection, and at least as many verified usable final deliveries. Claim a
final-output gain only if that last count strictly improves. Four requests cannot
establish statistical superiority; ceiling results or missing failure categories
remain inconclusive. Never keep sampling to obtain a favorable score.

Only a small, mechanism-specific product fix supported by a newly observed defect
may be attempted, once. It must remove that defect without a new regression on the
four requests and cannot be presented as independent transfer evidence after tuning.
Otherwise leave product behavior unchanged. Commit verified useful changes and the
honest evidence record; do not add a new judging pipeline or provider requirement.

## Results

### First observation and one bounded correction

Before arm results were opened, both visual reviewers agreed that three sources
were usable. On the key image, the primary reviewer marked teeth on the upper
key unverified, while the independent reviewer called them missing. Both saw four
separated, unobstructed key-shaped objects. Keep that disagreement explicit; there
are zero demonstrated source count failures and zero occlusion failures, so their
detection-rate improvement cannot be measured here.

Both initial arms retained all three valid originals. No skill requested one
targeted key edit; 2.1.6 held because the malformed upper key made the feature and
object interpretation uncertain. The no-skill edit exposed a clear toothed bit.
This is an actionable workflow defect: an unverified original should not be
accepted, but an observable ambiguity can justify an already-authorized correction.

Before a candidate rerun, freeze one small clarification in a private 2.1.7 pin:
keep acceptance blocked until verified, but use an available targeted correction
to make the required feature clear. Do not invent a missing part or weaken rights,
permission, tool or measurement holds. No other product behavior is changed.

This activates the predeclared one-fix allowance. Run one candidate review of the
same four originals and one candidate final selection, with at most one additional
key correction. These are development regression checks, not independent transfer
samples. Skip the unchanged 2.1.6 final-selection rerun because it generated no new
asset and already retained three/held one. Thus at most five Codex sessions replace
the initially planned four (two extra candidate sessions, one redundant session
removed). Native read-only smoke is required by the repository only if adopting a
changed SKILL body; it adds no image samples. Preserve the original transfer result.

### Runtime differences and limits

The candidate renderer loaded the native skill so its one edit also fulfilled the
required output smoke; the ordinary renderer had no skill. Both actual edit prompts
matched their own Codex correction text exactly. Only the ordinary edit explicitly
passed the optional `aspect_ratio: 3:2`; the candidate inherited the identical source
ratio, as the product requires. Both outputs measured 1248 × 832. Do not describe
all renderer context or all tool arguments as identical.

The other three native smoke sessions checked explicit brief, implicit project
brief and casual near-miss with zero image calls. The casual probe made no tool
calls. All original config lines remained intact; Grok appended marketplace-install
metadata during execution, so complete config-file hashes changed. No runtime
instruction, memory or tool setting changed. Actual tool reads did not open the
payload README/CHANGELOG or past experiment records. All commands stayed within
the task files, installed skill and returned image paths; this was not an OS sandbox.

There is one concrete text revision and one development retest, not repeated
sampling until the score improved. Requirements, inputs, budgets and correction
prompts were not adjusted after seeing their outputs. Independent judgments remain
model judgments; the original key's fail/unverified disagreement is not discarded.

### Verification

The product-scoped provider-free verification passed: 24 release-contract tests,
32 offline cases, 17 mutation checks, 83 image unit tests and compilation. The
first full check found a user-README ownership rule: product versions belong in
release metadata, not user guides. The new README version literals were replaced
with descriptive terms without weakening the test; the full check was rerun.
The final `python3 scripts/verify.py` passed all stages: 246 repository tests,
11 Korean package tests, 37 Korean offline cases and mutations, 256 Korean harness
unit tests, its no-provider dry run, 32 image cases and 17 mutations, 83 image unit
tests, 64 how-it-works tests and compilation. `git diff --check` and changed-document
relative-link checks also passed. The gallery was opened and visually inspected.
These checks do not add live visual-quality samples.

Independent runtime/claim audit passed with no material issue. Its private report
SHA-256 is `b23fe5650420cdf1f84fb0ddc9178916a60f272cc09b7d173aa950a71761b796`.
The local comparison gallery rendered all six actual images, and the eight selected
arm/case paths were mechanically inspected at their delivery locations. Its media
and screenshots remain outside Git.
