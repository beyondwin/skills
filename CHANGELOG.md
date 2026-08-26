# Changelog

All notable changes to this project are documented in this file.

## 2.0.0 - 2026-08-27

First public `beyondwin-skills` plugin and repository version identity.
GitHub tag `v2.0.0` and the four release artifacts are published at
https://github.com/beyondwin/skills/releases/tag/v2.0.0.
This does not claim a plugin-directory or marketplace listing.

### Added

- Codex plugin `beyondwin-skills` at version `2.0.0`. The manifest at
  `.codex-plugin/plugin.json` discovers exactly two skills under `./skills/`
  and does not declare MCP servers, apps, or hooks.
- Migrated skill `korean-writing-editor` `2.0.0`: conservatively proofreads,
  corrects, or polishes Korean text the user already supplied.
  korean-writing-editor: Codex supported; Agent Skills contract portable;
  other hosts only supported after a recorded smoke.
- Migrated skill `image-workbench` `2.0.0`: plans, generates, edits, compares,
  or audits a raster asset for a local project.
  image-workbench: Codex-only; generate/edit requires Codex image generation
  and local image viewing.
- Installed-payload separation. Only `skills/` is installed as skill content.
  Deterministic evaluators, the Korean live harness, documentation, migration
  evidence, and release tooling remain outside that payload.
- Provider-free verification through `python3 scripts/verify.py`. The default
  is `--profile full`. Windows portable verification is
  `python3 scripts/verify.py --profile windows-portable`. Required CI does not
  use credentials, models, or remote image calls.
- Opt-in live evaluation boundary.
  Offline fixtures: deterministic contract evidence only.
  Live execution: local, explicit, optional, potentially billable, and never
  required by CI.
- Apache-2.0 license at the repository root (`LICENSE`) and in each standalone
  skill (`LICENSE.txt`). `SKILL.md` declares `license: Apache-2.0`.
- Archive provenance in `NOTICE` and `docs/maintainers/archive-migration.md`.
  Skills were imported from `https://github.com/beyondwin/Archive.git` at
  pinned source commit `76e6bf4ebbc9430aee9a04a5b780ae38330f3021`,
  manifest digest `6917f68e6e0d81226e50195d58a884373d23ffbbbe48363ef2428c8cbcb83f78`.

### Notes

- The catalog is exactly these two skills. A third skill is out of scope for
  this version.
- Offline success does not prove general Korean editing quality, semantic
  equivalence, live image quality, commercial permission, a better provider,
  or cross-runtime parity.
- Local `dist/` archives are not publication proof. Public proof is the
  downloaded GitHub Release bytes. Archive current-tree copies of the two
  skills were removed after that gate in a separate revertible Archive
  commit.
