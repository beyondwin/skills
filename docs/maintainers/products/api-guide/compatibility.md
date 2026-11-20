# api-guide compatibility

The supported host is `claude-code` from the product registry, for local or
repository-based use. Live evidence for the current payload is `not_measured`.

- Codex: not supported. The skill publishes through Claude Code's Artifact tool.
- Grok, Cursor: not supported.
- Claude.ai, Cowork, Skills API upload, marketplace publishing, and cloud sync are not
  supported.

Terms: `not_measured` means not checked yet.

## Supported OS

The supported OS is macOS only. Windows and Linux are unsupported. A CI pass on Ubuntu is
not Linux support and is not macOS support evidence.

## Discovery path

```text
skills/api-guide/              repository source
└─ ~/.claude/skills/api-guide ─→ Claude Code
```

The one-off Python block in the product README makes the link. It never replaces a
different link, a dangling link, a file, a directory, or a target that appears after the
check.

## Runtime needs

- The Artifact tool, to publish and update the page.
- Read access to the server source and, for the to-do section, the consumer source.
- Git, to record commits and compute the diff against the base.
