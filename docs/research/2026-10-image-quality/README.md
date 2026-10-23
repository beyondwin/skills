# Image quality: ordinary generation and image-workbench

Date: 2026-10-22. Environment: macOS, Grok CLI 1.0.62 (1474f9cbdd91).
The observed agent model was `grok-4.7-build`, effort `high`; `grok-4.7` was
the requested alias. The image tool did not identify its underlying image model.

## Question and decision rule

Does image-workbench improve generated images beyond the ordinary host workflow,
and which changes improve usable project delivery? The ordinary arm received the
same full brief, project constraints, native image tool, and call budget. It was
not a deliberately weak raw-prompt baseline. Grok's bundled `imagine` instructions
were available to both arms; only the project skill differed.

The pre-registered development matrix was three synthetic briefs, two independent
runs each, per arm: a tea hero with four visible table legs and an empty left 40%;
a paper boat with three fully visible leaves; an amber bottle on a 4:5 canvas.
Every first-candidate run had a one-call budget. Same-case runs used separate
homes, conversations, fixed payload copies, and no shared memory or user skills.
Discovery found only image-workbench in skill arms and no user skills in plain.
The native tool list was not fully filtered by `--tools`; actual calls were audited.

Two separate model reviewers saw randomized file identifiers, the original brief,
and its critical checks, without condition labels or generation verdicts. They
opened every evaluated image. Four craft dimensions (geometry/artifacts,
material/light, composition, specificity/coherence) used a 1–5 scale. The aggregate
is the mean of both reviewers' four scores. Complete compliance also requires the
requested canvas. Disagreements remain visible; uncertainty is not a verified pass.
These are model judgments, not a human preference study, and reviewers saw batches
arrive over time even though condition labels were hidden.

A craft improvement required a mean paired gain of at least 0.5 points and more
than two standard errors, with no overall or per-brief compliance regression.
Standard errors use three brief-level mean differences, not six independent domains.
Missing results are missing, not zero scores. This is an exploratory development
comparison, not a powered superiority test. Final corrections and transfer probes
are separate from the fixed first-candidate comparison.

## Ordinary versus version 2.1.2

| Measure | Ordinary | image-workbench 2.1.2 |
| --- | ---: | ---: |
| Generated final images | 6 | 6 |
| Mean craft, out of 5 | 3.98 | 4.17 |
| Both reviewers confirm all critical conditions and canvas | 2/6 | 2/6 |
| Image tool calls, including rejected calls | 8 | 8 |
| Median elapsed seconds | 81.53 | 123.13 |
| Median agent turns | 6 | 8.5 |

The craft difference was +0.1875, with a brief-cluster standard error of 0.19094;
it met neither the 0.5-point threshold nor the two-standard-error threshold.
There is **no measured overall craft advantage** by the pre-registered rule.
The tea case favored the skill, while boat and bottle differences were small.

All four bottle runs sent unsupported 4:5, received HTTP 422, and retried at 3:4,
exceeding their one-call budgets. Each produced one image, not two. Their returned
pictures are retained for descriptive craft scoring, but these are protocol
violations, not clean one-call canvas comparisons. The corrected first-candidate
analysis must not hide these failures or silently replace them with another sample.

Elapsed time includes provider and local execution variability and partially
overlapping batches. It is descriptive, not a causal latency benchmark. A plain
tea run spent 14 turns on inspection; the skill did not make every run slower.
Reported agent cost does not establish the image provider's price or actual billing.

## Revision and final adoption

The first revision translated constraints into view/placement choices, separated
count from full visibility, and checked supported ratios before generation. It
was tested in six pinned first-candidate runs. A lower three-quarter view still
hid a leaf behind the boat rim, and one tea image showed only three legs. Therefore
broad first-prompt rewriting was not adopted as a quality improvement.

Its mean craft was 3.875/5, down 0.2917 from 2.1.2. Complete compliance was 3/6,
with one additional disputed boat result counted as unverified, not a pass.
Tea compliance fell from 2/2 to 1/2, violating the no-per-brief-regression rule.
Both revised bottle runs delivered 832×1040 (4:5) through an explicit crop from
a supported source ratio, using one image call each. That is useful output-contract
evidence, but not an aesthetic gain: bottle craft averaged 3.8125 versus 4.0 in
2.1.2. Conversion also added work; revised median elapsed time was 164.75 seconds.

The adopted 2.1.3 preserves a detailed first prompt. Spatial advice applies to an
observed failure, with an overhead option for complete container contents when
no viewpoint is fixed. It retains distinct count/visibility checks and explicit
supported-ratio conversion or hold. This restores the documented constraints;
it does not promise that the image model follows every instruction.

An initial targeted boat correction still hid a leaf; both reviewers rejected it.
An unseen nest illustration, selected before any generation, passed both reviewers'
critical and canvas checks. These two single runs are not another six-case matrix.
Only one of the two preselected transfer briefs was executed, so unseen coverage
is one brief. The lamp transfer brief was not run.

After the original 24-call ceiling was reached, a dated development amendment
allowed two further boat calls with a precisely vertical view. This amendment was
recorded and communicated before the calls. They are excluded from the fixed
comparisons; the initial failed correction remains in the results.

The two final calls both exposed the leaves. One generated four leaves and failed
count; the other satisfied all critical and canvas checks according to both
reviewers. Craft was 3.75 and 4.0/5 respectively. Neither is evidence of reliable
repair or aesthetic superiority. The successful image still used an oblique view:
acceptance depends on the requested visible contents, not obedience to a proposed
camera instruction. The generator correctly rejected the count failure and reported
the successful image's camera/style limitations.

The completed study used **26 image tool calls: 22 generated images and four
rejected calls**, plus six read-only model probes (28 sessions in total). All
sessions ended with a final response, all pinned payloads remained unchanged,
and all temporary credential copies were deleted. No image edit calls were made.

| Separate follow-up | Both reviewers' complete compliance | Interpretation |
| --- | --- | --- |
| First targeted boat correction | 0/1 | Near rim still hides a leaf |
| Unseen nest transfer | 1/1 | One new brief only; craft 4.0/5 |
| More precise vertical-view corrections | 1/2 | Count regression remains possible |

### Pinned resource identity

Each manifest maps installed relative filenames to SHA-256, sorted and serialized
as JSON with compact separators. The table gives the SHA-256 of that manifest.
Each pinned payload contains 11 files. These are development snapshots, not
published releases; multiple candidate bodies used the proposed version 2.1.3.

| Payload | Manifest SHA-256 |
| --- | --- |
| Original 2.1.2 | `6516e4da32138fe9a166efeac52f362d8eeffa917544ae4b6574cf6e1cc3811a` |
| Rejected broad first-prompt rewrite | `11a36181652741fdc0f0217331eee49dc98030c56135479de7b63d77a384cf74` |
| Adopted body, initial correction reference | `0fcd8124e4bd93d3dc229adcf5dc1e2deab1cb5e4751658cf219d6d6b4ff0275` |
| Final reference with precise vertical correction | `8390d30aca04dc40f50d9a1c401fff1eab6f6b206c49717833b06a413dd53925` |

The adopted/final SKILL body binding is
`9b6eefa323753cde7458b1b24d77bcb7341859acd8b4aa14c90678ebc57b802a`.
The final image-spec reference hash is
`b555ec00c59f1c0a08e1b28e7214c6f829c4c47e8da3ccfe5134c14fad9828b3`.
Final sessions are listed in the
[smoke record](../../../tests/products/image-workbench/live/smoke-record.json).
The body smoke alone does not bind a changed reference.

## Practical strategy

1. Start with the actual use, subject, count, canvas, necessary empty regions,
   full-visibility requirements, and desired materials/light. Keep a detailed
   brief intact for the first candidate.
2. Check native tool capabilities before spending a call. Unsupported canvas
   values require an explicit safe conversion, an authorized approximation, or
   a hold. Inspect the delivered file, including any deterministic conversion.
3. Treat required conditions as gates. Score craft only after identifying crop,
   occlusion, wrong counts, unwanted marks, and canvas mismatches. Countable
   objects are not necessarily fully visible objects.
4. Correct the physical cause of an observed defect: framing, camera or placement.
   Preserve the subject, palette and intended style. An extra style paragraph is
   not evidence that the defect was addressed.
5. When the user authorizes variants, keep every candidate and choose among those
   meeting critical conditions. Record the selection budget. Selected best images
   illustrate achievable output; they do not estimate average improvement or
   prove that extra sampling is more efficient than a correction.
6. Finish with the accepted file or an honest remaining failure. This study
   supports explicit constraint checks and conditional repairs, not a universal
   prompt formula or a guaranteed quality level.

Two read-only audits of the same boat image tested the distinction between
visibility and count: the full-visibility brief was rejected, while a control
allowing overlap but requiring three countable leaves was accepted. Neither audit
changed the source hash or generated an image. The audit instructions used an
earlier revision with the same quality-rubric bytes. Fresh explicit brief and
casual-request routing probes bind the adopted SKILL body; they produced no images.

## Evidence and limitations

The original checkout's `python3 scripts/verify.py` stopped at discovery because
five ignored retired product/test directories were still present. They were
preserved. A temporary copy of all current tracked files and new non-ignored
documents, with its own Git index for packaging checks, passed the full command:
642 unit tests, product contract/mutation checks and Python compilation; exit 0.
That is an offline check with no provider calls, run on macOS with Python 3.14.
The final smoke-record metadata and document-only edits were checked separately.
The generic skill-creator validator rejects the already-existing `compatibility`
frontmatter in both baseline and modified SKILL; the repository contract requires
that field, so it was retained. No runtime Python code changed.

Full resource manifests, synthetic briefs, generated final images, and independent
judgments are retained in a local ignored evidence bundle. Native transcripts and
provider receipts remain in temporary run directories outside the repository,
separate from the shareable bundle. None are committed. This repository carries
the method and sanitized results, so it cannot independently re-score the image
pixels without the local bundle. The baseline Git revision was `c2ddf61`.

An exporter initially selected a bottle's intermediate source instead of its final
requested destination. The mistaken `img211` score remains in the local record as
withdrawn; the actual delivered file was exported and judged as `img669`. The
other 16 then-existing exports matched their requested destinations. The scorer
also normalizes the reviewers' two canvas-key spellings and checks the verdict
against pixel dimensions; absent verdicts are errors, never failed images.

The official [xAI prompting guide](https://docs.x.ai/developers/model-capabilities/images/prompting-guide#write-the-subject-first)
was consulted on 2026-10-22 for subject/count/camera guidance. Its API settings
are not treated as Grok CLI parameters or proof of the image backend. The local
results, including the unsuccessful first revision, determine the adoption.

This work does not establish a general aesthetic advantage, seed-matched causality,
human taste, edit preservation, series identity consistency, alpha output, or Codex
live behavior. No deployment or release was performed.
