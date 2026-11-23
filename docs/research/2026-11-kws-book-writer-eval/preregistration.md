# kws-book-writer evaluation: pre-registration

Written 2026-11-20, before any gate-evaluation or pilot run. Results go in
[README.md](README.md). The design and its alternatives are in the
[learning case](../../learning/cases/2026-11-20-book-writing-skill-design.md).

All live runs use `claude -p` isolated per `CLAUDE.md` (`--setting-sources project
--strict-mcp-config`, opus at high effort), a fresh fixture directory per run, and a
pinned copy of the payload whose per-file SHA-256 and tree digest are recorded.
The model and effort that ran are read from the transcripts.

## Rung 1: offline

`tests/products/kws-book-writer/` checks `book_check.py` hard failures, report-only
items, the marker single source, and a run on `/usr/bin/python3` (3.9). The same
person wrote the checker and the tests, so a full pass is regression protection, not
evidence of detection quality.

## Rung 2: smoke

One synthetic mini-book (3 chapters, synthetic `tiny-queue` source written for this
study) run end to end across three turns: the request, plan approval, first-chapter
feedback. Pass means all of:

- the run stops for plan approval and again after chapter 1, and does not write chapter 2
  before the second stop;
- per-chapter writers and the gate run as fresh subagents and the parent waits for them;
- `book_check.py check --final` exits 0 at the end;
- no file outside the book workspace changes.

A failure caused by the headless host (for example killed background children) is
recorded as a harness limit, not a skill defect.

## Rung 3: seeded-defect gate evaluation

Question: does the gate brief in `references/acceptance.md` find more seeded defects than
a plain review instruction, without blocking clean manuscripts more often?

- Base: the accepted smoke-run workspace. Before seeding, nobody runs the gate or the
  control on it.
- Seeds: a fresh subagent that has not seen `references/acceptance.md` or this skill's
  references writes 12 defects into 3 copies of the base (4 each), editing chapter files
  only, and writes a key (file, original sentence, seeded sentence, type). Types: a number
  that contradicts the ledger, a wrong chapter reference, leaked process language, a
  promised topic removed, a negation flip in a factual sentence. Each copy is reassembled
  and re-checked with `book_check.py`.
- Clean: the unmodified base, judged 4 times per condition.
- Conditions, each a fresh `claude -p` session with the same workspace and source files:
  - gate: the gate brief from `references/acceptance.md`, filled in;
  - control: "Find the errors in manuscript.md that must be fixed before publication.
    Verdict BLOCK if any, else ACCEPT. Give the location and reason for each." (in Korean).
- Runs: 3 seeded copies x 2 runs + 4 clean runs = 10 per condition, 20 total.
- Scoring: outputs are renamed to random IDs; a fresh scorer subagent that does not know
  the conditions matches findings to the key. A seeded defect counts as detected if any
  finding names its location and what is wrong. Detections are counted out of 24 per
  condition (12 defects x 2 runs). Clean runs count a false block if the verdict is BLOCK;
  a block whose finding is a real defect of the base, confirmed against the source, is
  reported separately and not counted as false.

Decision rule:

- Keep the gate brief if gate detections minus control detections is at least 4 of 24
  and gate false blocks are at most 1 of 4.
- Otherwise report "no measured difference" and replace the gate brief with the plain
  review instruction plus the ledger and check-report inputs.
- With 24 opportunities a difference under 4 is within noise; this rung cannot show small
  effects in either direction.

### Addendum, written after the rung 3 decision and before its check run

Rung 3 ended at 24/24 versus 22/24, so the rule replaced the gate brief with the plain
review instruction plus the workspace inputs. That combination was not itself run. One
check run gives it the same 10 gate items (3 seeded copies x 2, clean base x 4), scored by
the same blind scorer and standard. It stays if it detects at least 22 of 24 and blocks a
clean run for a non-real defect at most once in 4; otherwise the eight-criterion brief is
restored and the result is reported as a failed simplification.

## Rung 4: pilot

One real book about a private backend platform, drafted from a snapshot of that
private repository outside this repository. The private workspace and transcripts are
never committed; only counts, costs, timings, and verdicts are recorded here.

- The user delegated the topic and the two stops, so the operator answers the plan and
  calibration stops and records that the calibration was not in the user's voice.
- Recorded: cost, wall time, gate verdicts by round, `check --final` result, hard-defect
  count, and whether any source file changed.
- Adoption criteria (absolute, judged by the user after the run): zero hard defects,
  at most 5 edits per chapter on 3 chapters the user picks at random, and the user judges
  the draft usable. Until the user judges it, adoption stays `not_measured`.

## Improvement loop

At most two improvement rounds after rungs 2 and 3. Each round changes one thing, comes
from a failure a run actually made, pins the payload again, and re-runs only the affected
rung. Gotchas are added only from observed failures.
