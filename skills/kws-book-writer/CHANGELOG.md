# Changelog

All notable changes to this product are documented in this file.

## Unreleased

- First version: explicit `/kws-book-writer` invocation in Claude Code drafts a Korean
  technical or nonfiction book in a workspace folder: brief, research ledger, a plan the
  user approves, first-chapter calibration, then the remaining chapters in order, each
  written by a fresh subagent, with a fact pass per batch.
- `scripts/book_check.py` assembles `manuscript.md` and checks it. Hard failures: leftover
  markers, a manuscript SHA-256 that does not match `checks/acceptance.json`, and invalid
  `book.json` metadata. Other findings are reported, not failed.
- A fresh-subagent acceptance gate returns ACCEPT or BLOCK, allows one fix round, and then
  records the user's decision.
  The gate is a plain review instruction with the workspace files as input.
- `book_check.py` also fails when a chapter differs from its copy in `manuscript.md`,
  keeps inline code in table-of-contents headings, and reports bold that will not render
  before a Korean particle (`**용어(term)**은`). Term-table variants match only at the
  start of a word.
- Output is Markdown; EPUB build is not included. The runtime script needs only the Python
  standard library.
