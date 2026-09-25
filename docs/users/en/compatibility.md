# Compatibility

[한국어](../ko/compatibility.md) · [Installation](installation.md)

The skills in use are [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), [`how-it-works`](../../../skills/how-it-works/README.en.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.en.md), and [`sddx`](../../../skills/sddx/README.en.md).

| Skill | Supported hosts |
| --- | --- |
| Korean Writing Editor | Codex only |
| Pre-SDD Review | Codex only |
| Image Workbench | Codex, Grok |
| How It Works | Codex, Claude Code (linked from this repo) |
| SDDx | Codex, Claude Code (linked from this repo) |

Terms:

- host: the program that runs the skill
- smoke: a recorded live run
- `not_measured`: not checked yet
- `historical-unbound`: an old record, not current execution evidence
- `current-bounded`: only version and hash are bound

## Shared support sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.

how-it-works: Codex and Claude Code supported for local or repository-based use.

pre-sdd-review: Codex supported; other hosts not_measured.

sddx: Claude Code and Codex supported for local or repository-based use.

## Contract portability versus measured support

A matching folder layout does not mean that host is supported. Adding a new supported host requires smoke evidence from the current build and an explicit support decision. Established support scope and current measurement status are separate. Record unmeasured current execution as `not_measured`; that alone does not change the established support scope. See each product README for the product guide.

`how-it-works` supports Codex and Claude Code for local or repository-based use. Claude.ai, Cowork, Skills API upload, and marketplace publication are not supported.

`image-workbench` can make or edit an image only when the current host has its own image tool and you can open the result. Otherwise, do not say it can make or edit images. A similar tool on another host is not support. The Grok shortcut is `~/.agents/skills/image-workbench`.

Other hosts for `pre-sdd-review` have not been checked yet (`not_measured`).

The preserved `how-it-works` smoke is `historical-unbound`; it is separate from current payload and model execution evidence. Actual execution of the current install files is `not_measured`. `current-bounded` validates version/hash and metadata binding only, not actual execution or explanation quality.

## Operating system

The supported OS is macOS only. Windows and Linux are unsupported. CI may run the `full` profile on Ubuntu. That pass is not Linux support and is not macOS support evidence.

## Install paths and hosts

The catalog plugin name is `beyondwin-skills`. That does not mean a marketplace listing.

Install, link, and remove steps are in [Installation](installation.md). Verification is in [Verification](verification.md).

The license is Apache-2.0.
