# beyondwin-skills

[한국어](README.md)

This repository publishes three curated Codex-first Agent Skills for conservative Korean editing, project-bound raster asset work, and mechanistic explanation.

[![CI](https://github.com/beyondwin/skills/actions/workflows/verify.yml/badge.svg)](https://github.com/beyondwin/skills/actions/workflows/verify.yml)
[![Release](https://img.shields.io/github/v/release/beyondwin/skills)](https://github.com/beyondwin/skills/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

The `beyondwin-skills` plugin bundle, the repository release identity, and skill metadata versions start at `2.0.0`. The license is Apache-2.0.

## Skill catalog and support

The catalog contains exactly these three skills. A fourth skill is out of scope unless governance is reopened.

| Skill | Role | Support |
| --- | --- | --- |
| `korean-writing-editor` | Conservatively proofreads, corrects, or polishes Korean text the user already supplied. | korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke. |
| `image-workbench` | Plans, generates, edits, compares, or audits a raster asset for a local project. | image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing. |
| `graspic` | Explains how one machine works at a chosen rung (picture, path, skeleton, or fracture). | graspic: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke. |

## One-minute install and invocation

The primary Codex path is `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists; it does not replace an existing install.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/graspic
```

After install, invoke explicitly on the next turn:

```text
$korean-writing-editor Proofread the supplied Korean source and keep meaning and voice.
$image-workbench Plan or generate a project-bound raster asset for this repository.
$graspic Explain DNS as a path.
```

Optional third-party installer (Korean editor only):

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

That `npx` command is a third-party installer with its own release and telemetry policy. It is not the primary Codex path and does not establish `image-workbench` compatibility.

The non-`npx` alternative is a verified Git clone plus host-native folder installation. Inspect the destination first and do not copy over an unexpected existing directory.

```bash
git clone https://github.com/beyondwin/skills.git
```

Exact-target inspection, update, and uninstall are in [Getting started](docs/en/getting-started.md). Provider-free verification:

```bash
python3 scripts/verify.py
```

The default is `--profile full`. Windows portable verification is `python3 scripts/verify.py --profile windows-portable`. Live `--execute` is not included.

## Exclusions and safety

This repository has no telemetry. Required CI does not use credentials, models, or remote image calls. This plugin is not claimed to be listed in a plugin directory.

Do not use `korean-writing-editor` for translation, drafting, summarization, code review, casual conversation, authorship detection, or detector evasion. Do not use `image-workbench` for casual one-off images, SVG or native UI, actual frontend implementation, or copying an external prompt gallery. Do not use `graspic` for debugging, implementing, reviewing, translating, one-line factual lookups, child-register explainers, or as a stand-in for `/eli5`.

Install, update, and uninstall touch only an inspected exact target. Do not pipe remote scripts into a shell, copy without inspecting the destination, delete parent skill directories, or replace an existing install by default.

## Offline and live evidence

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

Offline success does not prove general Korean editing quality, semantic equivalence, live image quality, commercial permission, a better provider, or cross-runtime parity.

## Documentation and community

- [Getting started](docs/en/getting-started.md)
- [Compatibility](docs/en/compatibility.md)
- [Privacy and rights](docs/en/privacy-and-rights.md)
- [Evaluation](docs/en/evaluation.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [License](LICENSE)
- [Korean README](README.md)
