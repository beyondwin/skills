# korean-writing-editor release

The version source is `skills/korean-writing-editor/release.toml`. The
`metadata.version` in `SKILL.md` is a checked copy. The user-facing history is
`CHANGELOG.md` in the same directory. The shared decision table is in
[Versioning](../../repository/versioning.md).

## Version rules

Bump the SemVer version when behavior changes. Do not bump when only doc
wording changes and behavior stays the same. Changes to the live harness (the
tool that evaluates with real model calls) or to dated reports alone do not
bump the skill version.

- PATCH: fixing a broken relative link, correcting an installed README, or a
  defect fix that restores the documented `correct` branch
- MINOR: a new optional argument that keeps `polish` as the default
- MAJOR: changing the default mode to `diagnose`, or implicitly activating a
  near-miss (a similar, out-of-scope request) that used to do nothing
- None: live-harness-only changes, dated-report format changes, and maintainer
  docs that are not installed

When installed files change, the version decision in `release.toml` and
`SKILL.md` and the product CHANGELOG entry must be in the same change.

## Release evidence

Release evidence must include all of:

- runner 18 product verification
- the thirty-three offline cases (`normative=10 preservation=8 noop=6 voice=4 trigger=5`)
- a README relative-link check on a copied or unpacked standalone payload

A pass on the repository source payload does not replace ZIP verification.
`release.toml` sets the current standalone version. Local preparation alone
does not publish a new GitHub tag or Release.

## Check, build, download

For the shared check / build / verify-download commands, see
[`docs/maintainers/repository/release.md`](../../repository/release.md).
The product check is `python3 scripts/release.py check --product korean-writing-editor`.

The product tag is `korean-writing-editor-v<version>`.

## Recovering from failure

- Local verification fails: fix the files, version, CHANGELOG, or tests, then
  verify again.
- Packaging fails: rebuild into a fresh output directory. Do not reuse partial
  output.
- Draft fails after tagging: do not move the tag. Fix and verify only the exact
  artifact from the same commit, or prepare a new version if code must change.
- Remote verification fails: keep the Draft private. Local success does not
  stand in for public evidence.
- This product fails: do not change another product's version, tag, or Release.
