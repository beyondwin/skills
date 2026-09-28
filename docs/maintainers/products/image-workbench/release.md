# image-workbench release

The version source is `skills/image-workbench/release.toml`. `SKILL.md`
`metadata.version` is a checked copy. The human-readable history is
`CHANGELOG.md` in the same folder. Follow the shared rules in
[Versioning](../../repository/versioning.md).

`release.toml` sets the current version. A passing local check does not show
that a tag, a push, or a GitHub Release is done.

## SemVer examples

- PATCH: a fixed inspector path hint, a broken relative link, or a fix that
  restores a documented authorization boundary
- MINOR: a new optional script that keeps the default `brief`/`audit`
  read-only
- MAJOR: making generation the default mode, or letting `brief` authorize an
  image call
- None: a test refactor that is not installed, or a provider source update
  that keeps the adopt/reject boundary and behavior

Bump SemVer when behavior changes. Do not bump when only doc wording changes
and behavior stays the same, or for a provider source update that keeps the
adopt/reject boundary and behavior.

When installed files change, the same change must include a version decision
in `release.toml` and `SKILL.md` and a product CHANGELOG entry.

## Check, build, and download

The shared check / build / verify-download commands are in
[`docs/maintainers/repository/release.md`](../../repository/release.md). The
product check is `python3 scripts/release.py check --product image-workbench`.

The extracted-payload smoke must call the extracted inspector from the skill
root. The shared release code that verifies checksums and compares against a
locally trusted source payload hash is owned by the integration owner. A change
to product docs alone is not evidence that the shared contract is implemented.

The product tag is `image-workbench-v<version>`.

## Failure recovery

- Local verification fails: fix the files, version, CHANGELOG, or tests and
  verify again.
- Packaging fails: rebuild into a fresh output folder. Do not reuse partial
  output.
- Draft fails after tagging: do not move the tag. Fix and verify only the exact
  artifacts from the same commit, or prepare a new version if code must change.
- Remote verification fails: keep the Draft private. Do not use a local
  success as public evidence.
- This product fails: do not change another product's version, tag, or
  Release.
