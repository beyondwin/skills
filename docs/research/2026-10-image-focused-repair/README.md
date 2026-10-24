# Focused image repair, 2026-10-23

Status: complete. Adopt the focused requirement-scope fix as **2.1.6**. The
verified delivery workflow used Codex review and Grok drawing by user request.
Grok autonomous-review improvement is **not** established.

## Outcome

The same three known originals, same Codex model/effort and task produced:

| Check | 2.1.5 | 2.1.6 candidate |
| --- | --- | --- |
| Correct source decisions | 2/3 | 3/3 |
| Count-failure detection | 1/1 | 1/1 |
| Occlusion-failure detection | 1/1 | 1/1 |
| Valid overlapping-parts candidate retained | 0/1 | 1/1 |
| False accepts / false rejects | 0 / 1 | 0 / 0 |
| Completed responses | 4 | 3 |
| Session seconds | 60.243 | 97.931 |

Both arms directly counted four legs in the valid image. The control rejected it
because the rear leg's whole shaft was not exposed; the patch accepted its directly
visible lower part and foot at the original requirement's strength. This reproduces
and removes a particular interpretation defect. Count and occlusion perception did
not improve over the already-correct Codex control. The sources were selected from
known failures; three examples do not establish statistical or general aesthetic
superiority, and the earlier G decision remains unchanged.

Final deliverables were inspected directly and independently:

| Deliverable | Actual outcome |
| --- | --- |
| Three-leg source | One correction produced four directly visible legs/feet; original space, vessels, exclusions and ratio retained |
| Occluded-leaf source | One new drawing exposed all three outlines/stems; one shore-position edit restored the distant-shore composition without new count/visibility defects |
| Valid four-foot source | Original bytes retained, zero additional image calls |

All **three final assets pass critical content, count, visibility and composition
checks**. The boat's requested clay texture remains visually unverified; it is not
reported as perfect full-brief compliance. Its broad folded hull can read as a basin;
the original request did not specify a particular origami form. Qualitative margins
and materials retain interpretation limits. The independent reviewer initially
missed source occlusion and corrected that result after a localized boundary check;
that is disclosed assistance, not first-pass blind agreement.

The delivered outputs used three drawing calls in total: the earlier successful
count edit, boat generation and shore edit. The comparison/diagnostic work made
three other drawing calls, all retained in the record. Across all work: **Grok
12 sessions, 80 turns, 6 image calls, 1582.343 summed session seconds**;
**Codex 2 sessions, 7 responses, 158.174 summed seconds**. Maximum concurrent host
processes was two. Summed seconds are not elapsed wall time. Grok reported
$0.62336688 for orchestration; image billing, Codex and independent-reviewer costs
are not established. Do not present this as total price or a speed improvement.

Grok CLI 1.0.67 actually ran `grok-4.7-build/high`; Codex CLI 0.163.0 actually ran
`gpt-6-astra/ultra`. The image engine identity is not inferred from the orchestrator.
The initial Grok comparison failed: both arms missed the occluded leaf and wrongly
corrected the valid source; the candidate then exhausted 16 turns without final
handoff. The intermediate refined rubric also missed the occlusion. These are
failures of that path, not counted as Codex gains. No requirement for another model
or automatic CLI fallback was added to the product.

[Sanitized results](results.json) retain the rows, hashes, cost limits, deviations
and output file facts. Native audit verified full pins, actual delivered image bytes,
complete drawing-base transmission, final copy hashes and authentication cleanup.
The independent final runtime audit SHA-256 is
`b1478110f92e4543318d1af4ad3bf698f09b293c2c323f64de697c7c6927eca4`.
Runtime success is separate from visual correctness.

## Verification

The current SKILL body passed real Grok discovery, explicit brief, implicit project
brief, casual near-miss and project-output checks. The three read-only probes used
an earlier rubric with the identical final SKILL body; the final output used the
final rubric. Codex quality runs used the complete pinned content, not native skill
discovery. The last newline difference in native expansion was checked against the
whole body and arguments without rerunning a provider.

On macOS, `python3 scripts/verify.py --skill image-workbench` passed: 24 release
contract tests, 32 offline cases, 17 mutation checks, 83 inspector/live-record
unit tests and compilation. `python3 scripts/verify.py` also passed: 246 repository,
11 Korean package, 256 Korean live-harness unit, 83 image and 64 how-it-works tests,
both offline matrices, the no-provider dry run and compilation. These are repository
checks, not extra live image-quality samples.

The first scoped attempt encountered only ignored Python caches under retired
product directories; those caches were removed. The first full attempt found one
stale version literal in a rejection test and two archive checks reading the older
Git index. The literal was updated and the reviewed product payload staged; the
subsequent full run passed without changing the release builder or weakening checks.
The final gallery rendered in the in-app browser, and its stored files were inspected
again at their delivery paths. A separate read-only audit found no material issue in
the aggregate, evidence hashes, claim boundaries or private-data exclusion.

The bundled generic skill-creator validator rejected the existing `compatibility`
frontmatter key; the repository's product contract is the authority for that
unchanged field. It was not removed to satisfy the narrower generic validator.

## Question and bounded decision

The user renewed authorization after the previous G study: repair the concrete
count, occlusion and false-rejection defects, verify final generated results,
and avoid more sampling or a larger evaluation system. The previous
[G decision](../2026-10-image-evidence-review/README.md) remains unchanged.

This is a focused regression and delivery test, not another unseen-population
superiority study. Three already inspected sources represent a three-visible-leg
count failure, a leaf hidden by a boat rim, and a valid four-visible-foot table
with partial overlap. Their original briefs and image bytes remain fixed across
the 2.1.5 control and the proposed 2.1.6 patch. The sources are development data;
new corrected outputs provide final-delivery evidence only.

Both arms use Grok CLI, the same requested model/effort, native tools, original
briefs, source images and budgets: one correction image call per task at most,
16 turns and 600 seconds. Each run has a fresh isolated home with a complete
pinned skill. Run each arm once per source, two concurrent sessions at most;
do not replace failures or add images to improve an aggregate. Preserve native
tool calls, model identity, original images, outputs and file hashes privately.

Before any calls, the decision is: the patch must correctly reject both invalid
sources, retain the valid source without a drawing call, and deliver all three
final assets with their original critical conditions verified. A reproduced
control defect must be removed without a new regression. Otherwise diagnose the
specific remaining failure and change the mechanism, not the sample count.
No quality improvement is credited for an already-correct count. No p-value or
general aesthetic superiority is inferred from these selected cases. The prior
two-SE G gate is not recalculated or declared passed by this repair test.

An independent reviewer receives anonymized source/final images and the original
briefs, without arm labels or the generating agent's verdict. The primary agent
also opens the originals. Disagreement remains explicit; a self-reported pass is
insufficient. Verify correction prompts retain the complete drawing base and
the actual final file, ratio, count, required visibility and exclusions. Native
Grok activation probes reuse final-output verification; no extra drawing is
needed for smoke.

## Intervention

Keep the complete original drawing base and one targeted correction. Replace
the broad outline check with directly located counts and three distinct scopes:
framing, identifiable named parts, explicitly unobstructed outlines. A rejection
needs a visible contradiction at the original requirement's strength. Preserve
a passing candidate instead of correcting advisory preferences. No new runtime
script, judge model, mandatory crop, output schema or provider is added.

## Results

### Localized revision after the first occlusion result

The initial patch and control both falsely accepted the boat source, despite
reading their complete rubrics. The initial independent reviewer also missed it;
a localized reinspection of the leaf/foreground junction corrected that verdict.
The initial report is retained, not presented as independent first-pass agreement.

The patch's complete-visibility branch now asks for each target's lowest visible
edge or endpoint and the adjacent foreground boundary before a pass. This is one
focused look within the same reviewer, not a new judge or mandatory image transform.
Before the follow-up call, the plan is restricted to rerunning this one affected
case with the new reference and the same input/task/budget. The count and valid-part
branches are unchanged; their completed results are version-specific regression
evidence, not reruns of the revised full pin. Keep both unsuccessful first reports.
No new source image or control rerun is added. The final output must expose all
three leaf outlines and retain every original condition. An unresolved failure
cannot be credited as a successful delivery.

### Responsibility change before further calls

The subsequent valid-table task exposed a more serious limit: Grok with the first
patch still called the visible rear foot missing, made an unnecessary edit, and
exhausted 16 turns without a final handoff. An attempted cancellation of the queued
refined Grok review did not stop its wrapper: the PID search returned no match,
and the queue later dispatched once. The initial cancellation marker is retained
with a correction. That extra review took six turns, made zero image calls and
again falsely accepted the occluded leaf. Its time/cost remains in the totals.
Actual timestamps show it finished before either Codex session; it did not overlap
that stratum. No cross-run latency advantage is claimed.
Do not treat the new rubric as a proven repair of
Grok's visual perception, and do not keep adding prompts to that reviewer.

The user asked for Grok CLI drawing, not Grok-only judgment. The remaining test
separates review from drawing: exactly two read-only Codex sessions compare 2.1.5
with the refined patch on the same three source images, original requirements,
model/effort and 20-response/600-second budgets. No new source sample or repeated
control session is added. This is a new host stratum, not a pooled Grok gain.
Codex judges the original conditions; Grok renders an exact authorized correction.
The final pipeline keeps the successful four-leg correction, preserves the valid
original, and makes one new drawing for the still-occluded boat. All three final
assets require direct and independent visual inspection. Generation stochasticity
and the historical source selection remain explicit limits.

The adoption question is a concrete requirement-scope bug fix on Codex plus a
verified final-delivery workflow. It does not establish a population-level quality
gain, nor an improved Grok autonomous-review workflow. Product hosts and default
native routes stay unchanged; the cross-host drawing route is the user's explicit
choice in this task, not a new automatic CLI fallback.

### Final-output correction

The first new boat drawing exposed all three leaves. Independent review confirmed
the four critical checks but identified a separate original-brief drift: the
requested distant shore appeared in the foreground. Do not call four checklist
passes complete original-brief preservation. Before the next call, authorize one
targeted shore-position edit with the complete drawing base, preserving the boat,
leaf outlines, spacing, colors, light and canvas. Keep both versions and verify
the edited original. This is an observed-defect repair, not an added review sample
or a replacement for the unsuccessful earlier trials.

Offline checks and native activation are reported separately from image
quality. Private media and provider receipts are not committed.
