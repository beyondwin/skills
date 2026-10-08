# Pre-SDD Review versus ordinary review

[한국어 보고서](README.ko.md)

Study conducted 2026-10-08–09 on macOS. The pre-registered procedure is in
[method.md](method.md). Derived cell-level results are in [results.json](results.json);
candidate and lifecycle results are in [followups.json](followups.json).

Historical follow-up recorded 2026-10-09: the study and 6.1.3 development correction
were committed, then pre-sdd-review, sddx, and waygent were retired. In the record
update conversation, the user explicitly stated that this experiment informed
the decision to sunset all three skills. The user further explained that these
harnesses had helped with earlier models but seemed unnecessary as newer models
became more capable. That is user experience and interpretation; this study did
not compare older and newer models to establish a temporal cause. The
[learning case](../../learning/cases/2026-10-08-pre-sdd-review-value.md) preserves
the study's intent, alternatives, and lessons; the
[retirement case](../../learning/cases/2026-10-09-retire-workflow-skills.md) records
the later removal and that retrospective explanation. Recommendations and
verification statements below describe study closure, before the user's final
retirement decision, not current installation or support status. The measured
scope remains pre-sdd-review on the tested fixtures, not a benchmark of all three.

## Decision

For the small single-plan repositories tested here, use an ordinary competent
review by default. The full skill has not added true defect discoveries, while
it adds time, tokens, and opportunities to demand unnecessary detail. Retain it
as an opt-in procedure when a separate reviewer, document-only repair and closure,
or a durable fingerprinted handoff is worth that overhead. This is not evidence
that the skill is useless for large plans or multi-plan campaigns: those were not
tested.

Adopt one bounded correction as development version **6.1.3**: a verification
counterexample must satisfy the assertions the plan actually prescribes. A
reviewer must not invent a gap by ignoring those assertions, or demand arbitrary
literal examples when named input categories and approved behavior determine the
expected values. The experiment does not justify deleting the skill, broadly
shortening it, or expanding its supported-host list.

## What was compared

The primary matrix uses frozen **6.1.2**, even after the candidate was adopted in
the working tree. SKILL.md SHA-256:
`d621401f528cdd2da43c6f78e73805d168813ed03542a33a51bcc4984773933f`.
The core matrix contains **62 controller attempts: 60 completed and two capped**.
Eight candidate and two reuse sessions bring the evaluation to 72 controller
attempts, excluding identity probes and invalid harness pilots; child model work
is additional and counted in the reported usage. The frozen text
is recoverable from source commit `f4e659b23f2f808ed6cce0e86de4bc1043526e99`.
The four synthetic repositories and hidden oracle are in [harness](harness/).
Oracle data never enters a reviewed repository or prompt.

| Condition | What the controller receives | What is measured |
| --- | --- | --- |
| plain | Same readiness objective, approved-intent and mutation boundaries; no skill or delegation | Ordinary self-review |
| skill | Frozen full skill in review-only mode, native independent reviewer and recorder | Entire procedure, including extra model work |
| protocol | Only the unmodified reviewer protocol; one reviewer, no controller/recorder/delegation | Diagnostic content ablation |

Four fixtures distinguish a fully specified clean plan, two repairable defects,
an explicitly deferred owner choice, and two cross-file/verification defects.
There are **five unique known defects**, not dozens of independent defects.
Clean and cross-file cases are repeated once. Protocol-only uses those two cases.
Default repair is tested separately on the two-defect case. All baseline suites
pass before the planned feature exists.

The [oracle checks](harness/test_oracle.py) execute the important counterexamples:
a writer-only schema change breaks its actual reader; nested acceptance tests can
be skipped by the planned command; exact category assertions reject normalization
mutants, whereas weak prefix-only assertions admit them. These tests establish
ground truth, not model quality.

| Requested engine | Observed identity | CLI | Interpretation |
| --- | --- | --- | --- |
| Codex Sol 6.1/high | `gpt-6.1-sol`, `high` | 0.160.0 | Supported-host experiment |
| Codex Astra/high | `gpt-6-astra`, `high` | 0.160.0 | Additional reference |
| Claude Opus 5.5/high | `claude-opus-5-5`, `high`, controller and children | 2.1.287 | Exploratory host probe |
| Grok 4.7/high | `grok-4.7-build`, `high`, controller and children | 1.0.46 | Requested alias resolves to Build; exploratory host probe |

Each cell uses fresh repository and session state. Codex homes contain only auth
and minimal configuration, with memories off. Grok uses isolated auth/state with
compatibility discovery and memories off. Claude disables native skill expansion,
hooks, memory, and MCP loading; its custom reviewer is read-only and explicitly
Opus/high. No private project source is used. Model identity comes from actual
transcripts, not a configuration guess.

## Primary outcomes

Each primary arm attempts six reviews: a/b/c/d once, then a/d once more.

| Engine | Ordinary: completed / found / FP | Full: completed / found / FP | Median seconds, ordinary → full |
| --- | --- | --- | --- |
| Sol 6.1/high | 6/6; 7/7; 0 | 6/6; 7/7; 0 | 39.9 → 120.7 |
| Astra/high | 6/6; 7/7; 0 | 6/6; 7/7; 0 | 36.7 → 142.1 |
| Opus 5.5/high | 6/6; 7/7; 0 | 6/6; 7/7; 2 | 28.5 → 94.9 |
| Grok 4.7 Build/high | 6/6; 7/7; 0 | 5/6; 6/6; 0 | 255.1 → 597.5 |

“Found” counts known-defect opportunities in completed, graded reviews.
The primary matrix has 48 attempts, 47 completed; both arms find every known
defect in their completed reviews. Ordinary verdicts are correct in 24/24; full
verdicts in 22/23 completed reviews, plus one unresolved timeout. Neither arm
produces a false READY. No additional valid defects beyond the oracle are found.

Grok’s completed medians use different case mixes because its c/full run timed
out. Restricting to its five completed matched pairs gives ordinary **269.6 s**
versus full **597.5 s**; the censored 901.4-second run remains a separate failure.

Counts are descriptive, not independent statistical samples. A duplicate finding
for a missing behavior and its missing test counts once. Correct advisory remarks
are not false positives. Timing includes controller work and waiting for children.
A timeout is a completion failure with a censored duration, not an inferred wrong
semantic verdict or an automatic zero on defect recall.

A separate LLM grading agent matched label-masked reports against the fixtures
and oracle; the primary agent checked disputed claims against executable
counterexamples. This is not a human expert panel or a fully independent
cross-provider judge. Two supported-host candidate smoke results were graded
unmasked by the primary agent and are labeled separately in the data.

Two material false positives occurred in Claude's original full-skill cells:

- On the unresolved-choice fixture, it additionally required enumerated literal
  input/output examples even though the plan prescribed exact tests by category
  and the approved invariant determined their expected values.
- On the repeated clean fixture, it demanded specific test method names despite
  five exact input/output cases and an explicit requirement to verify execution.
  This turned a correct plan into a false `REVISE`.

The ordinary reviews were not perfect prose. Some overstated a discovery
counterexample as the original plan necessarily exiting zero, even though the
separate writer/reader conflict would fail a baseline test. The actual discovery
defect remained valid; this is evidence precision, not another invented defect.

Grok's full unresolved-choice run exceeded the 900-second cap and left an
unfinished recorder run. A child had reported findings, but the controller had
not adjudicated them or produced a final verdict. Its incomplete `REVISE` is not
scored as the final answer. The ordinary run completed in 86.147 seconds.

## Cost and ablation

This ablation compares the **same a/d first-run pair** in each condition, n=2.
It does not compare a two-case protocol median with the six-case primary median.
Input totals include cached input and repeated context; they are not unique text size.

| Engine | Condition | Median seconds | Total input tokens | Total output tokens | Reported USD, pair total |
| --- | --- | ---: | ---: | ---: | ---: |
| Sol | plain | 45.2 | 137,646 | 2,054 | not reported |
| Sol | protocol | 55.9 | 169,852 | 2,642 | not reported |
| Sol | skill | 163.6 | 1,074,831 | 9,843 | not reported |
| Astra | plain | 52.5 | 152,983 | 2,055 | not reported |
| Astra | protocol | 55.3 | 171,473 | 2,397 | not reported |
| Astra | skill | 179.6 | 1,226,272 | 8,876 | not reported |
| Opus | plain | 30.3 | 150,819 | 5,190 | $0.3275 |
| Opus | protocol | 39.1 | 169,723 | 6,218 | $0.2769 |
| Opus | skill | 93.6 | 792,578 | 18,775 | $1.0389 |
| Grok | plain | 286.9 | 284,451 | 46,024 | $0.1855 |
| Grok | protocol | 457.7 | 381,572 | 63,096 | $0.2442 |
| Grok | skill | 545.6 | 2,102,776 | 102,470 | $0.7039 |

Across these matched cases, protocol-only is faster than full skill but slower
than ordinary review on every engine. It adds no detected defect. Extra protocol
content alone is therefore not a demonstrated improvement over the ordinary
prompt on this sample. Token and cache semantics differ across providers; use
within-engine comparisons, not raw cross-provider token counts as dollar estimates.

For all six primary Claude reviews, reported totals are **$0.8617 ordinary**
and **$3.1538 full**, about **3.66×**. This is procedure cost, not evidence that
a more expensive model or provider is better or worse.

Claude and Grok dollar amounts are CLI-reported estimates, not an invoice. Codex
did not report comparable dollars; no price was invented. Claude usage is
deduplicated by message ID and includes inspected child transcripts. Codex totals
sum distinct session ledgers. Grok's parent ledger includes child model calls;
adding child ledgers again would double count. Capped calls without a final
ledger have unknown complete cost. Across the valid Grok cells, known reported
cost is at least **$2.6761**, with both capped cells unpriced. Excluded Grok
harness pilots add at least **$0.8777**, also not a complete total. Claude
reports **$5.1621** for its 16 core cells and **$3.1893** for six follow-ups,
excluding identity probes. A complete dollar total for this study is unavailable.

Protocol-only reviews retained the known-defect results on the two ablation
cases without the full controller procedure. This is evidence that the complete
procedure is unnecessary for these cases, not a justification for replacing the
installed readiness gate with a new mode. The ablation changes text volume,
delegation, and recording together; it cannot attribute all overhead to any one
component. Plain and protocol each have one model reviewer; full skill has more
model work and no equal-token-budget control.

## Default repair and process value

| Engine | Ordinary repair | Full-skill repair | Actual scope and closure |
| --- | --- | --- | --- |
| Sol | 62.2 s | 244.9 s | Both fix both causal defects; plan only. Full has a distinct fresh closure. |
| Opus | 32.1 s / $0.1175 | 124.8 s / $0.7523 | Both fix both causal defects; plan only. Full has a distinct fresh closure. |
| Grok | 261.8 s / $0.1252 | 901.6 s (capped; cost unknown) | Both fix both defects; plan only. Full closure and READY record succeed; final report delivery times out. |

Repair cells are n=1 per condition. All six actual document repairs are correct.
Five controller runs deliver their final report. Grok full repair completes the
fresh closure and persists a finished READY record, but its finish tool-result
and final controller receipt are not delivered before the cap. It is a terminal
completion failure, not a failed document fix. Its three PSDR records split the
missing behavior/test into two records; these still represent only two causal defects.

Both ordinary and full procedures can produce correct repaired documents here.
The full procedure's additional, observed result is a separate closure reviewer
and a completed structured record with document hashes. That is traceability
and process assurance; no extra postrepair defect was caught in these small
repair cases. The experiment did not implement the repaired plans in production
or measure downstream defect rates.

Actual process evidence is weaker than simply counting subagents suggests:

- The bounded audit inspected all 27 main full-skill cells/32 dispatches and
  eight follow-up cells/dispatches: 39 fresh child contexts and one resumed
  missing-fields re-ask. A fresh context alone does not establish independence.
- Codex's 16 inspected dispatches use `fork_turns: none` and distinct child
  sessions. Saved message bodies are encrypted; discovery-hint content is
  `not_observable`. No decryption was attempted.
- Three readable Claude discovery dispatches supplied targeted unittest
  subdirectory or `__init__.py` hints: main d repetitions 1 and 2, and candidate d.
  Count their final findings as end-to-end detection, not unseeded independent
  rediscovery. Other readable inspected dispatches had no material seeding found.
- All three full repair runs used distinct discovery and closure agents. Actual
  file hashes show only the plan changed; both original causal defects were
  corrected. Grok's completed closure and recorder do not erase its final report
  timeout. A record's `reviewers: 1` means one logical role, not one cumulative
  physical agent.
- Grok d/repeat invoked an extra focused `data-boundary` reviewer for an
  explicitly internal envelope with no external clients. This overly broad risk
  interpretation adds a role and cost; it is separate from semantic false positives.

The recorder makes claims inspectable; its presence is not proof that the
reviewer's assertions, independence, or verdict are correct.

## The adopted correction

The candidate adds one paragraph to `reviewer-protocol.md` in the skill that
this study measured. That skill is no longer in the tree.
The frozen protocol SHA-256 is
`195b3cc04363769c6deb75b5b73544c039bf3b9f6b804a70e0f22b1e2eab7c9d`;
candidate is `5d70337be164a9e27d60512520118f419273b2ac0faaaa8786ef76dee8ebce40`.
The controller SKILL.md did not change in the candidate, so pinning only its hash
would have missed this experimental difference. Full payload manifests and the
protocol hash were recorded outside Git. Derived protocol hashes are retained in
[followups.json](followups.json). The repository measurement practice now requires
a changed-resource hash or full manifest, rather than SKILL.md alone.

| Follow-up | Frozen text | Candidate text |
| --- | --- | --- |
| Deferred-choice c, two fresh pairs | Same unnecessary material literal-example finding in 2/2 | Only the genuine owner-decision blocker in 2/2 |
| Separate clean a, Claude | Original repeat had false REVISE | READY, no material findings |
| Cross-file d, Claude | Main matrix found both real defects | Both preserved; targeted discovery hint limits independence claim |
| Supported-host a and d, Sol/high | Main matrix reference | Clean READY and both real defects preserved |

Label-masked grading independently agrees with the c distinction. Formatting,
absolute links, and occasional host names can reveal an arm, so this was not
fully blind grading. The candidate's semantic core reached actual reviewer
instructions; it was sometimes compressed rather than passed verbatim.

An independent final review found no material semantic regression and requested
one correction to a stale canonical handshake example. The local development
change includes the paragraph, version/handshake copies, Unreleased notes, and
the matching maintainer contract. It preserves the existing checks for real
missing assertions, consumer contracts, test discovery, state partitions, and
concurrency. It changes no host support, recorder schema, default mode, or repair
scope.

This is a repeated, bounded false-positive correction. Two pairs do not establish
statistical superiority or improved quality across arbitrary repositories.

## Additional freshness falsification

The documented reuse change list compares the current checkout to the previous
`HEAD`, not to the previous reviewed dirty tree. The
[offline counterexample](harness/reuse_counterexample.py) proves that reverting
previously reviewed dirty source can leave unchanged HEAD/document hashes and an
empty prescribed change list, although the source changed. Removing a previously
reviewed untracked file has the same issue.

A separate actual Sol/high lifecycle test first obtained READY with an untracked
working verification runner, deleted that runner, then sent the identical request
in a fresh session with the same recorder. **It did not produce a false READY.**
Sol inspected the repository again and returned REVISE for the missing command.
The static predicate is incomplete; an actual wrong verdict was not reproduced.
No further attempts were made to hunt for a failure.

A possible future correction is to record whether non-document dirty/untracked
inputs existed at review completion, or retain their content fingerprint. Blocking
all dirty previous runs would also disable valid reuse after ordinary document
repairs. That recorder/schema change is not bundled into the one-paragraph fix.

## Reproduction and verification

The [runner](harness/run.py) calls live models only when explicitly invoked.
It is not part of default verification or CI. Freeze the full skill resource tree
from the baseline commit, then pass `--skill-root` for every stage. Example:

```sh
python3 docs/research/2026-10-pre-sdd-review-eval/harness/run.py \
  --engine sol --stage discovery --parallel 2 \
  --skill-root /absolute/path/to/frozen/pre-sdd-review \
  --output /absolute/path/to/new-external-cells
```

Other stages are `repeat`, `protocol`, and `repair`. Existing cell directories
are never overwritten. `harness/oracle.json` is for grading, not model input.
Raw provider receipts, full model responses and generated repositories
are not committed. The 57 task-created isolated auth copies were removed after all
calls stopped; original user credentials were not changed. Only fixtures, code, paraphrased grades, and derived numbers
belong in this study.

The following verification actually ran:

- `python3 scripts/verify.py --skill pre-sdd-review`: passed after aligning the
  version copies and allowing the documented Unreleased development target.
- `python3 scripts/verify.py`: **1,286 tests plus compilation passed in a disposable
  local checkout with the current payload staged**. Packaging reads indexed blobs;
  an unstaged source run sees the old 6.1.2 payload and fails metadata matching.
  A global temporary `GIT_INDEX_FILE` was also unsuitable because nested test
  repositories inherit it. The disposable checkout isolated those indexes and
  preserved the real working tree and staging state.
- `harness/test_oracle.py`: six provider-free checks passed on Python 3.14 and
  stock macOS Python 3.9. They validate fixture/counterexample logic only.
- Public-document checks: 68 tests passed. All 21 research Python files compile
  on stock macOS Python 3.9, including the final bookkeeping edits.
  Local Markdown links and `git diff --check` passed. Changed product, test and
  release-script bytes match the full-suite verified snapshot exactly.
- No commit, tag, package publication, host-support expansion or push was performed.

## Practical use and remaining uncertainty

| Situation | Evidence-based choice |
| --- | --- |
| Small, clear single plan; material issues and an actionable answer are enough | Ordinary review |
| A structured review is wanted without repair/record lifecycle | Protocol-only preserved results but did not outperform ordinary review; no new shipped mode |
| Independent closure and a fingerprinted handoff are explicit requirements | Full skill on its supported Codex host; still inspect its actual evidence |
| Large campaign, concurrency-heavy system, migration, auth/security or public/private boundary | Not measured here; no general verdict about benefit |
| Grok or Claude production use of the full skill | Experimental results do not establish official host support |

The small fixtures create a ceiling on discovery quality. More repetitions of
the same five defects cannot prove broad equivalence. Cache behavior, native tool
and sandbox differences, provider load, and per-host parallelism affect timings.
Claude's independent reviewer lacks a command tool while its controller and plain
arm can run safe baseline checks; that capability difference belongs to the tested
workflow bundle. The experiments test explicit pinned invocation, not trigger
quality, native installation, production reliability, or long-term ROI.

Further work should target a new decision, not repeat the same ceiling cases:

1. Test genuinely different long or interacting plans before deciding whether to
   remove the full procedure. Measure unique material misses and false READYs,
   successful repair closure, and human correction effort as well as model cost.
2. If repeatability of independent review is required, audit discovery dispatch
   contents and focused-role triggers, rather than equating a fresh agent with an
   independent finding. This study found both seeded hints and an overly broad
   risk-role trigger.
3. Address the dirty-source reuse predicate in a separately tested recorder
   change, preserving valid document-only repair reuse. The present lifecycle
   probe establishes a static gap, not a demonstrated unsafe model outcome.
