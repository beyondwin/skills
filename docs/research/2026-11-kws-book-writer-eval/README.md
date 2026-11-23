# kws-book-writer evaluation

Date: 2026-11-20. Product: `kws-book-writer` 0.1.0 (development). Host: Claude Code
2.1.322, `claude -p` isolated per `CLAUDE.md`. Every session and subagent in these runs
ran `claude-opus-5-5` at `high` effort, read from the transcripts. The plan and decision
rules were written first: [pre-registration](preregistration.md). The decision record is
the [learning case](../../learning/cases/2026-11-20-book-writing-skill-design.md).

Raw transcripts, manuscripts, and the private pilot workspace are not committed.

## Rung 1: offline

`python3 scripts/verify.py` passes, including `kws-book-writer-contract`
(23 tests, one of them on `/usr/bin/python3` 3.9.6). This is regression protection
written by the same author as the checker, not evidence of detection quality.

## Rung 2: smoke

Synthetic `tiny-queue` source (three Python files, a README, two decision records written
for this study), 3 chapters of 2,500 to 3,500 characters, three turns.

| Turn | Input | Stopped at | Cumulative cost | Wall time |
| --- | --- | --- | --- | --- |
| 1 | the request | plan approval, with 39 ledger entries | $0.89 | 202 s |
| 2 | "승인합니다" | chapter 1 written by a subagent, calibration question | $1.69 | 172 s |
| 3 | two voice changes, "끝까지" | done, `check --final` exits 0 | $5.03 | 652 s |

Pinned payload tree SHA-256 `618c3274…` (per-file digests in the fixture manifest).

Against the pass criteria:

- Both stops held; chapter 2 was not written before the second stop.
- Six fresh subagents ran (three chapter writers, one fact pass over three chapters, two
  gate rounds); the parent waited for each in the headless session. The background-child
  risk did not occur.
- `check --final` exits 0 on the accepted manuscript (11,030 characters).
- The source tree is byte-identical to the template after the run.

What the run found:

- The run reported three places where the synthetic source disagreed with itself (README
  cap versus jitter order, decision record arithmetic, a misleading code comment) and wrote
  the chapters from the code.
- Gate round 1 blocked on four broken table-of-contents entries: `assemble` stripped inline
  code from headings ("넣기: `enqueue`와 작업의 모양" became "넣기: 와 작업의 모양"). The
  orchestrator worked around it by removing backticks from the headings. This was a real
  `book_check.py` defect; improvement round 1 fixed it and added a regression test.
- Round 2 accepted with no findings. The fact pass made no fact fixes, added three missing
  source tags, and added one ledger entry.

## Rung 3: seeded-defect gate evaluation

Base: the accepted smoke workspace. A fresh subagent that had not seen the skill seeded 12
defects into three copies (number 3, negation 3, chapter reference 2, process leak 2,
promise gap 2). Each condition ran 10 fresh sessions (3 copies x 2, clean base x 4).
A fresh scorer matched outputs to the key without the condition mapping. Two control
outputs had been captured as a closing postscript only; they were rebuilt from the full
session text and re-scored with the same standard (one went from 2/4 to 4/4).

| | Eight-criterion gate | Plain review (control) | Plain review + workspace inputs (check run) |
| --- | --- | --- | --- |
| Seeded defects found | 24/24 | 22/24 (missed D3-2 twice, a removed checklist) | 24/24 |
| Seeded copies blocked | 6/6 | 6/6 | 6/6 |
| Clean base blocked | 2/4, both for real defects | 4/4: 3 for real defects, 1 for bold rendering only | 4/4, all for real defects |
| Cost, 10 sessions | $7.57 | $4.68 | $7.41 |
| Mean session time | 189 s | 74 s | 126 s |

Decision by the pre-registered rule: the gate found 2 more seeded defects than the plain
review, under the threshold of 4, so this is no measured difference. The gate brief was
replaced by the plain review instruction plus the workspace inputs. The replacement was
not itself run, so a check run (pre-registered in the addendum) gave it the same 10 items;
it met the detection half of its bar (24/24) and stays. The
replacement read the same inputs, so it did not save cost.

Both conditions are near the ceiling on seeded defects, so this rung cannot show a small
quality difference either way. The "clean" base turned out to contain three real defects
(below), so no reviewer saw a clean manuscript: the false-block rate is not measured, and the
"0/4 non-real blocks" results say only that no block rested on an invented defect. The
scorer saw no condition labels, but the output format can reveal the condition, so scoring
was only partly blind.

What the clean runs showed about the accepted smoke book:

- It had two real errors that the smoke gate (eight-criterion brief, two rounds) accepted:
  chapter 2 opens with a worker *process* crashing and another worker re-leasing the job,
  which an in-process memory-only queue cannot do; chapter 3 closes with a 4.2-second
  ceiling on retry waits that ignores the worker's 1-second idle sleep. Across runs the
  first was found by the plain review in 3/4 clean runs and the eight-criterion gate in
  0/4; the second by the gate in 2/4 and the plain review in 0/4. The check run found them
  in 3/4 and 3/4. An ACCEPT is therefore not evidence of a defect-free book.
- Eight term definitions such as `**멱등성(idempotency)**은` do not render as bold:
  markdown-it 14.1.0 (CommonMark) leaves the asterisks. Improvement round 2 added a
  report-only `book_check.py` item and a voice rule for it. The scorer kept this finding
  "unclear" because no renderer is named in the book; this record counts it as real.
  In the check run every session raised it, likely because the regenerated check report
  now lists it.

## Rung 4: pilot

A snapshot of a private backend repository (about 1,300 files), kept outside this
repository. Payload tree `56beecc…`
(after improvement round 1, before round 2 and the gate change, so the gate was the
eight-criterion brief). The operator answered both stops; the calibration was not in the
user's voice.

| Turn | What happened | Cumulative cost | Time |
| --- | --- | --- | --- |
| 1 | 544 ledger entries (215,485 characters), plan of 6 chapters | $24.24 | |
| 2 | chapter 1 (7,980 characters), calibration question | $25.92 | 345 s |
| 3 | feedback on identifier density; chapters 2–6, two fact passes, assembly; stopped by the account's 5-hour usage limit before the gate | $44.54 | 3,525 s |
| 4 | new session, same workspace: resumed at phase 7, gate round 1 ACCEPT, `check --final` exits 0 | $3.16 (new session) | 381 s |

Total about $47.70 for a 51,742-character manuscript (chapters 7,904–7,992 characters).

- Research took over half the cost. A ledger cap is a candidate, not measured.
- The fact passes logged 19 fixes with before/after text (for example an overclaimed
  "only" and a missing branch). Unlike a log that only says "nothing unresolved",
  the before/after record shows what changed.
- Resume from folder state worked in a fresh session: it found the missing acceptance
  record, checked that phase 6 was done, and ran only the gate.
- The gate accepted with seven non-blocking notes, including one wrong chapter reference
  and one tension between two chapters, which an eight-criterion gate left as notes. The orchestrator left accepted text unchanged, as the hash lock requires.
- The term check flagged '리스' inside '릴리스' three times. It now matches only at word
  starts (a regression test covers it); on the current checker the pilot has no term hits
  and no unrendered bold.
- The source snapshot is byte-identical after the run.

Phase 7 again on the current payload (tree `ccaf0486…`, plain-review gate and current
checker), in a fresh session on a copy of the workspace with the verdict removed:

- Round 1 BLOCK with 4 findings the eight-criterion gate had accepted: two wrong HTTP status
  codes, a state described as terminal in two chapters and non-terminal in a third, and a
  wrong resend interval. The orchestrator confirmed each against the source before fixing;
  two came from wrong ledger entries, which it corrected too.
- Round 2 ACCEPT; round 3 re-judged three sentences changed for a memo, ACCEPT.
  `check --final` exits 0. $11.57, 1,109 s. The source snapshot is unchanged.
- One sample cannot compare the two gates, but the accepted pilot manuscript was not
  defect-free, matching the smoke result.

Total live spend for this study is about $72 (API-equivalent figures from the transcripts).

Adoption (the user reads three random chapters: at most 5 edits each and judged usable) is
`not_measured` until the user judges it.
