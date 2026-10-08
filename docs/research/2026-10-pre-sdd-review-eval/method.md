# Pre-registered Pre-SDD Review comparison

Registered 2026-10-08 before the comparative calls. Source commit:
`f4e659b23f2f808ed6cce0e86de4bc1043526e99`. Product: pre-sdd-review 6.1.2.
Identity probes are excluded from evaluation. Raw receipts, isolated auth copies,
and transcripts stay outside Git, under `/tmp/psdr-study-20261008`.

## Question and conditions

Does the installed procedure improve actionable review quality enough to justify
its extra work compared with an ordinary competent review on the same model?
The user authorized local live comparisons on Grok Build 4.7/high, Claude Code
Opus 5.5/high, and Codex 6.1 Sol/high. Codex 6 Astra/high is an additional reference.
Authentication failures are missing observations, never quality failures or zero cost wins.

- `plain`: a fresh session receives the review objective and common boundaries,
  no skill, no delegated review.
- `skill`: the same objective, explicit review-only invocation of the frozen full
  skill, with its native independent reviewer and evidence lifecycle.
- `protocol`: diagnostic ablation; one fresh reviewer reads only the unmodified
  reviewer protocol, without controller, recorder, or additional delegation.

The first two measure the whole procedure, so a quality difference cannot be
attributed to instruction text alone. The ablation helps separate content from
orchestration; it does not isolate every individual rule. Host settings and model
identities are reported separately from quality. Non-Codex results are exploratory
and do not extend the supported-host registry.

## Inputs, isolation, and sequence

Four newly authored stdlib Python fixtures live in `harness/fixtures/`. Each run
receives a fresh Git repository, identical bytes for its fixture, and no oracle.
The oracle and scoring rules live outside the model's working directory and are
not named in its prompt. There are no inherited conversations or previous run results.
Fixtures are synthetic; no private project source is sent or saved in Git.

| Case | Purpose | Expected unresolved defects | Expected verdict |
| --- | --- | --- | --- |
| a | Clean negative control, explicit edge cases | 0 | READY |
| b | Missing requirement and invalid verification command | 2 | REVISE |
| c | Explicitly deferred product choice | 1 | BLOCKED |
| d | Cross-file exact-key consumer and undiscovered nested tests | 2 | REVISE |

Stage 1: four fixtures x plain/skill x four requested/reference engines, one run
per cell (32 possible cells). Launch in balanced deterministic shuffled order;
at most two simultaneous cells per host, four for the two Codex model families.
Use 15 minutes per cell as a completion bound; retain timeouts as execution failures.
Do not retry a semantic failure. Record infrastructure retries separately.

Stage 2: repeat cases a and d for plain/skill on available engines, and run
protocol on a and d. These cases are selected before outcomes: a measures false
positives and d is the harder grounded defect case. Maximum 24 additional cells.

Stage 3: default document repair and closure on case b, plain/skill, using
available Sol, Claude, and Grok engines (up to six additional calls). Both arms
may edit only design and plan; no implementation. Check that both original
defects were repaired, no approved intent was changed, and claimed closure is
backed by actual fresh review. This stage is distinct from detection quality.

## Scoring and decision rule

Manually match findings to causal defects, with concrete evidence required.
Merging/splitting wording does not gain or lose credit. Count duplicate findings
once. Correct observations outside the oracle are adjudicated against the source,
and recorded separately; do not automatically label them false positives.
Generic advice, stylistic preferences, or requirements the design excludes are
false positives only if presented as material blockers or required changes.
Report format compliance separately; ordinary review need not use PSDR labels.

Primary: per-case known-defect recall, false positives, and semantic verdict.
Also: authority violations, out-of-scope writes, missing evidence, grounded
counterexamples, full-procedure compliance, time, tokens/cache, and provider-reported
cost when available. Cost is not inferred from stale pricing; hosts with different
usage semantics do not get a fabricated dollar comparison. Child usage and
controller usage must be separated or explicitly marked as incomplete.

The study is small and fixtures share structure. Do not treat five defects as
five independent experimental subjects, or claim statistical superiority from
one run. Report paired outcomes and disagreement/repeat spread. Differences below
about two standard errors are no measured difference, not equivalence.

Retain the skill for a scenario only if a repeated practical quality or process
benefit is observed without a new authority/scope failure. Prefer ordinary review
for simple cases when quality is tied and procedure overhead dominates. Consider
a product change only after a reproducible failure, a minimal candidate, and a
fresh held-out or regression run; do not simplify the shipped skill merely because
one small fixture reaches a ceiling. Product deletion, host support expansion,
and automatic implementation are outside this experiment.

## Limits planned in advance

Synthetic, small repositories; no measured downstream production defect rate;
no inference about large campaigns, long plans, authentication/security or data
migration review, repeated READY reuse, or real implementation productivity from
the four discovery fixtures. Report these gaps even if all scores are perfect.
An unavailable requested model remains explicitly not measured.

## Additional falsification registered before its live calls

A static audit found that the reuse change list cannot see a previously reviewed
untracked source file after that file is deleted. Test this separately from the
quality matrix: case a's plan names `python3 tools/check.py`; an untracked real
runner delegates to the existing unittest command. Obtain a real READY with
6.1.2 on Sol/high, delete only the runner, and send the identical request in a
fresh session with the same repository and recorder home. HEAD and document
hashes remain fixed. Check whether reuse overlooks the now-missing verification
command. This is an exploratory lifecycle counterexample, not another independent
sample for the core recall scores. Raw location: `/tmp/psdr-reuse-live-20261008`.

## Exploratory clarification test registered after initial grading

The initial label-masked grader identified one Claude skill false positive on c:
the plan already prescribes exact tests by input category and an invariant fixes
their expected values, but the reviewer demands enumerated literal examples.
Before any candidate call, define one protocol-only addition: evaluate checks as
specified; a counterexample that violates a prescribed assertion does not prove a
gap; choosing concrete data from named categories is implementation detail when
approved behavior determines the result.

Run two additional paired full-skill Claude/high reviews of c with frozen and
candidate resources, plus one candidate d regression check. Keep this separate
from the main scores. Record both protocol hashes (SKILL.md alone is unchanged).
Do not ship the clarification unless the failure repeats on frozen text and the
candidate shows a consistent benefit without missed real defects. This small
follow-up cannot establish statistical improvement; a non-repeated failure favors
leaving the shipped product unchanged. Raw results: `candidate-cells/` under the
external study root.

After grading the pre-registered clean repeat, the same unnecessary-prescription
shape also rejected a (test method names instead of literal test data). Before
running that input on the candidate, add one held-out candidate a check with the
unchanged paragraph. Keep this out of the core matrix. A clean or defect-detection
regression prevents shipping the candidate; six follow-up calls is the cap.

Before any shipped change, run the same unchanged candidate on a and d with the
supported Codex Sol/high host (two smoke calls, separately reported). These check
no immediate clean-case or real-defect regression on the supported host; they do
not expand the Claude experiment's sample size or establish a general quality gain.

## Execution amendments and attrition

Claude's variadic `--disallowedTools` initially consumed the positional prompt.
Four plain calls failed before inference; a `--` separator fixed the harness.
Those attempts remain outside the comparison and were retried once.

Grok's optional `--tools` list used wire names that the CLI could not map to its
internal agent tool allowlist. The first controller attempts therefore could not
obtain a working child. They are harness failures, including their spent tokens,
not skill-quality or valid latency observations. Removing that optional restriction
and exercising an actual fresh child verified both parent and child as
`grok-4.7-build/high` before restarting the matrix. The plain/protocol prompt and
native no-subagent option remain in place; inspect actual dispatches as well.

Prospective resource stop, added while the corrected A/B calls are still running:
if both corrected full-skill simple cases hit the registered time/turn cap despite
a working child facility, cancel queued full-skill repetitions on that host and
retain them as not-run after feasibility failure. Continue ordinary/protocol cells.
Do not reinterpret capped calls as semantic misses, or keep repeating the same
runtime failure in search of a better result.

Post-run bookkeeping correction: the runner originally populated
`protocol_sha256` only for the protocol arm. The final summarizer derives it for
full-skill cells from each saved resource copy, and candidate fingerprints are
checked against the independently saved manifest. The reproducible runner now
records that digest at setup for both arms. This changes no prompt or model call.
