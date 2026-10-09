# Korean technical-writing policy: evaluation and recommendation

Date: 2026-10-09. [한국어](README.ko.md).

Recommendation: pilot a small shared policy only where existing instructions have
a demonstrated gap. Keep `korean-writing-editor` focused on proofreading. Do not
install the supplied kit wholesale, create a fourth supported product, or make its
literal checker a mandatory gate from this evidence.

This is a proposal backed by bounded experiments, not a deployed behavior change.

## Find the reason, method and evidence

| Record | Question it answers |
| --- | --- |
| [Learning case](../../learning/cases/2026-10-09-korean-writing-policy.md) | Why did this work start, what alternatives were considered, and what is being recommended? |
| [Method](method.md) | Why each experiment, how it ran, what was authorized, and what cannot be inferred |
| [Frozen protocol](protocol.json) | What was decided before model generation, including hashes and decision gates |
| [Cases](cases.json) | Exact synthetic tasks and semantic invariants |
| [Compact candidate](core-candidate.txt) | The exact short policy evaluated, not an installed skill |
| [Reproduction results](reproduction-results.json) | What the supplied tests actually reproduced |
| [Offline probes](offline-results.json) | Per-probe rationale, expectation, observation and source fingerprint |
| [Live results](live-results.json) | Per-run identity, hashes, grades, usage and aggregate results |
| [Provenance](provenance.json) / [review log](review-log.md) | Retained harness/grade fingerprints, independent criticism and scoring corrections |
| [Design decision](design-decision.md) | Responsibility split, rejected options, tool repair priorities and follow-up gates |

Runners and prompt reconstruction are in [harness/](harness/). Raw prompts, outputs,
receipts and logs are retained in a separate local archive outside Git. They include
private supplied instructions and are not public evaluation fixtures. Public records
contain their hashes and synthetic grading summaries, not whole transcripts.

## What ran

**E1 — supplied evidence reproduction.** All 57 package checksums matched. The two
suites ran on a copied tree with stock macOS Python 3.9.6. The kit passed 41 tests;
its 26 paired cases are included in that suite, not 26 additional independent tests.
The earlier research reproduced 68/68 anchor checks and 24/24 linter expectations.
Both artifacts reproduced their eight undetected semantic mutants.

The supplied before/after examples changed from 14 to 61 sentences while total
characters went from 1,538 to 1,537. Mean whitespace-delimited Korean eojeol per
sentence fell from 27.429 to 5.885; that 78.54% reduction is
not a measured improvement in reader comprehension.

**E2 — independent local boundary probes.** Fifteen synthetic probes produced four
passing positive controls, eight concrete defects, one unsupported numeric-grammar
gap, and two documented/evidence limitations. This is adversarial case discovery,
not an estimated real-world failure rate.

Important examples: `최대10회` changing to `최대20회` bypasses numeric preservation;
duplicate contract keys can erase protected spans; malformed contract types crash
with the wrong exit status; directories and non-string YAML descriptions can pass
preflight; `diff.ignoreSubmodules=all` can hide an actual staged gitlink change.
The checker already disclaims semantic proof, but these examples concern even its
narrow literal/configuration/evidence responsibilities.

**E3 — approved live writing pilot.** Eight tasks × three conditions × three hosts:
72 dispatches, 71 generated answers. Grok's `readme--core` failed before generation
because the first isolated home lacked authentication. It was not retried or counted
as a writing failure. The 71 completed runs showed zero tool calls.

Runtime identities were Codex CLI 0.160.1 / `gpt-6-astra` high, Claude CLI 2.1.292 /
`claude-opus-5-5`, and Cursor CLI 2026.10.01-e373342 / `Grok 4.7 256K High`.
Opus high was requested but actual effort was not exposed in its receipts. Grok
exposed High in its runtime model display name, not a separate effort field.

## Results

The table uses the strict preregistered preservation, scope and format criteria,
out of generated answers. The missing Grok core result is unavailable, not passed.

| Host | Baseline | Compact policy | Full inlined kit |
| --- | ---: | ---: | ---: |
| Codex Astra | 8/8 | 8/8 | 8/8 |
| Claude Opus | 7/8 | 6/8 | 8/8 |
| Cursor Grok 4.7 | 8/8 | 7/7 | 8/8 |

Two Opus failures concern the same task: it said that the reasons for skipped
tests had not been checked, although the evidence stated only the pass/skip counts.
Missing evidence about an action is not evidence that the action was not performed.
The full-kit answer did not make that unsupported claim. This single observation
is useful for a targeted follow-up, not proof that the full kit is more reliable.

A separate blinded grader reviewed all 71 outputs. The third strict failure is
Opus compact's commit message, which mentioned the unchanged interval despite the
frozen invariant `no interval/OAuth claim`. Before labels were revealed, the parent
allowed that statement as a supported fact shown in staged diff context. An
independent report audit identified this as a relaxation of the registered scope
wording, not just a grading correction. The primary table retains the failure.
Under the secondary factual interpretation compact is 7/8; both judgments remain.
The compact condition therefore does not satisfy a strict no-regression gate.
All 71 answers passed the format
check; all nine JSON answers also passed a deterministic shape/value check.
Code fences around a commit message were allowed because the task did not explicitly
require raw plain text. Grok's numbered procedure placed its failure branch after
the successful notification step in one answer: the condition remained correct,
but clarity was lower. Clarity/overhead ratings are exploratory model judgments.

| Host | Output characters, baseline / compact / full | Comparable cases |
| --- | ---: | ---: |
| Codex | 1,098 / 1,104 / 1,104 | 8 |
| Opus | 1,685 / 1,566 / 1,452 | 8 |
| Grok | 854 / 813 / 822 | 7; README excluded from every condition |

Shorter is not necessarily better. Codex had no observed quality gain from either
added policy. Opus and Grok show some shorter outputs but uneven overhead. There is
no basis here for a model ranking or a universal benefit claim.

All resources in the full condition were deliberately inlined. Opus CLI cost
estimates for eight calls were $0.097302 baseline, $0.113742 compact, and $0.531143
full. These are not billing statements. The full condition also consumed more
reported input tokens on Codex and Grok. This is an instruction-content comparison,
not a comparison with an efficiently loaded native skill. Prompt language, content
and length differ together. Usage and latency across hosts are not normalized.

## Proposed adoption

1. Preserve requested language, format, meaningful conditions and technical literals.
2. Distinguish proposal, implemented change, observed check and deployment.
3. Keep “not provided,” “not known,” and “not performed” distinct.
4. Lead with the answer and include only the structure the task needs.

Deduplicate these concerns against current instructions before adding anything.
The third item is an evidence-based refinement suggested by this study; a revised
prompt containing it has **not** been retested. The frozen compact candidate remains
unchanged so the experiment stays reproducible.

Use a task-specific reference only if repeated substantial document/PR/handoff
work needs it. A native skill requires separate discovery, actual file-read and
tool-use tests. Repair the demonstrated checker defects before using those tools as
automation. Teacher-facing product prose and source-text proofreading keep their
own contracts.

## Limits and stopping point

One generation per case, eight synthetic tasks, strong task prompts, model-based
grading, different host system prompts, and no human comprehension study. Codex's
four built-in system skill descriptions remained available; no personal writing
skill or memory was injected. Opus safe mode disabled custom skills/tools. Cursor
retained tool schemas but a deny hook blocked execution; its CLI stripped only the
final prompt newline. Missing transport evidence is preserved.

The approved generation budget is exhausted; no repeat was used to tune away a
failure. Existing product behavior and versions are unchanged. Follow-up questions
are native discovery and whether the targeted evidence-status refinement works on
unseen tasks. See [verification](verification.md) for actual repository checks and
the limitation in the original checkout.
