# Compatibility

[한국어](../ko/compatibility.md) · [Installation](installation.md)

This page says which hosts each skill runs on. A host is the agent app that runs the skill. Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`how-it-works`](../../../skills/how-it-works/README.md).

| Skill | Supported hosts | How you install it |
| --- | --- | --- |
| Korean Writing Editor | Codex | `$skill-installer` |
| How It Works | Codex, Claude Code | Local link |

Terms:

- smoke: a recorded live run
- `not_measured`: not checked yet
- `current-bounded`: only the version and hash are tied to the record, not a real run

## Shared support sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

how-it-works: Codex and Claude Code supported for local or repository-based use.

## What counts as support

A skill folder that another host can read is not support. A new host needs a recorded smoke on the current build and an explicit decision. Support scope and measurement status are separate: if the current files have not been run, the status is `not_measured`, and the support scope stays the same.

None of these skills works through Claude.ai, Cowork, or a Skills API upload, and none is published to a marketplace.

## Per-skill notes

- `how-it-works`: a live run of the current install files is `not_measured`.

## Operating system

The supported OS is macOS only. Windows and Linux are unsupported. CI may run the full verification on Ubuntu. That pass is not Linux support and is not macOS support evidence.

## More

Install, link, and remove steps are in [Installation](installation.md). Checks are in [Verification](verification.md). The license is Apache-2.0.
