# pre-sdd-review release

This document sets how Pre-SDD Review is packaged on its own. The version
source is `skills/pre-sdd-review/release.toml`. `metadata.version` in
`SKILL.md` is a checked copy, and `CHANGELOG.md` is the human-readable contract
history.

## Check, build, download

Run the provider-free product verification, then package into a new empty
directory. Verify the bytes from a separately downloaded directory. The shared
check / build / verify-download commands are in
[`docs/maintainers/repository/release.md`](../../repository/release.md). The
product check is `python3 scripts/release.py check --product pre-sdd-review`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_c*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
```

`check` confirms the tracked product scope, SemVer, changelog, and required
verification. `build` writes only one standalone ZIP and `SHA256SUMS` into a
new empty output directory. `verify-download` checks the freshly downloaded
bytes, checksum, ZIP structure, extracted payload hashes, the exact payload
list, the canonical JSON from the extracted `evidence.py --version`, and the
product verification. A local build is not public release evidence.

`evidence/evidence.py` in the release payload has no executable bit. Run it
with `python3`; do not install it. Windows is not supported.

These commands do not create a tag or a GitHub Release.

## Recovering from a failure

Fix the product files, version decision, changelog, or tests, then rerun the
failed command. Never reuse partial output; rebuild only in a new empty
directory. Tagging and publishing are a separate, explicit release task,
outside this procedure.
