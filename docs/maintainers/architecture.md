# Architecture

This repository is one Codex plugin named `beyondwin-skills` at version `2.0.0`. The catalog is exactly `korean-writing-editor` and `image-workbench`. Apache-2.0 applies at the root and in each standalone skill.

## Payload, tests, and docs

Only `skills/` is the installed skill payload. Human quick starts, change protocols, offline evaluations, live runners, release procedures, and migration records stay outside that payload.

| Tree | Role | Installed? |
| --- | --- | --- |
| `skills/<name>/` | Runtime `SKILL.md`, references, per-skill `LICENSE.txt`, `agents/openai.yaml`, and `image-workbench` inspector | Yes |
| `.codex-plugin/plugin.json` | Plugin manifest pointing `skills` at `./skills/` | Plugin bundle only |
| `tests/contract/` | Manifest, frontmatter, link, packaging, version, license, and public-doc facts | No |
| `tests/korean-writing-editor/offline/` | Deterministic trigger, mode, preservation, and output fixtures | No |
| `tests/korean-writing-editor/live/` | Synthetic live harness, unit tests, dry-run, operator guide | No |
| `tests/image-workbench/` | Routing, authorization, evidence, and inspector tests | No |
| `docs/ko/`, `docs/en/` | Paired public install, compatibility, privacy, evaluation | No |
| `docs/maintainers/` | Architecture, release, per-skill protocol, Archive freeze | No |
| `scripts/verify.py` | Provider-free orchestrator | No |

Payload directories must not contain `README.md`, `CHANGE_PROTOCOL.md`, `evals/`, or `tests/`. The image inspector `skills/image-workbench/scripts/inspect_asset.py` is runtime code; its tests live under `tests/image-workbench/`.

## Interfaces

- Plugin discovery: `.codex-plugin/plugin.json` lists `./skills/` and no MCP servers, apps, or hooks.
- Skill identity: directory name, `SKILL.md` `name`, and version `2.0.0` must match. `license: Apache-2.0` is top-level frontmatter.
- Korean offline runner: `tests/korean-writing-editor/offline/run.py --skill-root PATH` with cases beside the runner.
- Image evaluator: `tests/image-workbench/run.py --skill-root PATH` with cases beside the runner.
- Inspector: resolve `python3 scripts/inspect_asset.py` from the skill root, not from a repository-relative `skills/` path.
- Live harness: source skill is `<repo>/skills/korean-writing-editor`; reports stay under an explicit ignored evidence root.
- Public facts: Korean and English docs must agree on commands, versions, support states, and limitations.

## Verification boundary

Required local verification is:

```bash
python3 scripts/verify.py
```

That command is credential-free and provider-free. Live Korean evaluation remains an explicit local operation. See [korean-writing-editor.md](korean-writing-editor.md), [image-workbench.md](image-workbench.md), [release-process.md](release-process.md), and [archive-migration.md](archive-migration.md).
