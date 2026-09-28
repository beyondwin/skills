# waygent release

This document sets when to bump waygent's version and how to check a release. The
version source is `skills/waygent/release.toml`. `SKILL.md` `metadata.version` is a
verified copy. The human-readable change history is `CHANGELOG.md` in the same
directory. The shared decision table is in [versioning](../../repository/versioning.md).

No waygent release has been published yet. No tag, publication, or GitHub Release has
been made.

## SemVer examples

- PATCH: a broken link, a README correction, a defect fix that restores a documented rule
- MINOR: a new optional input that keeps the existing flow
- MAJOR: a change to the trailer format, progress file location, review count, or branch rules
- No bump: a change only to tests or maintainer docs, which are not installed

When installed files change, the `release.toml` and `SKILL.md` versions and the product
CHANGELOG entry must be in the same change.

## Check, build, download

For the shared check / build / verify-download commands, see
[`docs/maintainers/repository/release.md`](../../repository/release.md). The product
check is `python3 scripts/release.py check --product waygent`. The product tag is
`waygent-v<version>`.

This command does not create a tag or a GitHub Release.
