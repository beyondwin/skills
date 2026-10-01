# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 2.1.1 - 2026-10-01

### Changed

- User-facing install and support wording uses ordinary terms. Codex and
  Grok install links are labeled separately.
- README wording is shorter and uses plain terms. Behavior is unchanged.
- Docs are English-first: `README.md` is English and `README.ko.md` is the
  Korean user guide. `README.en.md` is removed. Behavior is unchanged.

### Fixed

- The inspector runs on the stock macOS `/usr/bin/python3` (3.9). It used to crash with a traceback before printing any JSON, so every project handoff held.
- `--output` no longer overwrites an image or any other non-JSON file. An existing target must be a regular JSON report (a symlink to one is updated in place). The report is written atomically, and a failure names the output path in a new `output` key.
- A 4096x4096 RGBA PNG is inspected instead of being rejected by an undocumented 64 MiB cap. PNG image data is decoded in 1 MiB slices up to 512 MiB in total.
- A PNG, JPEG, or WebP file with extra bytes after its end marker (for example a camera trailer) is accepted, and the count is reported as `trailing_bytes`. It used to fail with a misleading "missing JPEG scan or EOI" or "invalid PNG IEND chunk".
- Lossless WebP (VP8L) reports alpha from its `alpha_is_used` bit instead of `null`.
- SVG-only, chart, UI, and logo-in-icon requests are non-activations, as the description always said. "Route The Deliverable" covers only a project raster request that turns out to need a native path.
- The rule and rubric no longer promise a "path readiness" fact the inspector never printed; confirm the destination path separately.

### Changed

- The description puts the use line and the exclusions in its first 250 or so characters, so Codex and Grok listings show them. The activation bounds are the same. The procedure summary and the relation to Codex's bundled `imagegen` skill (same built-in `image_gen` path, never its CLI fallback) are now in the body. `agents/openai.yaml` lists generate and edit.
- The host table names `image_gen` for Codex generate and edit. The copy-before-inspect rule names both hosts' result folders (Grok session `images/`, Codex `$CODEX_HOME/generated_images/`). The aspect-ratio, n/count, and video-tool lines say they apply on Grok.
- New Grok limits note: Grok image tools return JPEG without alpha, and Grok edit downscales references to about 768 px. Keep the `.jpg` extension; when acceptance needs transparency, PNG, or exact pixels, hold or apply an explicit, reported conversion. A Grok `[Image #N]` attachment has no local path; ask for a project file or hold.
- The inspector is called as `python3 <skill-root>/scripts/inspect_asset.py <absolute-asset-path>`, with any `--output` report outside the skill folder, so reports no longer land inside the installed skill.
- The former `kws-` name is no longer guarded; the matching offline case is replaced by a prompt-gallery near-miss.
- Both READMEs say that the `~/.agents/skills` link is read by Codex and Grok, so a user of both hosts installs only one copy, and list a data chart among the non-uses.

### Added

- Inspector output adds `extension_matches` (file suffix fits the detected format; `.jpg`/`.jpeg` count as JPEG) and `trailing_bytes`. Existing keys are unchanged.

## 2.1.0 - 2026-09-12

### Changed

- Host-native generate/edit table for Codex bundled tools and Grok
  `image_gen`/`image_edit`.
- A host session preview path is not a project-bound final file; copy into a
  project sibling before inspection, then report that project path.
- Grok generate/edit does not call `image_to_video` or `reference_to_video`.
  Single-image edit keeps the source aspect ratio unless a ratio change is
  explicit.

### Notes

- Grok is a supported host after recorded smoke on this build. Offline tests
  bind that claim to four `pass` values and the current `SKILL.md` hash. No
  GitHub tag or GitHub Release is created.

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
