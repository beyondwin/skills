# Verification

[한국어](../ko/verification.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md)

The required check needs no credentials and calls no model. A pass means the repo still follows its own rules. It does not mean a model edits well or that images look good.

Terms: a fixture is a saved test example. A smoke is a recorded live run. `not_measured` means not checked in this environment yet. `current-bounded` means only the version and hash are tied to the record.

```bash
python3 scripts/verify.py
```

With no arguments it runs every stage in this order and stops at the first failure:

- repository-contract
- korean-package
- korean-offline
- korean-live-unit
- korean-live-dry-run
- image-contract
- image-inspector
- how-it-works-contract
- pre-sdd-review-contract
- pre-sdd-review-evidence
- sddx-contract
- waygent-contract
- python-compile

CI runs this verification on Ubuntu. An Ubuntu CI pass does not prove macOS support.

To check one skill, pass its name. This runs `product-contract`, that skill's own stages, and `python-compile`. Any of the six names works, for example:

```bash
python3 scripts/verify.py --skill pre-sdd-review
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py --skill waygent
```

Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`how-it-works`](../../../skills/how-it-works/README.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.md), [`sddx`](../../../skills/sddx/README.md), [`waygent`](../../../skills/waygent/README.md).

## Shared evidence sentences

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## Offline fixtures

Offline tests prove the fixed contract only. Each product's fixture paths are in its maintainer `testing.md`.

- Korean Writing Editor: 33 offline cases (`normative=10 preservation=8 noop=6 voice=4 trigger=5`). New live evidence uses runner 18; older runner receipts are rejected.
- Image Workbench: 32 fixtures and 17 mutations (deliberately broken variants).
- Korean candidates: any hard failure makes the result `failed`. If hard checks pass but meaning, attribution, or the requested edit was not observed, the result is `partially_verified`. An offline pass alone is never a live status.
- How It Works: fence/hop validity, loading, syntax, and meaning each need their own evidence. Matching metadata alone proves no model run.

`pre-sdd-review` provider-free fixtures validate only instruction and package contracts. They do not prove reviewer independence, semantic completeness, or live review quality.

The `pre-sdd-review-evidence` stage tests `evidence.py` under `tests/products/pre-sdd-review/evidence/`. It makes no network, model, provider, or telemetry call.

The Pre-SDD recorder reads and writes schema 4 only, and commands that change records need its checkout binding. Records in schema 2 and schema 3, written by recorders before 6.0.0, fail every command with `schema-unsupported`; `summary` counts them in `unsupported_records`. They never block a new run; delete them to clear them. `--version` prints one canonical JSON line containing `"schema":4,"skill_name":"pre-sdd-review"`, then one LF, and creates no evidence home. The exact bytes are in the [recorder README](../../../skills/pre-sdd-review/evidence/README.md).

A pass does not prove general quality.

## Live execution

Live runs are local only. Each needs an explicit flag, a named runtime, a capped call budget, and an evidence folder outside tracked source. CI never needs them, and a provider is never swapped in silently.

Korean live coverage is 14 cases / 17 repeats. Its call caps are the 119 / 3 / 122 / 38 / 160 budgets in the maintainer protocol. Operator steps are in `tests/products/korean-writing-editor/live/README.md`.

Status labels:

- `verified`: confirmed
- `partially_verified`: only part confirmed
- `failed`: failed
- `blocked`: stopped before a run
- `not_measured`: not checked in this environment yet

Never report an offline pass as `partially_verified`, and never report an unavailable provider as a pass. Do not commit user Korean text, provider responses, private reference images, generated images, credentials, or receipts.

## Limits

Report only measured support and fixture results. Do not claim plugin-directory availability, support on every host, general quality, live image quality, settled reuse rights, or a better provider.
