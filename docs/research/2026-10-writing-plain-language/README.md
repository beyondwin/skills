# Familiar Korean technical writing: personal revision

[한국어](README.ko.md)

Current personal skill: [Readable 0.6.0](../2026-10-readable-rename/README.md),
invoked as `$readable`. Names, paths and results below describe the historical study.

**This study installed and verified personal Codex 0.5.1.** Eight native drafts, eight
external audits (four Opus/four Grok), three native regressions and one installed
smoke passed the separately declared personal-use acceptance. The earlier comparative
criterion did not pass; general superiority and human reading benefits remain unproven.

The reader found all earlier pairs difficult to distinguish and the terminology
unnatural. This study responds to that feedback with concrete actors/actions,
local explanations of unfamiliar concepts, and preservation of technical meaning.
It measures no vocabulary-frequency corpus or human reading performance.

## Development history

- 0.4.0: twelve writes, all returned. Author review rejected unexplained backfill,
  rollback-rehearsal and percentile terminology plus repeated cache explanation.
- 0.4.1: eight writes, all returned. Backfill and p95 explanations improved, but
  a cache-valid-time heading incorrectly included an after-expiry branch; upload
  digest terminology and repetition remained. Rejected.
- 0.4.2: eight writes and twelve judgments, all returned. Compared with 0.2.2:
  one concordant win, two losses, three undecided cases. Rejected. The SDK handoff
  incorrectly quoted a planned screen label as currently displayed; a reviewer
  caught an implementing-assistant miss. The schema handoff lost useful operational
  names, and the metric conclusion was less direct than it should have been.
- 0.4.3: eight writes and twelve judgments, all returned. Two concordant wins,
  no losses and four undecided cases still failed the frozen four-win criterion.
  No regression/install checks followed. A reported error about checking pending CI
  is an overstrict reviewer interpretation: proposing that check is not claiming
  an unobserved result. The raw preference is preserved.
- 0.5.0: eight writes and eight absolute audits, all returned. Seven drafts passed;
  the upload draft made two overbroad reuse claims. Rejected, with no install.
- 0.5.1: corrects those claims and adds contextual vocabulary examples. All eight
  known cases are now generated on the actual personal installation target, native
  Codex, with four Opus and four Grok audits. All eight audits reported no material
  error or blocking reading obstacle. Three native regressions and the installed
  smoke passed. The six installed resources exactly match the frozen payload;
  0.2.2 is backed up outside Git.

For 0.4.0 and 0.4.1, planned model judgments and adoption checks were skipped
because a required author gate already failed. 0.4.2 completed judgments but did
not proceed to adoption checks. This cost-saving deviation does not
create a preference result. Original responses and failed candidates are retained.

Six primary cases include three known cases from the reader's earlier comparison
and three author-written Korean-source cases. Two additional cases first appeared
in 0.4.1 and are known regression tasks by 0.4.2. Six frozen incumbent responses
are explicitly reused rather than counted as new generations. Each paired judgment
has reversed labels; order disagreement or absence is undecided. The 0.4.x comparative
adoption rule did not pass. Before 0.5.0 calls, the decision changed to absolute
personal readability/fidelity acceptance under the user's delegated judgment. It
is a separately disclosed personal configuration decision, not a passed comparison
or the earlier statistical-superiority goal. Before 0.5.1 calls, final writing
validation was scoped to the actual personal host; prior inline writer results do
not become support claims for Opus/Grok.

## Reproduction and evidence

Use Python 3.9 or later. Default commands prepare prompts without provider calls:

```sh
python3 docs/research/2026-10-writing-plain-language/native_run.py generate /absolute/private/archive
```

Live execution requires the already-authorized provider scope, private host
credentials and `--execute`. The `judge`, `regression` and `smoke` phases follow
only after their prerequisites. To reconstruct a revision archive, link or copy the
six `*--previous` run directories and external prompt files from the original
archive, checking their hashes in the protocol. Do not count these as new calls.

- [Original design](design.md), [protocol](protocol.json), [results](results.json), [author review](author-review.json)
- [First correction design](revision-design.md), [protocol](revision-protocol.json), [results](revision-results.json), [author review](revision-author-review.json)
- [0.4.2 protocol](final-protocol.json), [results](final-results.json), [corrected author review](final-author-review.json)
- [0.4.3 design](adoption-design.md), [protocol](adoption-protocol.json), [author review](adoption-author-review.json)
- [Personal decision change](personal-design.md), [0.5.0 audit results](personal-results.json)
- [Native 0.5.1 design](native-design.md), [protocol](native-protocol.json), [author review](native-author-review.json)
- [Cases](cases.json), [transfer cases](transfer-cases.json), [scorer representation repair](scorer-correction.md)
- [Decision record](../../learning/cases/2026-10-09-personal-technical-writing.md)

Native Codex runs use isolated HOME/CODEX_HOME, copied-and-removed authentication,
memories off and a pinned skill tree. Opus/Grok receive instructions inline, which
does not verify their native skill discovery. Raw generated responses, provider
receipts and private credentials are not repository artifacts.

## Final checks and limits

[Acceptance decision](adoption-decision.json), [native audit results](native-results.json),
[regressions](regression-results.json), [installation](installation-status.json),
[verification](verification.md), and [all-round accounting](study-summary.json) preserve
the evidence separately from the failed comparative adoption rule.

There were 96 distinct CLI dispatches and 96 completed responses across six versions:
52 writing responses, 24 pairwise judgments, 16 absolute audits, three regressions
and one installed smoke. There are only eight distinct source tasks. Reused incumbent
responses are counted once; this is not96 independent samples or96 HTTP/model calls.
All31 native workspaces stayed unchanged, required skill/reference reads were observed,
and copied auth files were removed.

Runtime: Codex CLI0.160.1, actual gpt-6-astra/high from turn_context; Claude Code2.1.292,
actual claude-opus-5-5; Cursor Agent2026.10.01-e373342, init label Grok4.7 256K Medium.
Claude requested effort is not independently confirmed. Grok's immutable backend model
ID is unavailable. Timing and provider token receipts are not human-reading measurements.

Known cases were reused while fixing the skill. Minor polish remains (for example CI
and staging labels in supporting evidence). Source-undefined terms are not replaced
with guessed definitions. Personal acceptance does not guarantee natural wording or
error-free text on every future task or model. Opus/Grok inline writing probes were
uneven and do not establish native support there.
