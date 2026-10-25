# grok-video release

The version source is `skills/grok-video/release.toml`. `SKILL.md`
`metadata.version` is a checked copy. The human-readable history is
`CHANGELOG.md` in the same folder. Follow
[Versioning](../../repository/versioning.md).

`release.toml` sets the current version. A passing local check does not show
that a tag, a push, or a GitHub Release is done.

## SemVer examples

- PATCH: a planner fix that restores a documented pin or question
- MINOR: a new optional field that keeps the default 6 second 720p travel shot
- MAJOR: changing the default pin, the default duration, or which requests activate the skill
- None: a test or maintainer-doc edit that does not ship

When installed files change, the same change must include `release.toml`,
`SKILL.md` `metadata.version`, and a `CHANGELOG.md` entry.

## Check

`python3 scripts/release.py check --product grok-video`

The product tag is `grok-video-v<version>`.

## Failure recovery

- Local verification fails: fix the files and verify again.
- This product fails: do not change another product's version, tag, or Release.
- Do not move an existing tag.
