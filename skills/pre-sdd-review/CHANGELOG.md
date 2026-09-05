# Changelog

All notable changes to this product are documented in this file.

## Unreleased

### Changed

- Product README language was simplified with no behaviour change.

## 2.0.0 - 2026-09-05

### Changed

- The evidence recorder is one standard-library script,
  `evidence/evidence.py`, run with `python3` from the loaded skill root. The
  `pre-sdd-review-evidence` launcher, installer, and package are removed.
- Records use schema 2: one file per run under `~/.pre-sdd-review/runs/`,
  and six commands `start`, `finish`, `abandon`, `outcome`, `show`, `summary`.
  Schema 1 receipts are not read.
- The controller passes the design path it resolved from `**Spec:**`; the
  recorder no longer parses that field. An unresolved design is recorded as
  null with a `BLOCKED` verdict.
- `finish` rejects a repair pass without a repaired finding. `summary` is
  agent-readable JSON with verdict counts, abandon reasons, per-plan chains,
  repeated finding patterns, outcome coverage, and anomalies, each carrying
  run IDs.
- `outcome` records one label (`good`, `false-ready`, `noisy`, `abandoned`)
  and an optional note, and may be re-recorded.
- Reviewer protocol: a `repo-reality` finding must cite a repository path
  other than the reviewed design or plan.

## 1.3.1 - 2026-09-02

### Changed

- Plans that explicitly name a required implementation base now block before
  reviewer dispatch when that base is unresolved or not an ancestor of the
  current `HEAD`.
- Provider-free coverage now includes the stale implementation-base boundary.

## 1.3.0 - 2026-08-30

### Changed

- Scoped re-review stops at unmapped material findings instead of widening the
  repair or starting another invocation.
- Each invocation uses at most a primary role and one triggered risk role;
  fresh closure agents do not add roles.
- Authority-preserving repairs need no approval. Unresolved product decisions
  are grouped into one checkpoint.
- Reporting now validates each receipt from the same bounded byte snapshot used
  for its size and SHA-256, avoiding repeated reads of one review/outcome pair.
- Source installation ignores only an ordinary `__pycache__` containing regular
  `.pyc` files; unsafe cache entries and runtime-manifest drift still fail.
- User and evidence guides now lead with installation and the basic workflow,
  then separate safety boundaries, operations, measured support, and residual
  limits.

## 1.2.0 - 2026-08-30

### Added

- The optional local `pre-sdd-review-evidence` CLI records provider-neutral,
  content-bounded review and outcome receipts. Recording is non-blocking and
  never changes a review verdict.
- The skill now starts compatible evidence before semantic review, finalizes
  it after the verdict, and hands a controller-local run ID only to an
  explicitly combined SDD flow.
- Product and maintainer guidance now documents explicit launcher install,
  local receipt privacy, immutable outcome limits, heuristic candidates, and
  the native-platform `not_measured` boundary.

## 1.1.0 - 2026-08-29

### Changed

- One invocation reviews exactly one implementation plan. Separate plan-local
  reviews never produce an aggregate `READY`.
- Structural document repairs now record a repair-impact map and receive a
  bounded regression re-review. The two-pass repair limit is unchanged.
- Final `REVISE` and `BLOCKED` reports include an unresolved handoff packet
  and a compact pass receipt. User documents and full model responses are not
  stored.

### Verification

- Added synthetic fixtures for schema-consumer drift, vacuous state
  verification, and conditional edit-surface drift.

## 1.0.0 - 2026-08-29

### Notes

- This is the first independent product release contract for Pre-SDD Review: a
  Codex-only readiness gate with provider-free contract evidence and
  documented maintainer protocols.
- This entry records the release contract only. It does not claim that a tag,
  published package, or GitHub Release exists.
