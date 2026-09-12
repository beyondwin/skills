# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 2.0.4 - 2026-09-12

### Changed

- In `correct` and `polish`, the reply is the edited text. In `diagnose`,
  the first line is the finding. Do not start with “using this skill…”.
- If a phrase is already correct, keep it in `polish` too. If the request
  is not editing (for example translation), do not do that other job in
  the same reply.
- The first README example is a light polish. Typo-only `correct` is the
  second example.

### Notes

- Offline fixtures are now 34 cases (`trigger=6`). Fixture pass still does
  not prove live model quality. This release does not add a recorded host
  smoke or a runner 18 live execute.

## 2.0.3 - 2026-09-11

### Changed

- Standalone README now uses the shared heading set and points install procedures at the split user guides.

### Notes

- No GitHub tag or GitHub Release is created.

## 2.0.2 - 2026-09-08

### Changed

- Clearly required local grammar repairs now apply in both `correct` and
  `polish`; optional readability and local-flow edits remain `polish` only.
- Repository-document links in both standalone READMEs now use absolute GitHub
  paths, while links to files shipped in the payload remain relative.
- Runner 18 distinguishes positive meaning and attribution evidence from
  unmeasured free-form output, detects positive numeric drift in diagnostic
  restatements, and retains bounded execution evidence separately from the
  final response body.
- Historical runner 10 through 17 receipts remain readable, but cannot
  authorize or skip runner 18 execution under the new semantics.

### Notes

- This is local release preparation for standalone target `2.0.2`. No new
  GitHub tag or GitHub Release has been published.

## 2.0.0 - 2026-08-27

Public legacy standalone asset `korean-writing-editor-v2.0.0.zip` published
under the integrated repository tag `v2.0.0` at
https://github.com/beyondwin/skills/releases/tag/v2.0.0.
No product-qualified tag `korean-writing-editor-v2.0.0` exists.

### Added

- Conservative Korean proofreading, correction, and polish of user-supplied
  text. korean-writing-editor: Codex supported; Agent Skills contract
  portable; other hosts only supported after a recorded smoke.
- Apache-2.0 `LICENSE.txt` and `SKILL.md` license declaration.

### Notes

- Offline success does not prove general Korean editing quality or semantic
  equivalence.
