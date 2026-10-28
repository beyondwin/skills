# Verification

[한국어](../ko/verification.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md)

The required check needs no credentials and calls no model. A pass means the repo still follows its own rules. It does not establish a model’s editing or explanation quality.

Repository tools require Python 3.11 or newer; the standard-library `tomllib` module is required.
This is a development requirement, separate from installed skill use.

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
- how-it-works-contract
- python-compile

CI runs this verification on Ubuntu. An Ubuntu CI pass does not prove macOS support.

To check one skill, pass its name. This runs `product-contract`, that skill's own stages, and `python-compile`. Either product name works, for example:

```bash
python3 scripts/verify.py --skill how-it-works
```

Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`how-it-works`](../../../skills/how-it-works/README.md).

## Shared evidence sentences

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## Offline fixtures

Offline tests prove the fixed contract only. Each product's fixture paths are in its maintainer `testing.md`.

- Korean Writing Editor: 37 offline cases (`normative=10 preservation=9 noop=7 voice=4 trigger=7`). New live evidence uses runner 18; older runner receipts are rejected.
- Korean candidates: any hard failure makes the result `failed`. If hard checks pass but meaning, attribution, or the requested edit was not observed, the result is `partially_verified`. An offline pass alone is never a live status.
- How It Works: fence/hop validity, loading, syntax, and meaning each need their own evidence. Matching metadata alone proves no model run.

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

Never report an offline pass as `partially_verified`, and never report an unavailable provider as a pass. Do not commit user Korean text, provider responses, credentials, or receipts.

## Limits

Report only measured support and fixture results. Do not claim plugin-directory availability, support on every host, general quality, settled reuse rights, or a better provider.
