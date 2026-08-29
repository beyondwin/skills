# beyondwin-skills

[한국어](README.md)

Four skills live here. Korean Writing Editor, Image Workbench, and Pre-SDD Review install in Codex. How It Works installs for local or repository-based use in Codex and Claude Code.

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

The license is Apache-2.0.

## Standalone products

The current standalone products are these four. The immutable catalog `v2.0.0` bundle does not include How It Works or Pre-SDD Review.

| Skill | Role | Hosts |
| --- | --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.en.md) | Takes Korean text you already have and fixes spelling and sentences without changing the meaning. | Codex |
| [`image-workbench`](skills/image-workbench/README.en.md) | Plans, makes, or edits PNG/JPG images that belong in this project. | Codex |
| [`how-it-works`](skills/how-it-works/README.en.md) | Explains how one machine works, at a depth you pick, in writing and diagrams. | Codex, Claude Code |
| [`pre-sdd-review`](skills/pre-sdd-review/README.en.md) | Checks an approved design and implementation plan against repository reality immediately before SDD, repairs the documents, and re-reviews them. | Codex |

Each product README has install and first-call steps. How It Works local links are in the product README and [Installation](docs/users/en/installation.md).

## Install

For Korean Writing Editor, Image Workbench, and Pre-SDD Review, use `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists. It does not replace an existing install.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

How It Works installs at `~/.agents/skills/how-it-works` (Codex) and `~/.claude/skills/how-it-works` (Claude Code). The public GitHub path is https://github.com/beyondwin/skills/tree/main/skills/how-it-works. Do not create a `~/.codex` duplicate.

Install, update, uninstall, and the third-party installer are in [Installation](docs/users/en/installation.md).

To check the repo without a model:

```bash
python3 scripts/verify.py
```

The default is `--profile full`. Windows portable verification is `python3 scripts/verify.py --profile windows-portable`. Live `--execute` is not included.

## Safety

This repository has no telemetry. Required CI does not use credentials, models, or remote image calls. This plugin is not claimed to be listed in a plugin directory.

Do not use the skills outside these bounds:

- `korean-writing-editor`: translation, drafting, summarization, code review, casual conversation, authorship detection, or detector evasion
- `image-workbench`: casual one-off images, SVG or native UI, actual frontend implementation, or copying an external prompt gallery
- `how-it-works`: debugging, implementing, reviewing, translating, one-line factual lookups, child-register explainers, or as a stand-in for `/eli5`
- `pre-sdd-review`: writing the first design or plan, reviewing code, or reviewing a release. It never starts implementation without an explicit outer request.

Install, update, and uninstall touch only an inspected exact target. Do not pipe remote scripts into a shell, copy without inspecting the destination, delete parent skill directories, or replace an existing install by default.

Details are in [Safety and privacy](docs/users/en/safety-and-privacy.md).

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
