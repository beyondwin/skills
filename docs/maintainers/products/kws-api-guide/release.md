# kws-api-guide release

The version source is `skills/kws-api-guide/release.toml`. `SKILL.md` `metadata.version` is a
verified copy. The change history is `CHANGELOG.md` in the same directory. The shared
decision table is in [versioning](../../repository/versioning.md).

No kws-api-guide release has been published yet. No tag, publication, or GitHub Release has
been made.

## SemVer examples

- PATCH: a broken reference link, a template style fix, a README install fix
- MINOR: a new optional input or an optional page section
- MAJOR: changing the default scope, the page skeleton or card order, the publish target,
  or adding a required host tool
- No bump: tests or maintainer docs only

## Check, build, download

For the shared commands, see
[`docs/maintainers/repository/release.md`](../../repository/release.md). The product check
is `python3 scripts/release.py check --product kws-api-guide`. The product tag is
`kws-api-guide-v<version>`.

This command does not create a tag or a GitHub Release.
