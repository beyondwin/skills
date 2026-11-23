# Workspace, brief, ledger, and assembly

## Workspace layout

```text
<ws>/
  brief.md               reader, promises, scope, length, sources: the single source of truth
  research/ledger.md     facts with IDs and sources
  plan.md                chapters, term table, openings and closings, figures
  voice.md               voice rules and calibration notes
  book.json              title, author, chapter order, front and back matter
  chapters/01.md ...     one file per chapter
  front/preface.md       written in phase 6
  back/references.md     written in phase 6
  checks/factcheck.md    before/after of every fact fix
  checks/check-report.md written by book_check.py check
  checks/acceptance.md   gate findings by round
  checks/acceptance.json verdicts with the manuscript SHA-256 (written only by book_check.py accept)
  manuscript.md          written only by book_check.py assemble
```

## Resume table

| If this is missing or stale | Resume at |
| --- | --- |
| `brief.md` | 1 |
| `research/ledger.md` | 2 |
| `plan.md`, `voice.md`, or `book.json`; or `plan.md` has no `승인:` line | 3 |
| `chapters/01.md`, or `voice.md` has no `## 보정` section and the user did not skip calibration | 4 |
| any chapter listed in `book.json` | 5, at the first missing chapter |
| `manuscript.md`, or it is older than a chapter file | 6 |
| `check --final` exits non-zero | 7 |

When the user approves the plan, append `승인: <date> <what the user said>` to `plan.md`.

## Phase 1: brief

Ask in one message only what you cannot infer. Defaults, stated back to the user:

| Slot | Default |
| --- | --- |
| reader | a working developer new to this subject |
| promise | three to five things the reader can do or explain after the book |
| scope | in and out lists drawn from the sources |
| length | 8 chapters of 8,000 to 12,000 Korean characters each |
| sources | the paths and URLs the user gave; nothing else unless the user allows web search |
| voice | 합니다체, plain explanations first; user samples if given |
| title and author | a working title; the author is the user's name if known, else `저자` |

`brief.md` holds these slots and nothing else. Other files point to it rather than restating it.

## Phase 2: research ledger

Read the sources before planning. For a large source, split it into up to three areas and
dispatch one fresh subagent per area, each writing `research/ledger-<letter>.md` with ID prefix
`RA`, `RB`, `RC`. Then concatenate them into `research/ledger.md`. Entry format:

```markdown
| ID | 사실 | 출처 | 확인 |
| --- | --- | --- | --- |
| RA01 | 결제 웹훅은 3회까지 재시도한다 | backend/billing/webhook.py:88 (a1b2c3d) | 2026-11-20 코드 |
```

- A fact is one checkable sentence. A source is a path with line and commit, a document
  path with heading, or a URL. `확인` says how it was checked: code, doc, or the user.
- Record design reasons only where a source states them (a decision record, a commit message,
  a comment). Otherwise record what the code does and mark the reason unknown.
- Record numbers exactly as the source gives them.

## Phase 6: assembly and boundaries

1. Write `front/preface.md` (who the book is for, what it promises, how to read it) and
   `back/references.md` (sources a reader can follow; no ledger IDs). Add both to `book.json`.
2. `book_check.py assemble <ws>`.
3. For each adjacent pair of chapters, read the last section of one and the first section of the
   next. Fix broken handoffs, repeated explanations, and term-table violations in the chapter
   files. Do not load the whole manuscript into one context.
4. `book_check.py assemble <ws>` again.

`book.json` example; every value is plain JSON, so quotes and backslashes in a title are safe:

```json
{
  "title": "제목",
  "subtitle": "부제",
  "author": "저자",
  "date": "2026-11",
  "language": "ko",
  "front": ["front/preface.md"],
  "chapters": ["chapters/01.md", "chapters/02.md"],
  "back": ["back/references.md"]
}
```
