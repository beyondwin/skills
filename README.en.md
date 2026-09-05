# beyondwin-skills

[한국어](README.md)

Four skills live here. Korean Writing Editor, Image Workbench, and Pre-SDD
Review install in Codex. How It Works installs for local or repository-based use
in Codex and Claude Code.

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

The license is Apache-2.0.

## Standalone products

The current standalone products are these four. The catalog bundle `v2.0.0`
does not include How It Works or Pre-SDD Review.

| Skill | Role | Hosts |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.en.md) | Takes Korean text you already have and fixes spelling and sentences without changing the meaning. | Codex |
| [`image-workbench`](skills/image-workbench/README.en.md) | Plans, makes, or edits PNG/JPG images that belong in this project. | Codex |
| [`how-it-works`](skills/how-it-works/README.en.md) | Explains how one machine works, at a depth you pick, in writing and diagrams. | Codex, Claude Code |
| [`pre-sdd-review`](skills/pre-sdd-review/README.en.md) | Checks an approved design and implementation plan against repository reality immediately before SDD, repairs the documents, and re-reviews them. | Codex |

Each product README has install and first-call steps.

## Install

For Korean Writing Editor, Image Workbench, and Pre-SDD Review, use
`$skill-installer` with the public GitHub skill path.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

The How It Works public path is
https://github.com/beyondwin/skills/tree/main/skills/how-it-works.

Install, update, uninstall, How It Works local links, and the third-party
installer are in [Installation](docs/users/en/installation.md).

To check the repo without a model:

```bash
python3 scripts/verify.py
```

Profiles and evidence limits are in
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
