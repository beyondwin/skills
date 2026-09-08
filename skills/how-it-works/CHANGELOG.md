# Changelog

All notable changes to this product are documented in this file.

## Unreleased

No changes yet.

## 2.0.0 - 2026-09-08

### Breaking

- Depth selection now follows explicit rung, explicit depth alias, existing
  jargon default, then one necessary question. Explicit easy aliases override
  jargon. This precedence is a MAJOR behavior change.
- Numeric aliases select a rung only in explicit depth context; numbers such as
  `Raft term 20`, `HTTP/2`, and `5 nodes` remain topic data.
- Required output is complete in chat: one-sentence claim, Mermaid source,
  numbered hop list, rung-specific body, adjacent slices, and one next move.
- Fracture keeps the baseline Mermaid and numbered hops in Map and puts its
  failure/regime table in Body. A host preview is optional and non-fatal.

### Changed

- One-turn hosts emit the complete required deliverable in the current reply
  even if focused references cannot be read this turn.
- Korean and English output stay in the selected language. High-stakes and
  source policy now distinguish verified claims from explicitly unverified
  claims without inventing citations or identifiers.
- Local installation is repeatable for an existing correct link and refuses
  files, directories, different links, dangling links, and targets that appear
  during installation. Links to repository docs now use public repository URLs.
- The preserved schema 1 smoke record is historical evidence only. Its earlier
  host verdicts are not live passing evidence for this version.
- This entry records release metadata and behavior changes. No tag, publication,
  or GitHub Release was created.

## 1.0.0 - 2026-08-28

### Notes

- The unpublished working identity `graspic` was replaced by `how-it-works`
  before first public release. No alias exists. Users install and invoke only
  `how-it-works`. This product was not published as `graspic 2.0.0` and was
  not part of the integrated `v2.0.0` GitHub Release. This section does not
  claim a GitHub tag or GitHub Release.
