# beyondwin/skills

[한국어](README.md)

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Five skills for AI coding tools such as Codex, Claude Code, and Grok. Pick the
ones you need and install each one on its own. The license is Apache-2.0.

The supported OS is macOS only. Windows and Linux are unsupported. A passing Ubuntu CI
run is not Linux support and is not macOS support evidence.

## Choose a skill

The current standalone products are these five. A host is the program that runs
the skill.

| Skill | What it does | Hosts |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.en.md) | Takes Korean text you already have and fixes spelling and sentences without changing the meaning. | Codex |
| [`image-workbench`](skills/image-workbench/README.en.md) | Plans, makes, or edits PNG/JPG images that belong in this project. | Codex, Grok |
| [`how-it-works`](skills/how-it-works/README.en.md) | Explains how one machine works, at a depth you pick, in writing and diagrams. | Codex, Claude Code |
| [`pre-sdd-review`](skills/pre-sdd-review/README.en.md) | Right before SDD, checks an approved design and implementation plan against the repository as it is now, repairs the documents, and re-checks what changed. | Codex |
| [`sddx`](skills/sddx/README.en.md) | Runs Superpowers SDD in your session and hands only the coding to Cursor Agent or Grok Build (Grok 4.7). | Claude Code, Codex |

Each skill README has usage and first-call steps.

## Install

There are two install methods, depending on the host.

Korean Writing Editor, Image Workbench, and Pre-SDD Review install in Codex with
`$skill-installer`. Full steps are in [Codex install](docs/users/en/install-codex.md).

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

How It Works and SDDx (Codex, Claude Code), and Image Workbench on Grok, use a
shortcut (symbolic link) to a clone of this repo. Steps are in
[Local links](docs/users/en/install-local.md). The public paths are:

- How It Works: https://github.com/beyondwin/skills/tree/main/skills/how-it-works
- SDDx: https://github.com/beyondwin/skills/tree/main/skills/sddx

The per-skill method table, update and uninstall, and the third-party installer
are reachable from [Installation](docs/users/en/installation.md).

## Verify

Check the repo rules without credentials or model calls.

```bash
python3 scripts/verify.py
```

What the check covers, and what a pass means, is in
[Verification](docs/users/en/verification.md).

## Safety

This repository has no telemetry. Details are in
[Safety and privacy](docs/users/en/safety-and-privacy.md).

## Documentation and community

- [Documentation index](docs/README.md)
- [Installation](docs/users/en/installation.md)
- [Compatibility](docs/users/en/compatibility.md)
- [Safety and privacy](docs/users/en/safety-and-privacy.md)
- [Verification](docs/users/en/verification.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [License](LICENSE)
- [Korean README](README.md)
