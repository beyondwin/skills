# beyondwin-skills

[한국어](README.md)

This repository collects three skills you can install in Codex. Use them to edit Korean you already wrote, make images that belong in this project, or explain how a machine works.

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

The license is Apache-2.0.

## Standalone products

The current standalone products are these three. A fourth product is out of scope unless governance is reopened.

| Skill | Role |
| --- | --- |
| [`korean-writing-editor`](skills/korean-writing-editor/README.en.md) | Takes Korean text you already have and fixes spelling and sentences without changing the meaning. |
| [`image-workbench`](skills/image-workbench/README.en.md) | Plans, makes, or edits PNG/JPG images that belong in this project. |
| [`graspic`](skills/graspic/README.en.md) | Explains how one machine works, at a depth you pick, in writing and diagrams. |

Use each product README for install and first invocation.

## Install

The primary Codex path is `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists; it does not replace an existing install.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/graspic
```

Install, update, uninstall, and the third-party installer are in [Installation](docs/users/en/installation.md).

Provider-free verification:

```bash
python3 scripts/verify.py
```

The default is `--profile full`. Windows portable verification is `python3 scripts/verify.py --profile windows-portable`. Live `--execute` is not included.

## Safety

This repository has no telemetry. Required CI does not use credentials, models, or remote image calls. This plugin is not claimed to be listed in a plugin directory.

Do not use `korean-writing-editor` for translation, drafting, summarization, code review, casual conversation, authorship detection, or detector evasion. Do not use `image-workbench` for casual one-off images, SVG or native UI, actual frontend implementation, or copying an external prompt gallery. Do not use `graspic` for debugging, implementing, reviewing, translating, one-line factual lookups, child-register explainers, or as a stand-in for `/eli5`.

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
