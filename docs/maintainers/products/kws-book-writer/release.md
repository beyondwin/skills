# kws-book-writer release

The version source is `skills/kws-book-writer/release.toml`. `SKILL.md`
`metadata.version` is a verified copy. The change history is `CHANGELOG.md` in the same
directory. The shared decision table is in [versioning](../../repository/versioning.md).

No kws-book-writer release has been published yet. No tag, publication, or GitHub
Release has been made.

## SemVer examples

- PATCH: a broken reference link, a report-only check fix, a README install fix
- MINOR: a new optional phase or report-only check, or an optional output format such as
  EPUB
- MAJOR: changing the workspace layout, the phase order, a hard-fail check, or the
  `book.json` schema, or adding a required host tool
- No bump: tests or maintainer docs only

## Check, build, download

For the shared commands, see
[`docs/maintainers/repository/release.md`](../../repository/release.md). The product check
is `python3 scripts/release.py check --product kws-book-writer`. The product tag is
`kws-book-writer-v<version>`.

This command does not create a tag or a GitHub Release.
