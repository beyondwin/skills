# beyondwin/skills

[한국어](README.ko.md)

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Five skills for AI coding tools like Codex, Claude Code, and Grok. Install only
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
| [`grok-video`](skills/grok-video/README.md) | Makes one Grok video and asks only when the subject, change, line, or photo is missing. | Grok |
| [`grok-image`](skills/grok-image/README.md) | Makes a Grok still from a concrete scene, and asks once when the subject is missing. | Grok |

Each skill README shows how to install it and make the first call.

## Install

In Codex, install Korean Writing Editor or Image Workbench with
`$skill-installer` ([Codex install](docs/users/en/install-codex.md)):

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

How It Works, Image Workbench on Grok, Grok Video, and Grok Image link from a clone of this repo
([Local links](docs/users/en/install-local.md)):

- https://github.com/beyondwin/skills/tree/main/skills/how-it-works
- https://github.com/beyondwin/skills/tree/main/skills/grok-video
- https://github.com/beyondwin/skills/tree/main/skills/grok-image

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
