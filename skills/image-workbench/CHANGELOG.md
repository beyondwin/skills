# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 2.0.2 - 2026-09-08

Local release preparation only. No new GitHub tag or GitHub Release
has been published for this version.

### Fixed

- The inspector rejects output paths that alias the input asset, including
  symlinks and hard links, before writing. Existing unrelated JSON reports
  can still be updated.

### Added

- Independent product `release.toml` and this changelog. The next standalone
  target is `2.0.2`.

### Changed

- Product README language was simplified with no behaviour change.

### Notes

- This section does not claim a new GitHub tag or GitHub Release.

## 2.0.0 - 2026-08-27

Public legacy standalone asset `image-workbench-v2.0.0.zip` published
under the integrated repository tag `v2.0.0` at
https://github.com/beyondwin/skills/releases/tag/v2.0.0.
No product-qualified tag `image-workbench-v2.0.0` exists.

### Added

- Project-bound raster planning, generation, edit, comparison, and audit.
  image-workbench: Codex-only; generate/edit requires Codex image generation
  and local image viewing.
- Apache-2.0 `LICENSE.txt` and `SKILL.md` license declaration.

### Notes

- Offline fixtures do not prove live image quality, commercial permission, or
  a better provider.
