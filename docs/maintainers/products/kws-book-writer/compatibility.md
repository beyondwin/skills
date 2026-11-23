# kws-book-writer compatibility

The supported host is `claude-code` from the product registry, for local or
repository-based use. Live runs on macOS with Claude Code 2.1.322 are recorded in the
[evaluation](../../../research/2026-11-kws-book-writer-eval/README.md); the final payload
was not run end to end after the last gate change.

- Codex: not supported. The workflow relies on Claude Code subagents.
- Grok, Cursor: not supported.
- Claude.ai, Cowork, Skills API upload, marketplace publishing, and cloud sync are not
  supported.

Terms: `not_measured` means not checked yet.

## Supported OS

The supported OS is macOS only. Windows and Linux are unsupported. A CI pass on Ubuntu is
not Linux support and is not macOS support evidence.

## Discovery path

```text
skills/kws-book-writer/              repository source
└─ ~/.claude/skills/kws-book-writer ─→ Claude Code
```

The one-off Python block in the product README makes the link. It never replaces a
different link, a dangling link, a file, a directory, or a target that appears after the
check.

## Runtime needs

- Subagents, for chapters and the acceptance gate.
- Write access to the user's workspace folder.
- Python 3.9 or later, standard library only, for `scripts/book_check.py`.
- No pandoc or epubcheck: EPUB build is not in this version.
