# Product release

This is how to check one product, build its ZIP, and verify the downloaded file after
publishing. Current version numbers are not written here.

- Version source: `skills/<name>/release.toml`
- SemVer rules: [versioning](versioning.md)
- Product examples: `docs/maintainers/products/<name>/release.md`

## Check, build, verify download

Run on a clean tracked tree.

```bash
python3 scripts/verify.py --skill <name>
python3 scripts/release.py check --product <name>
python3 scripts/release.py build --product <name> --output <new-empty-directory>
python3 scripts/release.py verify-download --product <name> --input <fresh-download-directory>
```

- `check` confirms a clean tracked tree, SemVer, CHANGELOG, no tag collision, product
  scope, and required checks. The version baseline is the latest `<name>-v<version>`
  tag.
- `build` writes only to a new empty output directory and makes one standalone ZIP
  and `SHA256SUMS`.
- `verify-download` checks the freshly downloaded bytes: checksum, ZIP structure, the
  hash of the extracted payload, product checks, and an install smoke.

Download check order: checksum → archive checks → extract → metadata → trusted source
hash → smoke. A checksum alone is not authentication. Bind the extracted payload to
the trusted source payload hash before running the smoke.

## Tags and publishing

- Local `dist/` is not publication evidence.
- A product tag is an annotated `<name>-v<version>` tag. Never reuse or move an
  existing tag.
- Tags and GitHub Releases are an explicit release task, never a side effect of a
  local build.

## Failure recovery

- Local check fails: fix the files, version, CHANGELOG, or tests, then check again.
- Packaging fails: build again into a new output directory. Do not reuse partial
  output.
- Draft (unpublished GitHub Release) fails after tagging: do not move the tag. Fix and
  verify only the exact artifacts from the same commit, or prepare a new version if
  code must change.
- Remote check fails: keep the Draft unpublished. Local success is not publication
  evidence.
- One product fails: do not change other products' versions, tags, or Releases.
