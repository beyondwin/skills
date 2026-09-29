# beyondwin/skills

[한국어](README.ko.md)

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Six skills for AI coding tools like Codex, Claude Code, Cursor, and Grok. Install only
the ones you want; each one stands alone.

The supported OS is macOS only. Windows and Linux are unsupported. A passing Ubuntu CI
run is not Linux support and is not macOS support evidence.

## Skills

These are the current standalone products. A host is the tool that runs the skill.

| Skill | What it does | Hosts |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.md) | Fixes spelling and sentences in Korean text you already have, keeping the meaning. | Codex |
| [`image-workbench`](skills/image-workbench/README.md) | Plans, makes, or edits an image (PNG, JPG) that must fit your project. | Codex, Grok |
| [`how-it-works`](skills/how-it-works/README.md) | Explains how something works, with a diagram, at the depth you pick. | Codex, Claude Code |
| [`pre-sdd-review`](skills/pre-sdd-review/README.md) | Checks an approved spec and plan against your repo right before SDD, fixes them, and re-checks. | Codex |
| [`sddx`](skills/sddx/README.md) | Runs a plan the waygent way in your session and hands only the coding to Cursor Agent or Grok Build. Needs `waygent` installed too. | Claude Code, Codex |
| [`waygent`](skills/waygent/README.md) | Runs a plan task by task with a fresh subagent each: tests first, one review per task, one final review. | Claude Code, Codex, Cursor |

Each skill README shows how to install it and make the first call.

## Install

In Codex, install Korean Writing Editor, Image Workbench, or Pre-SDD Review with
`$skill-installer` ([Codex install](docs/users/en/install-codex.md)):

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

The other skills, and Image Workbench on Grok, link from a clone of this repo
([Local links](docs/users/en/install-local.md)):

- https://github.com/beyondwin/skills/tree/main/skills/how-it-works
- https://github.com/beyondwin/skills/tree/main/skills/sddx
- https://github.com/beyondwin/skills/tree/main/skills/waygent

Updates, removal, and every option are in [Installation](docs/users/en/installation.md).

## Verify

Check the repo rules offline, with no credentials and no model calls
([what a pass means](docs/users/en/verification.md)):

```bash
python3 scripts/verify.py
```

## Docs

- [Documentation index](docs/README.md): user guides, maintainer docs, history, research
- [Compatibility](docs/users/en/compatibility.md) and [Safety and privacy](docs/users/en/safety-and-privacy.md) (no telemetry)
- [Contributing](CONTRIBUTING.md), [Security](SECURITY.md), [Code of conduct](CODE_OF_CONDUCT.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
