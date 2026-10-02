# how-it-works release

This document sets when to bump how-it-works' version and how to check a release. The
version source is `skills/how-it-works/release.toml`. `SKILL.md` `metadata.version` is
a verified copy. The human-readable change history is `CHANGELOG.md` in the same
directory. The shared decision table is in [versioning](../../repository/versioning.md).

No how-it-works release has been published yet. `release.toml` owns the current
standalone version. No tag, publication, or GitHub Release has been made.

## SemVer examples

- PATCH: a broken relative link, an install README fix, a defect fix that restores a
  documented rule
- MINOR: a new optional alias that keeps the default picture rung
- MAJOR: dropping the numbered hop list from the required output, requiring a host
  tool, activating on `/eli5`, or changing the default rung
- No bump: fixture comments that are not installed, or maintainer-doc-only changes

3.0.0 was a MAJOR: it made picture the default rung and removed the depth question.
3.0.1 is a PATCH: English-first docs and English instruction text, same behavior.
3.0.2 is a PATCH: the reply skeleton is inlined in `SKILL.md`, references are read
whenever the host can, and the rung rules contradicting each other are aligned.
3.0.3 is a PATCH: a requested analogy follows the mapped-analogy rule `output.md`
already documented instead of being refused, and `SKILL.md` drops restated rules.

Rules:

- Bump SemVer when behavior changes. Don't bump for wording-only changes outside the
  installed files.
- When installed files change, the `release.toml` and `SKILL.md` versions and the
  product CHANGELOG entry must be in the same change.

## Check, build, download

For the shared check / build / verify-download commands, see
[`docs/maintainers/repository/release.md`](../../repository/release.md). The product
check is `python3 scripts/release.py check --product how-it-works`.

The product tag is `how-it-works-v<version>`. Tags and drafts are explicit release
work, never a side effect of a local build.

## Recovering from failure

- Local verification fails: fix the files, version, CHANGELOG, or tests, then verify
  again.
- Packaging fails: rebuild into a fresh output directory. Don't reuse partial output.
- The draft fails after tagging: don't move the tag. Fix and verify only the exact
  artifact from the same commit, or prepare a new version if code must change.
- Remote verification fails: keep the draft private. A local pass is not public
  evidence.
- This product fails: don't change another product's version, tag, or Release.

This command does not create a tag or a GitHub Release.
