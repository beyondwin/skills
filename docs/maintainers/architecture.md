# Architecture

This repository is a monorepo of independent skill products plus a separately versioned catalog plugin named `beyondwin-skills` at version `2.0.0`. Current `skills/` development contains `korean-writing-editor`, `image-workbench`, and `graspic`. The last published catalog locks only the two public `v2.0.0` skills. Apache-2.0 applies at the root and in each standalone skill.

## Payload, tests, and docs

The repository root is the workspace for individual skill installs. It does not own plugin metadata. Catalog plugin metadata lives at `catalog/plugin/.codex-plugin/plugin.json` and is copied to the plugin ZIP root at catalog release time. Only released plugin ZIPs are supported catalog artifacts.

Only `skills/` is the installed skill payload for GitHub-path installs. Human quick starts, change protocols, offline evaluations, live runners, release procedures, and migration records stay outside that payload.

| Tree | Role | Installed? |
| --- | --- | --- |
| `skills/<name>/` | Runtime `SKILL.md`, references, per-skill `LICENSE.txt`, `agents/openai.yaml`, and `image-workbench` inspector | Yes |
| `catalog/plugin/.codex-plugin/plugin.json` | Last published catalog plugin manifest source | Plugin bundle only |
| `catalog/catalog.lock.json` | Immutable skill releases adopted by the catalog | No |
| `catalog/release.toml` | Catalog identity (`beyondwin-skills` `2.0.0`) | No |
| `tests/contract/` | Manifest, frontmatter, link, packaging, version, license, and public-doc facts | No |
| `tests/korean-writing-editor/offline/` | Deterministic trigger, mode, preservation, and output fixtures | No |
| `tests/korean-writing-editor/live/` | Synthetic live harness, unit tests, dry-run, operator guide | No |
| `tests/image-workbench/` | Routing, authorization, evidence, and inspector tests | No |
| `tests/graspic/` | Shape fixtures for dump, HTML, comparison, scope, and gloss cases | No |
| `docs/ko/`, `docs/en/` | Paired public install, compatibility, privacy, evaluation | No |
| `docs/maintainers/` | Architecture, release, per-skill protocol, Archive freeze | No |
| `scripts/verify.py` | Provider-free orchestrator | No |

Payload directories must not contain `README.md`, `CHANGE_PROTOCOL.md`, `evals/`, or `tests/`. The image inspector `skills/image-workbench/scripts/inspect_asset.py` is runtime code; its tests live under `tests/image-workbench/`.

## Interfaces

- Plugin discovery: `catalog/plugin/.codex-plugin/plugin.json` is the catalog manifest source. Released plugin ZIPs place that file at `.codex-plugin/plugin.json`, list `./skills/`, and declare no MCP servers, apps, or hooks.
- Catalog identity: `catalog/release.toml` and the catalog plugin manifest share name `beyondwin-skills` and version `2.0.0`. `catalog/catalog.lock.json` pins adopted skill releases and need not match current `skills/` versions.
- Skill identity: directory name, `SKILL.md` `name`, and that product's `release.toml` version must match. `license: Apache-2.0` is top-level frontmatter.
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

That command is credential-free and provider-free. Live Korean evaluation remains an explicit local operation. See [korean-writing-editor.md](korean-writing-editor.md), [image-workbench.md](image-workbench.md), [graspic.md](graspic.md), [release-process.md](release-process.md), and [archive-migration.md](archive-migration.md).
