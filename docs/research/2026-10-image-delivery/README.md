# Image delivery within a two-call budget

Historical study. `image-workbench` was retired on 2026-10-28; the versions,
commands, and support observations below describe the original study, not a
currently installable product. See the [retirement decision](../../learning/cases/2026-10-28-retire-image-workbench-and-simplify-repository.md).

Date: 2026-10-22. Follow-up to the
[first-candidate study](../2026-10-image-quality/README.md).
The question is whether inspection, optional correction, and selection deliver a
usable project asset within the same budget. This is a small development study,
not a statistical superiority test.

## Design fixed before execution

Three synthetic briefs cover a floor-lamp hero with a reserved text area, an
editorial tray illustration with three fully visible pebbles, and a product
photograph of two separate open-neck glass carafes. The lamp was written before
the earlier study but never executed. Pebbles and carafes are new briefs.

Each brief runs once with ordinary Grok and once with the current image-workbench
2.1.3. Both receive identical requirements, project paths, reporting instructions,
model request, and a maximum of two image-generation attempts, including failures.
Only the installed skill and its invocation differ. A second attempt is optional;
the budget is a ceiling, not a requirement to generate variants. Image edits are
not permitted. Total image-call ceiling: 12, without replacement runs.

Runs use isolated homes and conversations with memory and compatibility imports
disabled. The complete product payload is pinned before execution. Authentication
copies are removed afterward. Actual models, tool calls, and payload hashes are
audited from local transcripts. Generation provenance is hidden from two
independent model judges; every generated candidate is included, not only the
selected output. A final copy must match a preserved candidate by SHA-256.

The primary outcome is usable delivery: both judges confirm all four brief-specific
critical checks and the requested canvas, and the mean of their four craft scores
is at least 4.0/5. Craft dimensions are geometry/artifacts, material/light,
composition, and specificity/coherence. The 4-point anchor is polished and coherent
with minor compromises. Pixel dimensions are checked independently, allowing only
one-pixel ratio rounding.

Hard-condition delivery and usable delivery are reported separately. Choosing an
image that lacks both judges' hard-condition confirmation is an unverified
acceptance, with clear failures and judge disagreements distinguished. A craft
score below 4 alone is not a false acceptance. Holds, missing reports, provenance
errors, first-to-selected changes, and actual call counts remain separate. Missing
judgments are not filled with zeros.

## Read-only selection control

Two additional isolated sessions inspect the same three anonymous pools from the
earlier study: one acceptable and one failing boat; two failing boats; and two
acceptable tea images. The original briefs and image bytes are retained. Each
session must select an eligible candidate or none. Only a JSON report may be
written; image generation, editing, conversion, and copying are prohibited.

The key comes from the previous independent judgments and stays outside the
session workspaces. Candidate eligibility and final selection are scored
separately. This is a regression check on known images, not new image-quality
evidence. The task instructions themselves request careful inspection in both
arms, so any comparison measures the skill's incremental effect over that request.

## Results and decision

All six generation sessions completed on Grok CLI 1.0.62 with observed agent
model `grok-4.7-build/high`. They used seven image-generation calls: three ordinary
and four skill calls, producing seven candidates without rejected calls. No image
edits were made. Reports were valid, the five selected final files matched their
preserved candidates, payloads stayed fixed, and authentication copies were removed.
The image-generation backend was not independently identified.

| Brief | Ordinary final craft | Ordinary usable delivery | Skill final craft | Skill usable delivery | Calls, ordinary / skill |
| --- | ---: | --- | ---: | --- | ---: |
| Lamp | 4.50 | Yes | 4.375 | Yes | 1 / 1 |
| Pebbles | 4.25 | Yes | No selection | Hold | 1 / 2 |
| Carafes | 4.25 | Yes | 4.125 | Yes | 1 / 1 |

Both hard-condition and usable delivery were **3/3 ordinary and 2/3 skill**.
None of the five selected files failed the independent hard-condition check.
The ordinary selected-image mean was 4.333 over three images; the skill mean was
4.25 over two. These different denominators must not be treated as a paired
quality gain. Across all generated candidates, means were 4.333 (three ordinary)
and 3.90625 (four skill). No selected file differed from its first candidate: the
only second call ended in a hold, not an improved delivered image.

The two skill pebble candidates scored 3.5 and 3.625. Judges disagreed about
whether the tray was oval or a rounded rectangle, and whether the background
paper treatment was an extra object. The second candidate had visible text,
which both judges rejected. The first was not jointly confirmed and was below
the craft threshold; the hold therefore did not discard a verified usable result.

The correction's tool prompt retained the subject, count, and arrangement but
omitted the original exclusion list, including words, logos, and watermarks.
The resulting image added text. This is an observed constraint omission and
regression, not proof that the omission alone caused the text. A second attempt
is not automatically a quality improvement.

### Selection control and rejected revision

The original read-only control selected correctly in 2/3 pools for ordinary Grok
and 1/3 for the skill. Both accepted the same rim-occluded leaf. Ordinary review
rejected one of three reference-passing candidates; skill review rejected two,
miscounting four visible table feet as two or three. Root inspection of the source
images confirmed these specific discrepancies. The ordinary session also searched
its own isolated Grok configuration outside the permitted read scope; it accessed
no answer key or previous metrics. That protocol violation remains recorded.

A development-only reference revision asked the reviewer to inventory required
objects by visible position, inspect boundaries, and judge each candidate before
comparison. Its adoption rule required all three development pools and both held-out
pools to be correct, with every candidate eligibility decision correct and no
held-out regression. It made no new generation calls.

| Read-only check | Current reference | Inventory candidate |
| --- | ---: | ---: |
| Development pools selected correctly | 1/3 | 1/3 |
| Development candidates classified correctly | 3/6 | 3/6 |
| Held-out pools selected correctly | 0/2 | 0/2 |
| Held-out candidates classified correctly | 1/4 | 1/4 |

The revision repeated the errors and **was not adopted**. Before either held-out
run, a proposed passing boat was excluded because the earlier judges had recorded
an ambiguous leaf-stem boundary. Its prior pass label was preserved. It was replaced
with a clearly occluded boat, making that pool all-fail; the tea pool remained mixed.
The amendment and replacement inspection preceded both held-out executions.

The follow-up used eleven Grok sessions in total: six generation sessions and five
read-only selection sessions. The latter made zero image calls. The five audits
changed only their permitted report files, preserving image and payload bytes.
They are repeated checks of ten historical images, not five independent new
image-quality domains. The external judges are models, not a human preference
panel; their disagreements are retained.

## Product decision and practical use

The runtime instructions remain those tested as 2.1.3. Version 2.1.4 changes user
guides, the changelog, and version metadata only: it explains the absence of an
established aesthetic advantage and the observed limits of model self-review.
The failed inventory rule is kept out of the product. This is not a claim that
2.1.4 improves visual recognition.

For a well-specified new image, start with the detailed brief and one candidate.
Use the skill when project paths, formats, preservation, or integration need its
workflow; this experiment supplies no reason to invoke it solely for beauty.
If another attempt is authorized, state the observed defect and retain every
original requirement in the drawing prompt. Keep failed candidates, reject new
regressions, and stop at the budget. When exact count or complete visibility matters,
inspect those parts independently rather than trusting the generating agent's confident
summary. Independent review itself is not infallible.

This study does not estimate repeat success rates or establish general superiority
of ordinary generation. It also does not test image editing, identity preservation,
other agent models, or Codex generation. The six comparable runs use the unchanged
runtime payload manifest `8390d30aca04dc40f50d9a1c401fff1eab6f6b206c49717833b06a413dd53925`.
The rejected quality-rubric reference SHA-256 is
`b6cc2aa0d0ed1b4ce82ccb5862e196d933d71df97be49e53119a03c520c0b5b4`.

## Verification

`python3 scripts/verify.py --skill image-workbench` and the full
`python3 scripts/verify.py` passed in a temporary Git-indexed copy of 668 current
tracked and new non-ignored files. The full run covered 642 unit tests, product
contract/mutation checks, and Python compilation, without credentials or provider
calls. The original checkout's ignored retired product/test directories were
preserved and excluded from this copy, as in the earlier study. This is macOS with
Python 3.14, not additional OS or live-model evidence.

The final wording and verification-note edits receive content, relative-link, and
diff checks separately. Runtime SKILL text excluding metadata, quality-rubric.md,
and image-spec.md are byte-equivalent to the pinned current runtime. No executable
product code changed. Raw calls and generated images remain local; the repository
record cannot independently re-score pixels without the local evidence bundle.

The local scorer passed 16 boundary and arithmetic checks, including missing or
duplicate ratings, invalid values, one-pixel ratio tolerance, and the hold
denominator. The comparison gallery passed 34 local-link checks and JSON/hash
validation. Browser inspection confirmed side-by-side original images and the
expanded failed-candidate disclosure; screenshots remain in local evidence storage.

The associated [decision case](../../learning/cases/2026-10-22-image-delivery-budget.md)
records intent and alternatives. Generated media, prompts, and provider receipts
remain in local evaluation storage and are not committed.
