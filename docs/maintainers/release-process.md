# Release process

The plugin bundle and repository release start at `2.0.0`. Each `SKILL.md` keeps its own metadata version. A skill version changes only when that skill's contract or runtime payload changes; the plugin version changes whenever the packaged bundle changes. Root documentation-only changes do not require a new release.

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

The first release produces:

```text
beyondwin-skills-v2.0.0.zip
korean-writing-editor-v2.0.0.zip
image-workbench-v2.0.0.zip
SHA256SUMS
```

Build archives in a temporary directory from tracked files. The plugin zip contains `.codex-plugin/plugin.json`, both complete `skills/` payloads, `LICENSE`, and `NOTICE`. Each standalone zip contains one top-level skill directory with `LICENSE.txt`. Tests, live harness, docs, caches, and evidence are not members of the purpose-built skill zips.

## Archive, extraction, and checksum

After the provider-free verifier passes on a clean tree:

```bash
python3 scripts/build_release.py --version 2.0.0 --output dist
(cd dist && shasum -a 256 -c SHA256SUMS)
```

The builder reads only tracked source files, sorts zip members, rejects symlinks and special files, stamps every member at `1980-01-01T00:00:00`, and uses mode `0644` for regular files and `0755` for executable scripts. It then:

1. Validates archive membership (no tests, no maintainer eval runners, no unexpected members).
2. Extracts every archive into a fresh temporary directory.
3. Runs installation smokes against the extracted content, including Korean and image deterministic evaluators and the extracted inspector.
4. Computes `SHA256SUMS` only after those checks pass.

Reject absolute paths, `..`, duplicates, case-fold collisions, and unexpected members before extraction. `SHA256SUMS` lists exactly the three zip files.

## Remote download

Local `dist/` is not publication proof. After tagging `v2.0.0` and publishing the four artifacts:

1. Download the remote artifacts into a fresh directory rather than reusing local build output.
2. Verify checksums against the downloaded bytes.
3. Run fresh extraction and installation smokes from those bytes:

   ```bash
   python3 scripts/build_release.py --verify-download "$RELEASE_DOWNLOAD_DIR" --version 2.0.0
   ```

4. Confirm public README links and source skill URLs resolve.

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
