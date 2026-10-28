# Image review and correction repair

Historical study. `image-workbench` was retired on 2026-10-28; the versions,
commands, and support observations below describe the original study, not a
currently installable product. See the [retirement decision](../../learning/cases/2026-10-28-retire-image-workbench-and-simplify-repository.md).

Started: 2026-10-22. Updated: 2026-10-23. Status: completed with a narrow retention patch; broader review-repair criteria failed.

This follows the [two-call delivery study](../2026-10-image-delivery/README.md).
The user requested actual fixes for count/occlusion errors and dropped correction
constraints, with a new comparison under the same image budget. The Korean
[decision case](../../learning/cases/2026-10-22-image-review-repair.md) records the
intent and alternatives.

## Design fixed before execution

The frozen control is image-workbench 2.1.4. Development candidate A retains the complete
original drawing brief and appends only the targeted correction. It distinguishes
requested visibility from an extra unobstructed-outline requirement, and uses
an overview plus a native-resolution detail view for small parts and contact
boundaries. A temporary macOS `sips` helper is optional; the original remains
unchanged and is the only candidate deliverable.

Both arms first audit the same ten historical images in five pools. Both receive
the same explicit permission for temporary diagnostic crops, their factual JSON
receipts, and private temporary directories. This is a controlled procedural
change from the earlier no-crop audit, not its exact reproduction. The historical
labels are development data. Both also receive the same prior pebble failure for
one correction attempt, with the original request unchanged.

After development, the retained candidate is 2.1.5: only the original-brief
preservation and full critical-condition recheck component is kept. None of the
three failed visual-review variants or their optional crop helper is shipped.
This component selection is recorded prospectively before final generation, not
called a successful fourth visual-development variant. A's paired correction is
development support, not a final-payload measurement.

Ordinary generation, the frozen baseline and locked 2.1.5 receive the unchanged
lamp, pebbles and carafes briefs. Each session
has at most two image-generation attempts, 20 turns and 600 seconds. The only
common protocol amendment is permission for temporary diagnostic inspection
files. Every successful candidate is independently judged, including unselected
or held images. A later audit of these new images tests selection transfer without
further candidate revision.

Usable delivery requires both blinded reviewers to pass all four original hard
conditions, the measured aspect ratio to match within one pixel of integer
rounding, and the mean of eight craft ratings to reach 4.0/5. Hard delivery,
usable delivery, false accepts, false holds, first and selected candidate craft,
calls, elapsed time and reported cost remain separate. A hold has no selected
craft score. Reviewer disagreement is recorded rather than converted to a pass.

Grok CLI 1.0.67 is pinned by its actual executable path and SHA-256; the earlier
study used 1.0.62. All three controls therefore run contemporaneously. The
requested orchestration configuration is `grok-4.7/high`; the actual model and
effort are read from native history. This does not identify the image backend.
Fresh subprocess homes, memory disabled, no imported skills or MCPs, private
temporary directories, full payload manifests and credential cleanup preserve
isolation. Prompt caps are audited, not described as a proven tool-level quota.

## Local evidence

The run root is `/tmp/image-workbench-improve-20261022`. Its preregistration,
frozen payloads, inputs, generated media, provider logs, receipts, blinded ratings
and private answer keys stay local and must not be committed. Repository records
contain methods and aggregate findings only.

## Results and limitations

The first development candidate did not improve visual eligibility: baseline and
candidate A each classified 5/10 images correctly and selected correctly in 1/5
pools. Both produced two false accepts and three false rejects. A opened all 30
native detail views it created; the 40 delivered image contents (ten originals
and 30 details) matched their source bytes. Cropping alone is not an effective
repair in this test, and A is rejected as a visual-review fix.

A separate paired correction retained the complete original drawing brief in A's
actual image call. The baseline omitted the original exclusion sentence and
generated visible words; A preserved it and generated no visible text. Each made
one generation call and finished normally. Two fresh blinded reviewers passed
all four original critical conditions for A (craft mean 4.0/5) and both rejected
the baseline's visible text (craft mean 3.25/5). They disagreed on whether its
pebble texture also violated the smoothness condition. Both original files were
1248 by 832, matching 3:2. The first exploratory reviewer had seen arm-bearing
directory names and is excluded from this blinded aggregate; the replacement
review protocol was fixed before its final reviewer returned. This is one targeted
comparison; prompt transmission and image compliance remain separate outcomes.

Candidate B added candidate-at-a-time decisions, source-named detail files,
floor-contact and perspective semantics, and explicit foreground-termination
checks. It exhausted the unchanged 30-turn limit after 394.802 seconds, opening
8/10 sources and 16/18 created details. It produced no final report, so its
accuracy is missing, not an invented zero. Its partial working notes still
contained the known errors; they are not a scored result.

Candidate C is the final preregistered development variant. It batches independent
reads and crop work within one comparison group, keeps one contextual detail for
an unresolved count/contact check, and skips crops for already decisive failures
or clear empty regions. The budget and inputs remain unchanged. Completion and
visual accuracy must both be measured. C finished in 23 turns and 669.508 seconds,
but accuracy regressed to 4/10 with three false accepts and three false rejects.
It still selected correctly in only 1/5 pools. All source bytes and payloads were
preserved, its report matched the final response, and it made no image calls.
Thus execution recovery did not repair perception, and C is rejected.

| Development run | Correct eligibility | False accepts | False rejects | Correct pool decisions |
| --- | ---: | ---: | ---: | ---: |
| Baseline 2.1.4 | 5/10 | 2 | 3 | 1/5 |
| A: detail views | 5/10 | 2 | 3 | 1/5 |
| B: sequential review and semantics | Not measured: turn limit | Not measured | Not measured | Not measured |
| C: bounded grouped review | 4/10 | 3 | 3 | 1/5 |

The retained 2.1.5 changes correction-condition preservation only. Count and
occlusion self-review remain unresolved. Fresh-image results cannot erase these
historical failures.

## Final matched generation

All nine fresh sessions completed normally on `grok-4.7-build/high`, producing
12 images in 12 attempts. Both independent reviewers assessed all 12 originals;
there were no critical-item disagreements or unverified items. All requested
ratios passed the mechanical check. Every selected image matched its final file
hash, every frozen payload remained unchanged, and copied credentials were
removed. No forbidden call or call-budget violation occurred.

| Final-generation metric | Plain | Baseline 2.1.4 | Retained 2.1.5 |
| --- | ---: | ---: | ---: |
| Usable deliveries | 2/3 | 3/3 | 3/3 |
| Hard-condition deliveries | 3/3 | 3/3 | 3/3 |
| False accepts / selected deliveries | 0/3 | 0/3 | 0/3 |
| First candidates usable | 2/3 | 3/3 | 2/3 |
| Selected craft mean, 3 images each | 3.833 | 4.000 | 4.000 |
| All-candidate craft mean | 3.813 (4) | 4.000 (3) | 3.925 (5) |
| Image calls | 4 | 3 | 5 |
| Total turns | 42 | 36 | 50 |
| Sum of session seconds | 1080.010 | 592.970 | 615.897 |
| Reported orchestration cost, USD | 0.4805 | 0.3090 | 0.4163 |

There were no holds, missing deliveries or rejected image attempts. The durations
are sums of session durations, not elapsed experiment time; cost may omit image
billing. The [aggregate record](results.json) preserves the denominators.

Plain generation corrected four pebbles to three, but its final image's craft
score was 3.5/5. Both skill versions reached 4.0/5 in all three selected images.
The retained version removed visible embossed-like marks from its first carafe
image. Its pebble correction, however, changed a candidate both reviewers had
already considered usable and left craft at 4.0/5. The new version met the local
3/3 delivery target, but tied the baseline while using two additional image calls.
This is a measured correction mechanism, not an overall quality or efficiency win.

Both actual retained-version correction calls reused the entire first drawing
prompt as an exact prefix and preserved all seven original visual-condition
categories, including the aspect-ratio parameter. No new or inherited condition
omission was found in those two calls. This is distinct from literal reuse of the
raw user brief: opening wording had been compressed and operational fields were
removed. Full verbatim compliance with the user text is therefore not established.

The baseline made no correction in this final matrix, so its correction-retention
denominator is zero. Plain's single correction did not introduce a new omission;
it inherited missing explicit no-words/logo/watermark restrictions from the first
prompt, and the resulting image nevertheless contained no visible text. Do not
misdescribe this as a new correction loss. The separate paired development
correction remains the direct baseline comparison for the exclusion-loss defect.

The reviewers were fresh independent Codex contexts, not human raters; their
exact model identifiers were not verified. Three briefs with one session per
arm do not establish significance, general preference, or a population success
rate. A visually compliant result does not prove its prompt retained all conditions,
and retained conditions do not guarantee a compliant result.

## Fresh-image selection transfer

The inclusion manifest was fixed before dispatch: all 12 new images, ten clear
hard passes and two clear failures, with no exclusions. The negative controls
are the four-pebble image and the marked carafe image. There is no new occlusion
negative, so this set cannot establish an occlusion-review repair. Uncertainty
about transcribing the marks does not make their prohibited presence uncertain.

Both versions receive identical anonymous images, original requirements and
three case pools, with 30 turns, 900 seconds and zero image calls. Candidate
eligibility is scored against the hard labels, separately from craft. Any hard-
eligible selection is a correct pool decision; this does not establish that the
highest-craft candidate was selected.

| Transfer metric | Baseline 2.1.4 | Retained 2.1.5 |
| --- | ---: | ---: |
| Correct eligibility | 10/12 | 9/12 |
| True positive / true negative | 8 / 2 | 7 / 2 |
| False accept / false reject | 0 / 2 | 0 / 3 |
| Correct pool selection | 3/3 | 3/3 |
| Turns | 19 | 13 |
| Session seconds | 722.821 | 590.413 |
| Reported orchestration cost, USD | 0.3382 | 0.2378 |
| Image calls | 0 | 0 |
| Strict procedural pass | No | Yes |

Both runs finished normally, opened all 12 original images with matching delivered
bytes, preserved source and runtime payload hashes, and removed copied credentials.
Both rejected the two negative controls. The retained version falsely treated
background paper in two pebble images and the integrated lamp base in one image
as extra objects. It therefore failed the preregistered no-eligibility-regression
criterion. Correct selection in three pools does not erase these false rejects;
every pool contained at least one eligible candidate, so no all-failing pool tested
the ability to hold.

The baseline wrote nine plain-text diagnostic receipts despite the prompt's
JSON-only receipt restriction. It fails the strict procedural gate, while its
normal, intact visual report remains scoreable. This separation was fixed before
the baseline result returned. The retained version's 29 temporary crops had PNG
names but JPEG contents: an auxiliary format defect, not a changed deliverable or
source. Its receipt also inaccurately described PNG re-encoding. PNG encoding was
permitted rather than required. These deviations are
disclosed instead of calling the entire comparison protocol-clean.

The scorer initially rejected both runs because native CLI startup appended the
same five marketplace bootstrap lines to each isolated config. The intermediate
null result was preserved; normalization now allows only that exact suffix while
still rejecting changes to the isolation settings. Seventeen provider-free scorer
fixtures passed. A harness metadata import also created one bytecode cache outside
the isolated runs; it was moved to diagnostic evidence and the external pin was
rechecked. Neither event changed the model inputs, labels, executed payloads or
reported visual answers.

## Adoption and practical use

The broader review-repair acceptance criteria were **not met**. The preregistered
option to retain a useful measured component is applied only to correction-condition
preservation in 2.1.5, with the failed transfer criterion disclosed in both user
guides and the CHANGELOG. This is not acceptance of a generally improved review
workflow. Three failed visual revisions, one additional false reject on transfer,
and the extra generation calls remain part of the result.

Keep a detailed original drawing brief, including exclusions and canvas, as the
base. Generate once, correct one visible failure with that complete base, then
recheck all original conditions. Stop when the image already passes: the extra
pebble correction supplied no craft gain. For acceptance-critical counts or full
outlines, independently inspect the actual image; a second confident answer from
the same generation context is insufficient. This study supports that bounded
strategy and a specific retention repair, not a promise that more prompting,
cropping or retries will reliably raise quality.

This small synthetic comparison cannot establish general aesthetic superiority,
human preference, complete image billing or visual accuracy on another host.

## Verification boundary

The product-scoped provider-free check passed 32 cases, 17 mutation checks and
65 unit tests. The full repository check passed 642 unit tests, its other offline
contracts, dry runs and Python compilation. Both commands ran against a fresh
Git-listed snapshot of the working files, preserving unrelated ignored local
directories in the original checkout. No production runtime Python changed.

Seven runtime and metadata files have identical hashes in the final experiment
pin, verified snapshot and working tree. The README pair and CHANGELOG were
updated after the experiment pin; this is runtime identity, not a claim that the
entire final installed payload is byte-identical to the experimental payload.
Every live session separately used and preserved its complete frozen payload.

The new output-contract smoke uses a real final-payload carafe generation. The
three image-free routing/brief probes reuse candidate C's identical SKILL body,
with different references and its rejected helper explicitly disclosed. The
body-bound smoke does not establish reference-wide equivalence, image-edit
preservation, Codex live behavior, or visual quality. Actual image quality comes
from the separate blinded comparisons above.
