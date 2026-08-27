# Contributing

This repository is a curated catalog of three skills: `korean-writing-editor`, `image-workbench`, and `graspic`. New skills are not accepted by default. A pull request that adds a fourth skill is out of scope unless repository governance is changed first.

## What we accept

Focused fixes for the three existing skills only:

- behavior defects
- documentation corrections
- security fixes
- measured compatibility evidence
- synthetic, non-personal regression fixtures

Live provider results are not sufficient evidence by themselves. Include a reproducible case definition, runtime identity, consent-safe artifacts, and a passing deterministic contract gate.

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

CI runs only `python scripts/verify.py --profile <full|windows-portable>`. It does not use secrets, live `--execute`/`--preflight`, a provider CLI, or a remote image call.

See [SECURITY.md](SECURITY.md) for private vulnerability reporting and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.
