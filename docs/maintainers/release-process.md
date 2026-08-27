# Release process

The last published catalog identity is `beyondwin-skills` `2.0.0`. Plugin metadata lives under `catalog/plugin/.codex-plugin/plugin.json`, not at the repository root. Each skill product keeps its own `release.toml` and `SKILL.md` metadata version. A skill version changes only when that skill's contract or runtime payload changes; the catalog version changes only when the adopted lock or packaged catalog bundle changes. Root documentation-only changes do not require a new catalog release.

Do not claim a GitHub release exists until remote publication is verified.
`v2.0.0` is published at https://github.com/beyondwin/skills/releases/tag/v2.0.0.
That does not claim a plugin-directory listing. Provenance is in
[archive-migration.md](archive-migration.md). Future releases follow the same
remote-download gate. Archive current-tree copies of the two skills were
removed after the `v2.0.0` gate in a separate revertible Archive commit.

## Local gates

Run from a clean tracked tree:

```bash
python3 scripts/verify.py
git status --short --branch --untracked-files=all
git diff --check
```

The source tree must be clean. Generated evidence, caches, and `dist/` stay untracked.

The first catalog release produced:

```text
beyondwin-skills-v2.0.0.zip
korean-writing-editor-v2.0.0.zip
image-workbench-v2.0.0.zip
SHA256SUMS
```

`catalog/catalog.lock.json` pins those two standalone skill ZIPs as `legacy-bundle` inputs at tag `v2.0.0`. Current `skills/` development, including unpublished `graspic`, is not copied into a catalog ZIP. Only released plugin ZIPs are supported catalog artifacts. The shared-version bundle builder is retired; independent product packaging lands with the later release pipeline.

Catalog plugin metadata is sourced from `catalog/plugin/.codex-plugin/plugin.json` and copied to ZIP-root `.codex-plugin/plugin.json` at catalog release time. Each standalone zip contains one top-level skill directory with `LICENSE.txt`. Tests, live harness, docs, caches, and evidence are not members of the purpose-built skill zips.

## Archive, extraction, and checksum

Published `v2.0.0` archives used tracked regular files, sorted zip members, rejected
symlinks and special files, stamped every member at `1980-01-01T00:00:00`, and used
mode `0644` for regular files and `0755` for executable scripts. The shared-version
command `python3 scripts/build_release.py --version 2.0.0 --output dist` is retired
and fails closed.

Verify the last catalog from a fresh download of the published standalone ZIPs plus
`SHA256SUMS`, not from current `skills/`:

```bash
(cd "$RELEASE_DOWNLOAD_DIR" && shasum -a 256 -c SHA256SUMS)
```

Reject absolute paths, `..`, duplicates, case-fold collisions, and unexpected
members before extraction. `SHA256SUMS` lists the published release zip files.
After checksums pass, extract every archive into a fresh temporary directory and
run installation smokes against the extracted Korean and image payloads, including
the extracted inspector.

## Remote download

Local `dist/` is not publication proof. For published `v2.0.0`:

1. Download the remote artifacts into a fresh directory rather than reusing local build output.
2. Verify checksums against the downloaded bytes.
3. Run fresh extraction and installation smokes from those bytes.
4. Confirm public README links and source skill URLs resolve.

Do not treat `scripts/build_release.py --verify-download` as a working catalog verifier; that wrapper is retired.

## Archive deletion gate

Do not mutate Archive until all of the following hold:

- public `beyondwin/skills` `main` resolves to the reviewed commit
- tag `v2.0.0` resolves to that commit
- all required CI jobs are green
- all four release artifacts are publicly downloadable
- release checksums match freshly downloaded bytes
- plugin and individual-skill installation smokes pass
- the source-to-import manifest is accounted for
- Archive source commit and migration provenance are recorded
- personal paths, secrets, private fixtures, and unintended artifacts are absent
- no unsupported compatibility or quality claim is present

Any missing condition blocks deletion. After a local Archive removal commit but before push, do not publish it; repair or revert it non-destructively. After push, use `git revert` on the exact removal commit.
