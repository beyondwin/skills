# Korean technical writing: testing superiority

[한국어](README.ko.md) · [Previous study](../2026-10-writing-readability/README.md)

**Superiority was not established. The personal installation remained 0.2.2 when this study ended.**
A [later personal-language revision](../2026-10-writing-plain-language/README.md)
installed0.5.1 under separately declared personal-use criteria; it does not turn
this comparison into a passed superiority test.
The 0.3.0 candidate received more favorable comparisons than unfavorable ones, but
failed both prespecified comparison thresholds. One of 24 planned judgments timed
out. This is insufficient evidence of superiority, not evidence that the skill has
no effect. Later development corrections cannot inherit the 0.3.0 measurements.

## Frozen comparison

Twelve new synthetic tasks: explanation, procedure, handoff and measurement
interpretation, one of each per writer host. Each task was written with no writing
skill, frozen 0.2.2, and candidate 0.3.0. A different provider judged each trio in two
cyclic label orders, with balanced labels. Two judgments of one task count as one
unit. A win or loss requires both orders to agree; disagreements and missingness
remain undecided. No completed unfavorable answer was replaced.

|0.3.0 versus|Concordant wins|Concordant losses|Tied, order-discordant or missing|Exact one-sided tail on decisive tasks|
|---|---:|---:|---:|---:|
|No writing skill|7|1|4|0.03515625|
|Installed0.2.2|3|0|9|0.125|

The frozen rule required at least 8 wins, tail <= 0.025 for **each** comparison, a
complete primary batch, clean source fidelity, native regressions and installation
smoke. These conditions were not met. The timeout does not explain the failed
incumbent comparison: too few tasks favored the candidate even if the missing
judgment had been favorable. Do not reinterpret p=0.035 as a successful result
under an uncorrected 0.05 threshold after observing it.

[Design](design.md), [protocol](protocol.json), [cases](cases.json),
[scoring implementation](scoring-implementation.json), [results](results.json).
The scoring code was fixed before model judging; the decision rule and generation
resources were fixed before generation. Source tasks were authored by the same
agent as the skill. This is an author-designed holdout with one generation per
cell, not an independent population sample or a human study.

## What changed and what the review caught

0.3.0 emphasizes selecting evidence for the reader's question and connecting its
causal relationships. It did not reliably eliminate repetition. All three writers
produced longer outputs than with 0.2.2 and had higher median generation times:

|Writer|Characters, no skill /0.2.2 /0.3.0|Median seconds, no skill /0.2.2 /0.3.0|
|---|---|---|
|Codex|5,729 /6,132 /6,384|34.4 /34.7 /38.2|
|Opus|7,256 /6,438 /6,600|22.9 /28.2 /38.9|
|Grok|4,524 /4,288 /4,822|36.3 /123.4 /130.8|

Each row contains four tasks per arm. Length is not a quality score; timings are
single observations with concurrency/cache effects. Provider-reported usage and
cost estimates are retained in results; missing Grok billing information is not 0.

The author found an overbroad opening: a delete response was described as a
committed tombstone even though a missing object also returns that status. A later
paragraph correctly stated the exception. The judge called this minor, while the
author conservatively vetoed adoption. See [author audit](author-audit.json).

Both evaluator controls identified an obvious changed threshold and preferred a
faithful draft to its exact duplication. Nevertheless, substantive false positives
occurred: comparative70% to 90% wording was treated as a within-B historical claim,
and a 503 retry warning was treated as proof that 401 retry was safe. A monitoring
interface distinction was inferred from ambiguous source wording. Raw preferences
are unchanged; [adjudication](adjudication.md) records these limits. Passing simple
controls does not establish reliable natural-language judging.

## Development corrections

[0.3.1](revision/ko-technical-writing/SKILL.md) keeps conditions in opening answers,
removes unrelated lifecycle inventories, and distinguishes unknown sample
representativeness from established nonrepresentativeness. Two transfer cases were
run on all three writers, plus native commit, JSON and gitlink regressions.
All 9 calls completed; author source review passed 7 and rejected 2: Opus translated
authorization as authentication, and Grok turned unestablished subjective speed
improvement into a categorical statement that no relationship exists.

[0.3.2](final-candidate/ko-technical-writing/SKILL.md) corrects those technical-term
and uncertainty distinctions. Its frozen regression repeats the two transfer cases
on three writers and checks the exact native JSON contract. These are targeted
replays, not a fresh superiority comparison. All seven calls completed and passed author source checks; [final results](final-results.json).
Some awkward Grok phrasing remains. These checks do not prove naturalness or establish
the comparative quality of the final candidate.

[Revision protocol](revision-protocol.json), [revision results](revision-results.json),
[final correction protocol](final-repair-protocol.json).
No runtime model calls, global policies, supported products, host support or skill
names were changed. Candidate trees are historical experimental payloads.

## Runtime and limits

- Native Codex CLI 0.160.1: actual `gpt-6-astra`, high, from rollout turn contexts.
  Fresh HOME/CODEX_HOME, memories disabled, read-only fixture workspaces. Both skill
  arms read the pinned entrypoint and references; [native audit](native-audit.json).
  The existing proofreading skill is installed in all Codex arms, including baseline.
- Claude CLI 2.1.292: assistant messages report `claude-opus-5-5`; requested high
  effort is not independently reported. Inline payload, tools/MCP/native skills off.
- Cursor Agent 2026.10.01-e373342: init reports `Grok 4.7 256K Medium`; an immutable
  backend identity is unavailable. Fresh home/config/workspace and deny-all tools.
  Shared provider system instructions and authentication remain isolation limits.

The main round dispatched 62 CLI jobs and received 61 completed responses: 36 drafts,
23 of 24 judgments, and 2 controls. The missing Grok judgment reached 480 seconds;
no retry or model fallback was used. Conditional native regressions and installation
smoke for the rejected0.3.0 were not dispatched. Later correction tests have separate
ledgers. Across all three rounds, 78 jobs produced 77 completed responses;
[combined summary](study-summary.json). CLI dispatches are not HTTP requests or independent writing cases.

A private three-pair reading sheet compares the **installed 0.2.2 with no skill**.
It is for personal preference elicitation, selected after seeing results, with a
simplified common Markdown rendering and links removed. It is not a blinded human
benchmark. The user initially submitted **1: B, 2: B, 3: A**, which decoded to
one 0.2.2 selection and two no-skill selections. The same reader then clarified that
all pairs were hard to distinguish and all texts used terminology that did not feel
like terms people use. **The one-versus-two clear-preference interpretation is
withdrawn.** [Human preferences](human-preferences.json) retains the original labels,
artifact hashes and subsequent clarification. No formal itemwise tie ratings were
collected, and UI test clicks remain excluded.

The actionable observation is a lack of perceptible improvement and dissatisfaction
with terminology in both arms. The reader did not identify individual words. Author
inspection found candidates such as `UI 소비 코드`, `nullable이다`, and unexplained
`dual-write`, `outbox`, `dispatcher`, and `consumer`; these are author hypotheses,
not reader-attributed selections. A next revision should test familiar explanations
of the concepts while retaining identifiers and technical meaning, rather than assume
that translating every term or adding more rules establishes naturalness. Model
fidelity scores and reader-perceived naturalness require separate evidence. This is
one reader, three post-hoc pairs, no order reversal, no comprehension or timing test,
and no evaluation of 0.3.2. Installation remains unchanged.
The standalone file is in `/Users/kws/Downloads/ko_writing_reading_check_20261009/`.

## Reproduction

Offline, no credentials or provider calls:

```bash
python3 -m unittest discover -s docs/research/2026-10-writing-superiority -p test_summary.py -q
python3 docs/research/2026-10-writing-superiority/run.py generate /absolute/private/archive
```

Live calls require explicit user authorization. For one archive, run phases
sequentially: `generate`, `judge`, `control`; `regression` and `smoke` are conditional
on the adoption gate. Add `--execute` to dispatch. IDs cannot be rerun automatically.
The separate correction runners are `repair.py` and `final_repair.py`, also dry-run
by default. Both import pinned historical host runners rather than alter them.

Reproduce exported aggregates from the private archives with `summarize.py` and
`summarize_repairs.py`; the latter verifies native reads, prompt/response hashes,
auth cleanup, JSON shape and author grades. It does not independently validate the
author's semantic judgments. All raw prompts, responses, receipts, and temporary
authentication stay outside Git. Public files contain only synthetic sources,
hashes, aggregates and author conclusions. See [verification](verification.md).
