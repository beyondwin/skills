# Compatibility

[한국어](../ko/compatibility.md) · [Installation](installation.md)

Codex is the first-class runtime for the current standalone products. The current standalone products are [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), and [`graspic`](../../../skills/graspic/README.en.md).

## Shared support sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

graspic: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

## Contract portability versus measured support

`korean-writing-editor` follows the open Agent Skills directory format (`SKILL.md`, optional `scripts/`, `references/`, and `assets/`). That contract portability does not mean Claude Code, Cursor, or any other host is supported today. A host is `supported` only after a current smoke test; otherwise its status is `partially verified` or `not_measured`.

`image-workbench` is Codex-only. Similar tools in another host do not establish compatibility. `brief` and `audit` can run read-only, but generate or edit requires Codex built-in image generation and local image viewing.

`graspic` follows the open Agent Skills directory format. Output is GitHub-flavored markdown and mermaid. That contract portability does not mean another host is supported today.

The plugin name `beyondwin-skills` means the repository is packaged as one plugin. It does not mean the plugin is listed in a plugin directory.

## Install paths and hosts

- Primary: `$skill-installer` with the public GitHub skill path. See [Installation](installation.md).
- Optional: third-party `npx skills add beyondwin/skills --skill korean-writing-editor`. That installer has its own policy.
- Alternative: `git clone` plus host-native folder install. Inspect the exact target before copying.

Windows-meaningful checks are the Korean-editor offline suite and repository contracts. Do not claim `image-workbench` generate or edit support except where the Codex prerequisites exist.

The license is Apache-2.0. Provider-free verification is `python3 scripts/verify.py`.
