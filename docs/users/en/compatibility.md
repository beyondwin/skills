# Compatibility

[한국어](../ko/compatibility.md) · [Installation](installation.md)

The current standalone products are [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), and [`how-it-works`](../../../skills/how-it-works/README.en.md). Only How It Works has the four-host claim. Korean Writing Editor and Image Workbench keep their registered Codex boundaries.

## Shared support sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

how-it-works: Codex, Claude Code, Grok, and Cursor supported for local or repository-based use.

## Contract portability versus measured support

`korean-writing-editor` follows the open Agent Skills directory format (`SKILL.md`, optional `scripts/`, `references/`, and `assets/`). That contract portability does not mean Claude Code, Cursor, or any other host is supported today. A host is `supported` only after a current smoke test; otherwise its status is `partially verified` or `not_measured`.

`image-workbench` is Codex-only. Similar tools in another host do not establish compatibility. `brief` and `audit` can run read-only, but generate or edit requires Codex built-in image generation and local image viewing.

`how-it-works` supports `codex`, `claude-code`, `grok`, and `cursor` for local or repository-based use. Output is GitHub-flavored markdown in chat, plus mermaid source and a numbered hop list. A host page or mermaid renderer is not required. Claude.ai, Cowork, Skills API upload, and marketplace publication are not supported.

The immutable catalog `v2.0.0` plugin bundle does not include How It Works. The plugin name `beyondwin-skills` means the repository is packaged as one plugin. It does not mean the plugin is listed in a plugin directory.

## Install paths and hosts

- Codex primary: `$skill-installer` with the public GitHub skill path. See [Installation](installation.md).
- How It Works: `~/.agents/skills/how-it-works` (Codex, Grok, Cursor) and `~/.claude/skills/how-it-works` (Claude Code). `ln -s` fails instead of overwriting an existing target.
- Optional: third-party `npx skills add beyondwin/skills --skill korean-writing-editor`. That installer has its own policy.
- Alternative: `git clone` plus host-native folder install. Inspect the exact target before copying.

Windows-meaningful checks are the Korean-editor offline suite and repository contracts. Do not claim `image-workbench` generate or edit support except where the Codex prerequisites exist.

The license is Apache-2.0. Provider-free verification is `python3 scripts/verify.py`.
