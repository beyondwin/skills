# pre-sdd-review release

This document owns the independent packaging procedure for Pre-SDD Review.
The version source is `skills/pre-sdd-review/release.toml`; `SKILL.md`
`metadata.version` is its verified copy, and `CHANGELOG.md` records the
human-readable contract history.

## Check, build, and verify download

Run the provider-free product verification, then package into a new empty
directory and validate bytes from a fresh download directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
python3 scripts/release.py check --product pre-sdd-review
python3 scripts/release.py build --product pre-sdd-review --output <new-empty-directory>
python3 scripts/release.py verify-download --product pre-sdd-review --input <fresh-download-directory>
```

`check` validates the tracked product scope, SemVer, changelog, and required
verification. `build` writes one standalone ZIP and `SHA256SUMS` only to the
new empty output directory. `verify-download` validates the fresh bytes,
checksum, ZIP structure, extracted payload hash, and product verification.
Local build output is not public-release evidence.

No tag or GitHub Release is created by these commands.

## Failure recovery

Correct the product files, version decision, changelog, or tests and repeat
the failed command. Rebuild only in a new empty directory; do not reuse partial
artifacts. Tagging and publishing are separate, explicit release operations
and are outside this procedure.
