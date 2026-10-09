# Review and adjudication log

Recorded on 2026-10-09. No additional provider calls were made for these reviews.

## Independent roles

- A separate agent designed and ran the offline boundary probes without modifying
  the supplied tools.
- Provider operators ran the same hashed prompts without grading outputs.
- A separate model reviewer received shuffled task/output records without host or
  condition labels. It reviewed 48 outputs, then 23 additional outputs.
- The parent reviewed the same masked outputs against source meaning and resolved
  one disagreement before opening the label map.
- A separate report auditor checked claims and aggregate arithmetic after the draft.
  This is model-based review with shared-bias limits, not a human reading experiment.

## R020: supported fact versus the frozen scope criterion

The commit task's frozen invariant was `no interval/OAuth claim`. R020 mentioned
that the interval remains 300; the unchanged line is present in the staged diff.
The first reviewer marked semantic failure. The parent judged it supported factual
context and changed the semantic judgment to pass, retaining an overhead penalty.

The report auditor correctly noted that this relaxes the registered wording even
if the semantic reasoning is defensible. The initial draft called it only a scoring
correction, which understated the change. Final reporting therefore distinguishes:

- **Primary, strict registered scope:** fail. Opus compact is 6/8, versus 7/8 baseline.
- **Secondary factual interpretation:** pass for this item. Opus compact is 7/8.

Both interpretations are retained in `live-results.json`; neither the original
case nor the first grader's private record was overwritten. A strict no-regression
claim for the compact policy is rejected. This correction changes the confidence
claim, not the raw generations or the proposal to test only missing rules later.

## Other report corrections

- `median_wall_seconds` was renamed `matched_median_wall_seconds`. Grok's timing
  comparison uses seven shared cases, while token totals include every completed
  call in each condition. The arithmetic was correct but the old name hid the base.
- The inherited 78.54% sentence-length reduction now names its unit: mean Korean
  whitespace-delimited eojeol per sentence, 27.429 to 5.885. Character counts are
  a different measurement.
- Secondary rubric scale details were fixed after generation started, before
  grading. They are labeled exploratory; primary case predicates were frozen before
  generation and the strict interpretation is preserved as described above.

## Remaining uncertainty

Opus's unsupported “skip reasons were not checked” statement occurred under the
baseline and compact conditions, but not the full condition. One trial cannot show
that a specific rule caused the difference. A targeted rule separating missing
evidence from known non-execution remains an untested proposal. No extra generation
was used to produce a cleaner-looking result.
