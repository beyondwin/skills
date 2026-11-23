---
name: kws-book-writer
description: Use when explicitly invoked and the user wants a multi-chapter Korean nonfiction or technical book drafted from sources such as a code repository, documents, or notes, with a plan the user approves, chapter-by-chapter drafting, fact checks against a source ledger, and an acceptance check. Do not use for a single article or blog post, editing or proofreading existing Korean text (korean-writing-editor), explaining one mechanism (how-it-works), fiction, translation, or EPUB/PDF typesetting.
disable-model-invocation: true
license: Apache-2.0
compatibility: Requires Claude Code with the Agent tool for fresh subagents, and python3 (3.9 or newer) for scripts/book_check.py.
metadata:
  version: "0.1.0"
  updated_at: "2026-11-20"
---

# kws-book-writer

Activate only on explicit invocation: `/kws-book-writer`. Matching task text alone does not activate it.

You are the orchestrator. You keep the plan and the files in order; fresh subagents write
chapters, check facts, and judge the finished book. Write reader-facing text in Korean.
`<skill-dir>` below is this skill's base directory; `<ws>` is the book workspace.

## Invariants

- Every fact in a chapter traces to a ledger entry. A writer that lacks a fact leaves a marker
  from `python3 <skill-dir>/scripts/book_check.py markers` instead of inventing or padding.
  That command is the only list of markers; paste its output into every writer brief.
- The user approves the plan before any chapter is written. Ask nothing else mid-run except
  the first-chapter calibration and a gate that blocks twice.
- A subagent's "no problems" is not evidence. Keep what changed (before/after) on file.
- Never edit the sources the book is about. Write only inside `<ws>`.
- Only `book_check.py` hard failures block. Its report-only items are things to read and
  judge, not rules to satisfy mechanically.

## Workspace and resume

`<ws>` defaults to `./book-<slug>/` in the current directory; use a path the user names.
On every invocation, list `<ws>` first and resume at the first phase whose required output
is missing or stale. Say which phase you are resuming. File formats and the resume table are
in [references/workflow.md](references/workflow.md).

## Phases and required outputs

| # | Phase | Required output | Read first |
| --- | --- | --- | --- |
| 1 | Brief: ask all open questions in one message; use defaults for the rest and say which | `brief.md` | [workflow.md](references/workflow.md) |
| 2 | Research ledger: read the sources (subagents may split areas) | `research/ledger.md` | [workflow.md](references/workflow.md) |
| 3 | Plan, then stop for approval | `plan.md`, `voice.md`, `book.json` | [plan.md](references/plan.md), [voice.md](references/voice.md) |
| 4 | First-chapter calibration, then stop for the user's changes | `chapters/01.md`, calibration notes in `voice.md` | [chapter.md](references/chapter.md) |
| 5 | Remaining chapters in order, a fact pass after each batch of up to three | `chapters/NN.md`, `checks/factcheck.md` | [chapter.md](references/chapter.md) |
| 6 | Assemble, polish chapter boundaries two chapters at a time, assemble again | `manuscript.md`, `front/`, `back/` | [workflow.md](references/workflow.md) |
| 7 | `book_check.py check`, then the acceptance gate | `checks/check-report.md`, `checks/acceptance.md`, `checks/acceptance.json` | [acceptance.md](references/acceptance.md) |

Phase 3 stop: show the chapter list with each chapter's reader promise, the term table, and
the defaults you chose, then end the turn. Continue only on approval; apply requested changes
first. Phase 4 stop: give the path to `chapters/01.md`, ask what to change, and end the turn.
Record the answer in `voice.md` and revise chapter 1. If the user said to write to the end
without stopping, skip the phase 4 stop and say so in the final report.

## Dispatching subagents

- One fresh subagent per chapter, in chapter order. Wait for each result before starting the
  next one; do not end your turn while a subagent is running.
- Give a subagent file paths and its task, not your conversation. The briefs are in
  [chapter.md](references/chapter.md) and [acceptance.md](references/acceptance.md).
- After each subagent returns, read its file. If it ignored the plan's opening, closing, or
  length, send it back once with the specific gap.

## Commands

```bash
python3 <skill-dir>/scripts/book_check.py markers
python3 <skill-dir>/scripts/book_check.py assemble <ws>
python3 <skill-dir>/scripts/book_check.py check <ws>            # draft
python3 <skill-dir>/scripts/book_check.py accept <ws> --verdict ACCEPT|BLOCK|USER_APPROVED --note "..."
python3 <skill-dir>/scripts/book_check.py check <ws> --final    # done only when this exits 0
```

Any edit to a chapter after assembly means: assemble again, check again. An accepted
manuscript that changes needs the gate again; the script enforces this with the SHA-256 in
`checks/acceptance.json`.

## Done

The book is done when `check <ws> --final` exits 0. Report to the user in Korean:

- the manuscript path, chapter count, and character count
- the gate verdicts by round, and any user decision that closed a block
- open report-only items you chose not to fix, with one reason each
- whether the phase 4 stop was skipped
