# Compatibility

[한국어](../ko/compatibility.md) · [Getting started](getting-started.md)

Codex is the first-class runtime for both skills. The catalog is exactly `korean-writing-editor` and `image-workbench` at version `2.0.0`.

## Shared support sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## Contract portability versus measured support

`korean-writing-editor` follows the open Agent Skills directory format (`SKILL.md`, optional `scripts/`, `references/`, and `assets/`). That contract portability does not mean Claude Code, Cursor, or any other host is supported today. A host is `supported` only after a current smoke test; otherwise its status is `partially verified` or `not_measured`.

`image-workbench` is Codex-only. Similar tools in another host do not establish compatibility. `brief` and `audit` can run read-only, but generate or edit requires Codex built-in image generation and local image viewing.

The plugin name `beyondwin-skills` means the repository is packaged as one plugin. It does not mean the plugin is listed in a plugin directory.

## Install paths and hosts

- Primary: `$skill-installer` with the public GitHub skill path. See [Getting started](getting-started.md).
- Optional: third-party `npx skills add beyondwin/skills --skill korean-writing-editor`. That installer has its own policy.
- Alternative: `git clone` plus host-native folder install. Inspect the exact target before copying.

Windows-meaningful checks are the Korean-editor offline suite and repository contracts. Do not claim `image-workbench` generate or edit support except where the Codex prerequisites exist.

The license is Apache-2.0. Provider-free verification is `python3 scripts/verify.py`.
