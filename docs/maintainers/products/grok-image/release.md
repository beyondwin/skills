# grok-image release

The version source is `skills/grok-image/release.toml`. `SKILL.md` `metadata.version` is a verified copy. The change history is `CHANGELOG.md`. The shared decision table is in [versioning](../../repository/versioning.md).

No grok-image release has been published yet. No tag, publication, or GitHub Release has been made.

## SemVer examples

- PATCH: a broken relative link, an install README fix, a defect fix that restores a documented rule
- MINOR: an optional extra ratio note that keeps the default photograph at `3:2`
- MAJOR: asking a questionnaire before every still, or dropping the single-repair stop
- No bump: maintainer-doc-only changes

1.0.0 is the first installed behavior.

## Check, build, download

The product check is `python3 scripts/release.py check --product grok-image`. Shared commands are in [release](../../repository/release.md).

The product tag is `grok-image-v<version>`. Tags and drafts are explicit release work.

## Recovering from failure

- Local verification fails: fix the files, version, CHANGELOG, or tests, then verify again.
- Packaging fails: rebuild into a fresh output directory.
- The draft fails after tagging: do not move the tag.
- This product fails: do not change another product's version, tag, or Release.

This command does not create a tag or a GitHub Release.
