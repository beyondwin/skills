# Compatibility

[한국어](../ko/compatibility.md) · [Installation](installation.md)

This page says which hosts each skill runs on. A host is the agent app that runs the skill. Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`how-it-works`](../../../skills/how-it-works/README.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.md), [`sddx`](../../../skills/sddx/README.md), [`waygent`](../../../skills/waygent/README.md).

| Skill | Supported hosts | How you install it |
| --- | --- | --- |
| Korean Writing Editor | Codex | `$skill-installer` |
| Pre-SDD Review | Codex | `$skill-installer` |
| Image Workbench | Codex, Grok | Codex: `$skill-installer`. Grok: local link |
| How It Works | Codex, Claude Code | Local link |
| SDDx | Claude Code, Codex | Local link |
| Waygent | Claude Code, Codex, Cursor Agent, Grok Build | Local link |

Terms:

- smoke: a recorded live run
- `not_measured`: not checked yet
- `current-bounded`: only the version and hash are tied to the record, not a real run

## Shared support sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.

how-it-works: Codex and Claude Code supported for local or repository-based use.

pre-sdd-review: Codex supported; other hosts not_measured.

sddx: Claude Code and Codex supported for local or repository-based use.

waygent: Claude Code, Codex, Cursor Agent, and Grok Build supported for local or repository-based use.

## What counts as support

A skill folder that another host can read is not support. A new host needs a recorded smoke on the current build and an explicit decision. Support scope and measurement status are separate: if the current files have not been run, the status is `not_measured`, and the support scope stays the same.

None of these skills works through Claude.ai, Cowork, or a Skills API upload, and none is published to a marketplace.

## Per-skill notes

- `image-workbench` makes or edits an image only when the current host has its own image tool and you can open the result. A similar tool on another host does not count. On Grok it uses the `~/.agents/skills/image-workbench` link.
- `pre-sdd-review` has not been checked on other hosts (`not_measured`).
- `how-it-works`: a live run of the current install files is `not_measured`.
- `sddx`: Cursor Agent and Grok Build are workers it hands tasks to, not hosts. It needs `waygent` linked next to it on the same host.
- `waygent`: every host must be able to start subagents. Codex needs `multi_agent = true` under `[features]` in `~/.codex/config.toml`. Measured runs are in the [waygent compatibility record](../../maintainers/products/waygent/compatibility.md).

## Operating system

The supported OS is macOS only. Windows and Linux are unsupported. CI may run the full verification on Ubuntu. That pass is not Linux support and is not macOS support evidence.

## More

Install, link, and remove steps are in [Installation](installation.md). Checks are in [Verification](verification.md). The license is Apache-2.0.
