# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 2.1.0 - 2026-09-12

### Changed

- Host-native generate/edit table for Codex bundled tools and Grok
  `image_gen`/`image_edit`.
- A host session preview path is not a project-bound final file; copy into a
  project sibling before inspection.

### Notes

- Registry `grok` claim is a separate smoke-gated step in the same release
  train. No GitHub tag or GitHub Release is created.

## 2.0.3 - 2026-09-11

### Changed

- Standalone README now uses the shared heading set and points install procedures at the split user guides.

### Notes

- No GitHub tag or GitHub Release is created.

## 2.0.2 - 2026-09-08

Local release preparation only. No new GitHub tag or GitHub Release
has been published for this version.

### Fixed

- The inspector rejects output paths that alias the input asset, including
  symlinks and hard links, before writing. Existing unrelated JSON reports
  can still be updated.
- PNG inspection now checks the IHDR CRC, scanline filter range across
  non-interlaced and Adam7 rows, and required indexed palette structure.
  Existing bounded decompression and file-fact reporting remain in place.
- JPEG inspection rejects malformed first-scan headers and invalid component
  selectors. WebP inspection rejects reserved VP8 versions and nonzero VP8L
  versions while preserving existing alpha reporting.
- Offline evaluation now rejects generation and asset writes in brief,
  audit, and no-op decisions even when candidate and expected values agree
  on the prohibited action.
- Standalone README links to repository documentation use public URLs.
  Inspector documentation now distinguishes selected structural checks
  from complete decoding, visual review, and rights verification.

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
