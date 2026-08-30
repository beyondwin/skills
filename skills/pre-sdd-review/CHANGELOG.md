# Changelog

All notable changes to this product are documented in this file.

## Unreleased

No unreleased behavior change is recorded.

## 1.2.0 - 2026-08-30

### Added

- The optional local `pre-sdd-review-evidence` CLI records provider-neutral,
  content-bounded review and outcome receipts. Recording is non-blocking and
  never changes a review verdict.

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
