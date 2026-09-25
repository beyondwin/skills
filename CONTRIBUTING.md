# Contributing

This repository ships five standalone products. Where documents live is in
[docs/README.md](docs/README.md). How the tree is split is in
[architecture](docs/maintainers/repository/architecture.md).

- `korean-writing-editor`
- `image-workbench`
- `how-it-works`
- `pre-sdd-review`
- `sddx`

## Scope

New skills are not accepted by default. A pull request that adds another skill is out of scope unless repository governance is changed first.

The supported OS is macOS only. Windows and Linux are unsupported. An Ubuntu CI pass is not OS support evidence.

Host support:

- `how-it-works` and `sddx` currently claim Codex and Claude Code only.
- Do not broaden host support for `korean-writing-editor` or `pre-sdd-review`.
- `image-workbench` claims Codex and Grok only after a recorded smoke on the current build.

Host-support changes must update `products.toml`, the matching docs, and tests together.

## What we accept

Focused fixes for the current standalone products only:

- behavior defects
- documentation corrections
- security fixes
- measured compatibility evidence
- synthetic, non-personal regression fixtures

Live provider results are not enough on their own. Include a reproducible case, runtime identity, consent-safe artifacts, and a passing offline check.

## Requirements

- Contributions are licensed under Apache-2.0 unless explicitly rejected before merge.
- Provide exact reproduction steps.
- Prefer deterministic, provider-free evidence.
- Do not include a private prompt, personal Korean text, a private image, credentials, provider receipts, or generated media.
- Do not add telemetry, a required provider call, or a new skill.

## Verification

Required local verification is credential-free and provider-free:

```bash
python3 scripts/verify.py
```

- After a product edit, run `python3 scripts/verify.py --skill <name>` first.
- Before merge, run `python3 scripts/verify.py`.
- Run live `--execute` only when that product's runtime or execution contract changed, on macOS, and only with explicit approval.

CI runs only `python scripts/verify.py --profile full`. It does not use secrets, live `--execute`/`--preflight`, a provider CLI, or a remote image call. An Ubuntu CI pass is not macOS support evidence.

See [SECURITY.md](SECURITY.md) for private vulnerability reporting and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.
