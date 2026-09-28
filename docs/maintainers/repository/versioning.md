# Versioning

Bump the version when a rule users can see changes. Do not bump it when only tests or
maintainer docs change, since they are not installed. The table below decides whether
to bump and by how much.

When you bump a product version, change these together in one change:

- `skills/<name>/release.toml`: the version source.
- `SKILL.md` `metadata.version`: the copy installers read. CI requires both to change
  together; no tool syncs them for you.
- The `Unreleased` entry in `skills/<name>/CHANGELOG.md`.

During development, `release.toml` `version` is the next release target. If the
payload differs from the last published product tag but the version is unchanged, the
check fails. When preparing a release, turn `Unreleased` into `## <version> - <date>`
and open a new empty `Unreleased` section.

## Skill SemVer

Judge SemVer by the effect on product rules users can see, not by how many files
changed.

| Change | Skill version | Example |
| --- | --- | --- |
| Compatible fix that restores a documented rule | PATCH | Wrong branch, broken relative link, transparent security hardening |
| Change to installed README, CHANGELOG, or package info | PATCH | Install fix, added release provenance |
| Opt-in feature that keeps default behavior | MINOR | New optional mode, argument, or script |
| Breaking change to activation or near-miss bounds | MAJOR | Implicit activation of a request that used to be a no-op |
| Change to default mode, default output, or required input | MAJOR | New default path, output format removed or renamed |
| Change to the required runtime, safety, or data-handling contract | MAJOR | New required provider, new data retention policy |
| Only uninstalled tests, maintainer docs, or CI change | None | Test refactor, internal wording cleanup |

Changes to `SKILL.md`, `agents/openai.yaml`, runtime `references/`, or `scripts/` are
never assumed to be wording-only. They can change agent behavior, so they need a
contract impact review and at least a PATCH. If only maintainer docs or repository
tools change and the shipped product is identical, do not bump the skill version.

## Tags

- Product tag: an annotated `<name>-v<version>` tag. Never reuse or move an existing
  tag.
