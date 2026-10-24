# image-workbench testing

Current activation is explicit-only. Earlier implicit-activation results below are
historical and do not validate the current policy. No live activation run was made
for this change; current host behavior is `not_measured`.

Fixtures live in `tests/products/image-workbench/`. To change the fixture
format or a judging rule, first change the evaluator self-test and the
fixtures (positive and near-miss cases). See the test fail, then implement.

## Deterministic fixtures

Deterministic fixtures are offline cases that always give the same result
without a real image call.

- `tests/products/image-workbench/cases.json` and
  `tests/products/image-workbench/run.py` define the expected routing,
  authorization, ImageSpec, handoff, and inspector results.
- The runtime inspector is `skills/image-workbench/scripts/inspect_asset.py`.
  Its tests live in `tests/products/image-workbench/test_inspect_asset.py`.
  Do not put a unittest suite in the runtime script.
- When inspector output changes, update
  `tests/products/image-workbench/test_inspect_asset.py`, the evaluator
  full-scope expectations, and the public docs together. Bump SemVer when
  behavior changes.
- Call the inspector by its path under the real skill root
  (`python3 <skill-root>/scripts/inspect_asset.py <absolute-asset-path>`),
  not through a repo-relative `skills/` path. Keep any `--output` report
  outside the skill folder.
- When an evaluator or inspector command or package path changes, align
  `tests/products/image-workbench/run.py` and `python3 scripts/verify.py`.
- `test_payload_docs.py` checks, in a temporary standalone copy, that README
  relative links resolve inside the payload. Public docs URLs are checked only
  against the matching file in this repo; this does not prove a remote HTTP
  response.
- The evaluator checks the read-only boundary with the original 8 mutations
  plus 9 that corrupt expected and candidate together. It runs without a real
  image call.

There are 32 offline cases. They do not prove an image looks good. The live
Grok check steps are in `tests/products/image-workbench/live/README.md`; CI
does not run them. Record offline passes and live image results separately.

`test_live_record.py` binds the Grok claim to `live/smoke-record.json`: four
`pass` values, a `session_id`, an ISO `run_at` with a time zone, an
`inspector` object, and the SHA-256 of `SKILL.md` without its frontmatter
`metadata:` block. A version-only bump keeps a valid smoke; any other
`SKILL.md` change needs a new Grok smoke before the test passes again.

## Codex trigger eval, 2026-10-02

Recorded in full in the [skill trigger eval](../../../research/2026-10-skill-trigger-eval/README.md). Codex gpt-6-astra/high with every installed skill and plugin,
in a synthetic project with brand notes and PNG assets. SKILL.md was `95c1a397`
at the time; this is historical trigger evidence, not a binding for later edits.

- **Positives.** The skill loaded for 24 of 24 project raster requests: replacing the hero
  image, a transparent logo, an App Store size, a thumbnail, comparing two heroes, auditing a
  banner, onboarding art, colour correction, an OG plan, an asset audit, an app icon, and
  masking personal data. `imagegen` loaded with it on the generation requests.
- **Near-misses.** It loaded for 0 of 24: a casual cat picture, an SVG logo, a data chart, a
  React section, a prompt gallery, icon swaps, lazy loading, a PNG/WebP question, a Mermaid
  diagram, badges, slides, and an app recommendation.
- **Design.** 12 prompts per kind with 4 held out, two repeats each.

The description stays as it is. Grok was not part of this eval.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill image-workbench
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
IMAGE_WORKBENCH_EXTRACTED_ROOT=/path/to/extracted/image-workbench
IMAGE_WORKBENCH_INSPECTOR="$IMAGE_WORKBENCH_EXTRACTED_ROOT/scripts/inspect_asset.py" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full --skill-root "$IMAGE_WORKBENCH_EXTRACTED_ROOT"
git diff --check
```

The last two commands show the scope of the product smoke that the shared
`verify-download` runs on the extracted payload. Do not unpack the same
archive again by hand to repeat that check.

CI does not require real image generation. It may need a login and may cost
money. Do not describe an offline pass as "the image is good".

## Inspection convergence, 2026-10-21

Version 2.1.2 was checked with Grok 1.0.62 (`grok-4.7-build` in the
transcript). A fresh generation completed in 8 turns with a correct hold for
visible table crop, versus the historical 18-turn limit without a final
report. Two audits of the same saved image rejected forbidden crop and
accepted explicitly allowed crop, each in 4 turns, without pixel-analysis
scripts or image calls. Explicit brief and a read-only casual-picture routing
probe made no images or file changes. The latter read the skill boundary but
did not execute its project workflow.

These are single regression runs, not statistical quality or latency claims.
Exact numerical acceptance, image edits, and Codex live behavior were not
retested. See the [decision record](../../../learning/cases/2026-10-21-image-inspection-convergence.md)
for this historical scope; `live/smoke-record.json` now records the later run.

## Image quality comparison, 2026-10-22

The [quality study](../../../research/2026-10-image-quality/README.md) compares
ordinary generation and 2.1.2 on three synthetic briefs repeated twice per arm.
Two condition-blind model reviewers scored actual delivered images. Craft means
were 3.98 and 4.17/5, below the predeclared improvement threshold; complete
compliance was 2/6 in each arm. Four unsupported-ratio calls were rejected, and
the resulting retries violated the one-call budget. Those failures remain visible.

A six-image broad rewriting revision lost craft and regressed the tea case, so
2.1.3 preserves detailed first prompts and confines spatial advice to a known
failure. Read-only visibility/count audit controls and fresh brief/routing probes
exercise the distinction; individual correction and unseen transfer generations
are recorded separately from first-candidate statistics. Full pinned payload
manifests, including later reference-only corrections, are retained locally.
The current smoke record binds the adopted SKILL body, not every reference byte.
This does not establish a general aesthetic advantage, human preference, image
edit preservation, or Codex live behavior.

## Delivery and selection follow-up, 2026-10-22

The [two-call study](../../../research/2026-10-image-delivery/README.md) gave
three unseen briefs to ordinary Grok and the unchanged 2.1.3 runtime, with at most
two generation calls per run. Seven generated candidates produced usable delivery
in 3/3 ordinary and 2/3 skill tasks under two independent model judges. The skill's
only correction omitted original exclusions and introduced visible text; it held
the result. This is a small comparison, not general superiority evidence.

Five additional read-only selection sessions exposed count/occlusion mistakes.
A reference-only spatial-inventory revision repeated them on development and
held-out pools and was rejected. Version 2.1.4 updates user guidance and metadata;
the tested SKILL body and runtime references are unchanged. The existing body-bound
smoke remains applicable. The unsuccessful revision is not part of the payload.

## Correction preservation and review repair, 2026-10-23

The [repair study](../../../research/2026-10-image-review-repair/README.md) pins
Grok CLI 1.0.67 and reruns all controls on `grok-4.7-build/high`. Version 2.1.5
keeps the original drawing conditions for correction calls and rechecks every
original critical condition afterward. In two final-payload correction calls,
the entire first drawing prompt was retained verbatim as a prefix and all seven
visual-condition categories survived. This does not prove verbatim preservation
of the raw user brief, whose opening and operational wording were changed.

Nine final-generation sessions produced 12 candidates. Two fresh blinded model
reviewers scored every original: usable delivery was plain 2/3, baseline 3/3 and
2.1.5 3/3. Selected craft was 3.83, 4.00 and 4.00/5, with four, three and five
image calls respectively. The baseline made no correction in this matrix. The
separate one-pair development correction supplies the direct exclusion-loss
comparison; it is not merged into final-generation denominators.

Three attempted count/occlusion review repairs failed: A tied baseline at 5/10,
B exhausted its turn limit without a report, and C regressed to 4/10. Their
visual rules and crop helper are not shipped. Count and occlusion self-review
remain unresolved; independent model review is also not human preference evidence.

A fresh selection audit of all 12 new images scored baseline 10/12 and 2.1.5
9/12, with zero false accepts but two versus three false rejects. Both selected
eligible images in 3/3 pools. The candidate failed the no-regression criterion;
only the measured retention component is retained. The baseline also failed the
strict JSON-receipt rule, while both intact reports remained scoreable. Temporary
crop format defects and scorer normalization are disclosed in the study.

The product-scoped provider-free check passed 32 cases, 17 mutations and 65 unit
tests. The full repository check passed 642 unit tests and its other offline
gates in a Git-listed working-file snapshot. Seven runtime/metadata hashes match
the final live pin and working tree; README/CHANGELOG updates are distinguished
from that runtime binding. The output smoke uses final 2.1.5 generation, while
the three image-free probes bind C's identical SKILL body only, with reference
differences disclosed. No image-edit or Codex live execution was retested.


## Focused requirement-scope repair, 2.1.6

The [focused repair record](../../../research/2026-10-image-focused-repair/README.md)
keeps the unsuccessful Grok review attempts, the content-pinned Codex comparison,
and final delivery separate. On three known sources, Codex 2.1.5 rejected one
valid partially overlapping leg; 2.1.6 retained it while both detected the actual
count and occlusion failures. This is a targeted regression, not a statistical
quality claim. Three final assets passed critical/composition checks; boat clay
texture remains unverified. The drawing route was the user's explicit Grok choice.

The 2.1.6 body-bound Grok smoke covered discovery, explicit/implicit read-only
activation, casual boundary and actual project output. Activation probes precede
the final rubric refinement; the output run read the final rubric. Native body
expansion removed one trailing newline, independently matched without retries.
All generated media and raw receipts stay private. Existing offline fixtures test
routing, permissions, metadata and file facts; no string-matching vision test was
added to imply that those fixtures prove model perception.

## Fresh transfer and one stop-rule repair, 2.1.7

The [fresh transfer record](../../../research/2026-10-image-fresh-transfer/README.md)
compares four new requests with no skill versus pinned 2.1.6 using shared first
images and equal per-request caps (one initial plus one conditional correction).
Both retained all three verified valid originals. The skill held on an ambiguous
key feature despite available repair authorization; no skill corrected it.
Source count/occlusion failure denominators were zero, so no detection-rate gain
can be inferred. The disputed key's exact fail/unverified label remains explicit.

One 2.1.7 development retest separates an unverified acceptance state from an
eligible targeted correction. It retains the three valid originals and corrects
the key, restoring four usable final assets and tying the ordinary workflow.
The retest is not a new transfer sample or proof of statistical superiority.
The full actual drawing prompt, final files and independent visual checks are
retained privately. Runtime SKILL/reference bytes match the tested candidate;
README/CHANGELOG reporting changes follow the results.

The refreshed native Grok smoke reuses the candidate's actual project edit and
three image-free explicit/implicit/near-miss probes. No extra image is generated
for host checking. The corrected renderer loads the skill for this smoke whereas
the no-skill renderer does not; both send their supplied correction prompt exactly.
Requested and measured ratios match, although only the no-skill edit explicitly
sets the optional aspect_ratio argument. Provider-free checks remain separate
from observed image quality.
