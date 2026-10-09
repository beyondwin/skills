# Korean technical writing: readability revision

[한국어](README.ko.md)

Current personal skill: [Readable 0.6.0](../2026-10-readable-rename/README.md),
invoked as `$readable`. Names, paths and results below describe the historical study.

This study targets the user's actual product goal: a personal skill that helps a
reader understand a technical explanation on the first read, while preserving meaning.
The [previous pilot](../2026-10-personal-writing-pilot/README.md) measured evidence
handling and native skill use, not reader comprehension. Its frozen payload remains
unchanged. This directory contains the separate 0.2.0 candidate and evaluation.

## Method fixed before generation

[protocol.json](protocol.json) pins both complete payloads, the six synthetic tasks,
the generation and judging code, and the promotion rule. [cases.json](cases.json)
contains authored source notes, requests and decision questions. The generator sees
only the source notes and request, not the question/answer key. Each task runs with
no writing skill, version 0.1.0, and version 0.2.0. All use fresh isolated Codex homes,
memories disabled and a read-only workspace. The existing proofreading editor is
available in each home as a competing skill. The prohibited superpowers plugin is
not installed in these runs.

The candidate adds reader-question ordering, explicit causal connections, concrete
Korean verbs, stable references and a silent revision pass. It does not impose a
sentence-length target, ban headings or require an extra model service in daily use.
The skill remains a personal installation, outside the three supported repository
products.

Two fresh model judgments per task receive all three drafts as A/B/C; the second
reverses their order. They receive the request and source for correctness checking,
but no skill text, arm labels or acceptance threshold. They score orientation,
connections, naturalness and economy independently of factual accuracy. Their
question answers are source-assisted judgments, not reader-comprehension results.
Separate source-blind reader probes answer three questions each from two tasks and
two skill versions. These check answer availability, not human reading speed.

Promotion requires the predeclared absolute quality and regression gates. A claim
of observed preference improvement has a separate, stronger gate. Neither gate
establishes a statistically generalizable improvement or human comprehension gain.

## Reproduction and privacy

Live calls require the user's authorization. The default invocation is a dry run:

```sh
python3 docs/research/2026-10-writing-readability/study.py generate /path/outside/git
```

To execute, add `--execute --auth /path/to/auth.json`. Run phases `generate`, `judge`,
`regression`, `reader`, then `smoke` only after installing the candidate and passing
its pre-install gates. Every phase shares a 40-dispatch ledger; an existing job
cannot be dispatched again under the same ID. A transport retry must receive a new
ID and retain identical input. Runtime identity comes from rollout turn_context,
not the requested model setting. The harness removes each copied credential.

```sh
python3 docs/research/2026-10-writing-readability/summarize.py /path/outside/git --out /tmp/results.json
```

The summary checks hashes, coverage, credentials, installed payloads and judge
schemas. Full transcripts are audited because compact command events can omit
failed compound commands. Raw prompts, model outputs and receipts stay outside Git;
only synthetic inputs, aggregate grades, hashes and decision records belong here.

## Source basis and limits

The [official ASD explanation](https://www.asd-ste100.org/about.html) describes
understanding technical instructions as the goal and consistent terminology as a
mechanism. Its [FAQ](https://asd-ste100.org/STE_faq.html) distinguishes procedural and
descriptive writing from general prose. This skill adapts those principles for
Korean; it does not reproduce the dictionary, enforce English word limits, or claim
ASD-STE100 compliance. The Korean reader/editing procedure is our design hypothesis,
not an official standard requirement.

A single model family generates and judges all drafts; masking cannot eliminate
shared preferences. The author also reviews accuracy. Order reversal probes position
sensitivity, not independent human agreement. Six synthetic tasks cannot establish
human reading-time gains, personal long-term usefulness or other-host support.

## Amendments and additional providers

[Masking amendment](masking-amendment.json): before the first judge dispatch, source
citation paths exposed an arm name. `masked_evaluation.py judge` and `reader` replace
only the environment path prefix with `/source/`. Text and grades are unchanged;
private receipts preserve both hashes. Use this wrapper for those two phases.

[Transport follow-up](followup.json) retains capacity failures and identical-input
retries. Missing answers never count as semantic losses.

The user subsequently requested Claude CLI Opus and Cursor Agent Grok.
[External protocol](external-protocol.json) adds six baseline/candidate pairs per
provider, cross-provider masked judgments and diagnostic scorer controls, within
40 additional dispatches. `external.py generate` executed Opus and the first Grok
High job. After High timed out, [the follow-up](external-followup.json) starts a
separate complete Grok Medium condition through `external_followup.py generate-medium`.
Use that runner for `judge` and `control` too. All commands require an output path
outside Git and `--execute` for live calls. `external_summary.py` reproduces the
sanitized evidence. No successful High draft is pooled with Medium.

The skill and document reference are supplied inline in the external CLI study.
Tools and native skills are disabled. This evaluates writing behavior, not native
installation, routing or file access on Claude/Cursor. No host-support claim follows.
Opus judges Grok outputs and Grok judges Opus outputs; both see source evidence.
The controls inject a false completion claim and severe repetition. Passing them
shows sensitivity to conspicuous defects, not subtle stylistic discrimination.

## Codex 0.2.0 comparison results

[results.json](results.json) reproduces 40 dispatches, 37 completed answers and
40 unchanged workspaces. Three attempts ended with model-capacity 503 before an
answer. The cache judge and staged-commit case were retried with unchanged input;
the previous-version pagination reader remains missing. No missing answer is a
semantic failure. Actual runtime was gpt-6-astra/high, Codex CLI 0.160.1.

All six candidate drafts preserved decision-critical meaning in the author audit.
All twelve masked judgments gave the candidate 4/4 on each readability dimension,
but the previous skill also remained in every preferred set: no measured preference
gain. A baseline citation error flagged by one judge was caused by path masking,
not by the generated document; [author-grades.json](author-grades.json) records that
adjudication. Scores cluster at the ceiling and are not human readability evidence.
Four targeted workflow regressions passed after the commit retry. The source-blind
reader answered 6/6 candidate questions correctly; previous-version evidence is 3/3,
with its other three questions missing. This is answer extraction, not human reading.

| Six drafting tasks | No skill | 0.1.0 | 0.2.0 |
|---|---:|---:|---:|
| Final output characters, total | 10097 | 10511 | 10774 |
| Wall time, median seconds | 41.290 | 44.346 | 47.238 |
| Reported input tokens, total | 124726 | 206027 | 210240 |
| Reported output tokens, total | 6465 | 7220 | 7426 |

Token counters include tool turns; they are not final-text tokens or a bill. Concurrent
runs and provider caching prevent a causal speed claim. Output length is not a quality
score. The later cross-provider defects prevent adopting 0.2.0 despite these high scores.

## Observed-defect revisions

0.2.1 added local procedure conditions, less repeated handoff state, bounded editing
and a guard against extending percentile changes to an entire tail population.
Its [separate protocol](repair-protocol.json) ran eight checks. Seven preserved the
required meaning; Grok's new performance report placed A's error exclusion in B's
success table cell while the prose correctly said B had 1,000 successes. That conflict
fails the all-cases gate: [grades](repair-author-grades.json), [run evidence](repair-results.json).
The candidate was not installed.

[0.2.2](final-candidate/ko-technical-writing/README.md) adds per-column source checks
and agreement between tables and prose. [final-protocol.json](final-protocol.json)
pins its complete payload and repeats the targeted cases under a separate 10-dispatch
cap. `final_round.py generate` and `smoke` execute it; `final_summary.py` reproduces
evidence. These are regression cases after inspecting failures, not fresh held-out
or masked comparisons. Scores from 0.2.0 are never transferred to the final revision.

## Final personal installation

Version **0.2.2** is installed at `~/.codex/skills/ko-technical-writing`.
[Installation evidence](installation.json) matches all six files to the final
candidate and verifies a native installed-copy run. The original 0.1.0 installation
was checked before replacement and backed up outside Git. No repository product,
global policy, or Claude/Cursor installation was added.

[Final results](final-results.json): 10 dispatches, 9 completed answers. Six regression
drafts (two tasks on three models), the Opus percentile replay, the native JSON case,
and the installed-copy smoke passed the [author audit](final-author-grades.json).
The first Grok rejoin attempt timed out at 240 seconds; an identical-input retry with
a 480-second limit completed in 151.952 seconds. The timeout remains in the denominator.
[Retry details](final-followup.json) also record a local launcher validation error
that stopped before any provider call. A copied version literal in the final
acceptance sentence was corrected to match the already-pinned 0.2.2 manifest:
[erratum](final-protocol-erratum.json). No metric or threshold changed.

This is a personal Codex release decision based on targeted regression behavior.
It is not a fresh masked preference study of 0.2.2, a human comprehension experiment,
or a promise of natural prose on every request. Grok remains slow and can produce
awkward wording; no Grok runtime support is added. Opus/Grok runs evaluate an inline
payload, while Codex exercises native files. The skill does not call those extra
models during ordinary use.

## Cross-provider comparison and total execution

[External results](external-results.json) cover 39 dispatches and 37 answers. Claude
CLI 2.1.292 reported `claude-opus-5-5`; requested high effort was not returned in the
receipt. Cursor Agent 2026.10.01-e373342 reported Grok 4.7 256K Medium. Its earlier High
condition timed out without an answer. A separate Grok judgment also timed out.

| Generator being compared, 0.2.0 versus no skill | Candidate preferred | Baseline preferred | Ties | Missing judgment |
|---|---:|---:|---:|---:|
| Opus, judged by Grok Medium | 4 | 1 | 0 | 1 |
| Grok Medium, judged by Opus | 5 | 1 | 0 | 0 |

These are raw masked model preferences on six reused tasks, with balanced A/B order
but no order-reversal replication. They are not human votes or final-version scores.
Some model error flags overreach: for example, resuming an explicitly supplied
backfill with its current prerequisite satisfied is not an invented next action.
Do not turn every reviewer flag into a confirmed defect. Conversely, author review
found the percentile interpretation and poor runbook navigation despite passing
model scores. Both scorer controls detected the deliberately false 202 completion
claim and assigned severe repetition an economy score of 1. This validates gross
error sensitivity, not fine stylistic discrimination.

| Six drafting tasks per provider | No skill output chars | 0.2.0 output chars | No skill median seconds | 0.2.0 median seconds |
|---|---:|---:|---:|---:|
| Opus |17589|14256|34.2345|47.7535|
| Grok Medium |9740|10486|38.297|141.137|

Opus CLI cost estimates totaled $0.506961 without the skill and $0.7961944 with it for
these drafting tasks. These are CLI estimates, not a bill. Grok did not supply cost;
missing cost is not zero. Concurrent studies and caching limit timing comparisons.
The output-length reduction on Opus is an observation, not a readability metric.
Grok's long latency and timeouts are practical limits, even when its answer is valid.

[Study summary](study-summary.json): 97 CLI dispatches, 91 completed answers across
all four rounds, including generation, judges, reader probes, controls and smoke.
The six missing answers comprise three Codex capacity failures and three timeouts.
Two early candidates were rejected; their results and the final regression are kept
separate. No new reader trial or broad benchmark claim is manufactured from reruns.
