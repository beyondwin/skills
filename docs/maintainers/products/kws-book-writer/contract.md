# kws-book-writer contract

This document sets kws-book-writer's activation, workspace files, phases, checks, and the
files that change together. When behavior changes, update `SKILL.md`, its references,
`scripts/book_check.py`, the tests in `tests/products/kws-book-writer/`, and both product
READMEs in the same change.

## Activation

Only `/kws-book-writer` in Claude Code activates the skill
(`disable-model-invocation: true`). Codex is not a supported host; `agents/openai.yaml`
exists because every payload carries one, and it keeps implicit invocation off.

## Workspace

The skill writes a Korean technical or nonfiction book draft into one workspace folder
the user chooses:

- `brief.md`: topic, reader, scope, and length
- `research/ledger.md`: claims and their sources
- `plan.md`: the chapter plan
- `voice.md`: what the user asked to change after the first chapter
- `chapters/NN.md`: one file per chapter
- `checks/`: `factcheck.md` (fact-pass edits, before and after) and `acceptance.json`
- `book.json`: book metadata
- `manuscript.md`: the assembled manuscript

Manuscripts stay in the user's workspace and are never committed to this repository.

## Phases

1. Brief.
2. Research ledger.
3. Plan. The user must approve it before any chapter is written.
4. First-chapter calibration, on by default. The user says what to change, and the skill
   records it in `voice.md`. It is skipped when the user says to write to the end.
5. Remaining chapters, in order, each written by a fresh subagent. A fact pass runs per
   batch and logs each edit, before and after, in `checks/factcheck.md`.
6. Assembly into `manuscript.md` by `scripts/book_check.py assemble`.
7. `scripts/book_check.py check`.
8. Acceptance gate by a fresh subagent: ACCEPT or BLOCK. One fix round re-judges only the
   changed sentences. After that the user decides, and the decision is recorded.

## Mechanical check

`scripts/book_check.py check` fails hard on:

- leftover markers, from one declared list (`MARKERS` in `book_check.py`; no other
  payload file repeats them, and writers get them from `book_check.py markers`)
- a `manuscript.md` SHA-256 that does not match the last verdict in
  `checks/acceptance.json` when that verdict passed, or in `--final` mode
- invalid `book.json` metadata
- a chapter file that differs from its copy in `manuscript.md` (assemble again)

`--final` also fails without a passing verdict (`ACCEPT` or `USER_APPROVED`). Editing a
blocked draft before the next gate round is expected and only reported.

It reports without failing: Korean angle-bracket placeholders outside code, the chapter
cross-reference list, length ratio, numbers without a source, term variants, heading
structure, and openings or closings repeated across the book.

## Output

Markdown only. EPUB build is not in this version, because pandoc and epubcheck have not
been verified on the supported Mac.

## Runtime and safety

`scripts/book_check.py` needs only the Python 3.9 standard library. The skill calls no
provider besides the host's own model and sends no telemetry. The payload carries no
manuscript or private source text.
