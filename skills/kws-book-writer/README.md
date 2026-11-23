# KWS Book Writer

Use this skill only by explicitly invoking `/kws-book-writer` in Claude Code.
Matching requests alone do not activate it.

[한국어](README.ko.md)

## Purpose

KWS Book Writer drafts a Korean technical or nonfiction book in a workspace folder you
choose. It works in fixed phases and keeps every working file in that folder:

- a brief (`brief.md`) and a research ledger with sources (`research/ledger.md`)
- a chapter plan (`plan.md`) that you approve before any chapter is written
- a first-chapter calibration, on by default: you say what to change, and the result is
  recorded in `voice.md`. Skip it by saying to write through to the end.
- the remaining chapters (`chapters/NN.md`), in order, each written by a fresh subagent,
  with a fact pass per batch that logs each edit before and after in
  `checks/factcheck.md`
- assembly into `manuscript.md` and a mechanical check by `scripts/book_check.py`
- an acceptance gate run by a fresh subagent that returns ACCEPT or BLOCK, one fix round,
  and then your decision, which is recorded

Book metadata lives in `book.json`. The output is Markdown.

## When to use and not use

Use it when you want a full first draft of a Korean technical or nonfiction book and are
willing to approve the plan and review the first chapter.

Don't use it for a single article or blog post, to proofread or edit Korean text you
already wrote (`korean-writing-editor`), to explain one mechanism (`/how-it-works`), for
fiction or translation, or to build an EPUB or a print file. EPUB build is not included
yet.

## Supported hosts

kws-book-writer: Claude Code supported for local or repository-based use.

The host id is `claude-code`. The skill needs subagents, file writes in the workspace
folder, and Python 3 for `scripts/book_check.py`, which uses only the standard library.
Live runs on macOS are recorded in the repository's evaluation notes; the final install files were not run end to end. Codex, Grok, and Cursor are
not supported.

Claude.ai, Cowork, Skills API upload, and marketplace publishing are not supported.
Shared limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Clone the repo and link the skill folder into Claude Code's skill folder.

Public path: https://github.com/beyondwin/skills/tree/main/skills/kws-book-writer

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills
```

The Python block below takes two arguments, source (the skill folder) and target
(where the link goes), and makes the link.

- It first checks that source is a real skill folder.
- If the same link is already there, that counts as success.
- It does not replace a different link, dangling link, file, or directory.
- It also stops if the target shows up after the check. Look at it, then retry.

<!-- kws-book-writer-local-links -->
```python
import os
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: python3 - SOURCE TARGET")
source = Path(sys.argv[1]).expanduser().resolve(strict=True)
target = Path(os.path.abspath(os.path.expanduser(sys.argv[2])))
if not source.is_dir() or not (source / "SKILL.md").is_file():
    raise SystemExit("source must be a skill directory")
if target.is_symlink():
    try:
        same = target.resolve(strict=True) == source
    except (OSError, RuntimeError):
        same = False
    if same:
        print("already linked")
        raise SystemExit(0)
    raise SystemExit("refusing different or dangling link")
if target.exists():
    raise SystemExit("refusing existing file or directory")
target.parent.mkdir(parents=True, exist_ok=True)
try:
    target.symlink_to(source, target_is_directory=True)
except FileExistsError:
    raise SystemExit("target appeared during installation; inspect it before retrying")
print("linked")
```

Feed the block on standard input with a quoted here-document (`<<'PY'`):

`python3 - "$PWD/skills/kws-book-writer" "$HOME/.claude/skills/kws-book-writer" <<'PY'`

After that first line, paste the Python block as is, then end with `PY` on its own
line. Keep the quotes around source and target.

Update and removal steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

Start Claude Code in an empty folder for the book, or name the folder, and call the
skill by name with the topic and the reader.

```text
/kws-book-writer
/kws-book-writer A book on PostgreSQL indexing for backend developers, about 10 chapters
```

## Expected result

A workspace folder with `brief.md`, `research/ledger.md`, `plan.md`, `voice.md`,
`chapters/NN.md`, `checks/`, `book.json`, and `manuscript.md`, plus a short chat report.

The skill stops twice for you: to approve the plan, and after the first chapter unless
you asked it to write through to the end. At the end the chat report gives the check
result, the acceptance verdict (ACCEPT or BLOCK), what was fixed in the fix round, and
what is left for you to decide.

`book_check.py check` fails hard on leftover markers, a manuscript that changed after
acceptance (its SHA-256 no longer matches `checks/acceptance.json`), invalid
`book.json` metadata, or a chapter file that differs from `manuscript.md`. With `--final`
it also fails without a passing verdict. It reports, without failing, placeholders left
outside code, chapter cross-references, length ratios, numbers without a source, term
variants, heading structure, process words visible to readers, bold that will not render,
and openings or closings repeated across the book.

The manuscript is a draft. Facts that the fact pass could not trace to a source are
reported, not hidden. Keep the workspace folder private; it is your manuscript.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-book-writer/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-book-writer/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-book-writer/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-book-writer/release.md)
