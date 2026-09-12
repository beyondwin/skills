# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 3.0.0 - 2026-09-12

### Breaking

- Default rung is 그림. A missing depth is filled by precedence, announced
  in the intent line, and explained in the same turn. The old last step
  `one necessary question` is removed.
- Picture Map prints numbered hops before Mermaid source. Body at 그림
  does not walk the hops again.

### Changed

- `감이 안 와` is a silent 그림 alias. Type word `흐름` still does not fill
  rung. Jargon without a depth alias remains 뼈대.
- First-call README examples use `$how-it-works DNS` / `/how-it-works DNS`.
  Explicit `DNS 길` remains a path example.

### Notes

- Live model quality stays `not_measured`. Fixture pass is not host
  execution evidence. No GitHub tag or GitHub Release is created.

## 2.0.1 - 2026-09-11

### Changed

- Standalone README now uses the shared heading set and points install procedures at the split user guides.

### Notes

- No GitHub tag or GitHub Release is created.

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
