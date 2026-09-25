# Verification

[한국어](../ko/verification.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md)

Required verification runs without credentials or models. A pass means the repo rules match today. It does not mean a model edits well or that images look good.

In short: a fixture is a saved test example. A smoke is a recorded live run. `not_measured` means not checked in this environment yet. `historical-unbound` is an old record, not current execution evidence. `current-bounded` means only version and hash are bound.

```bash
python3 scripts/verify.py
```

With no arguments it runs every stage. Stages run in this order. The first failing stage stops the command.

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
- python-compile

CI runs this verification on Ubuntu. An Ubuntu CI pass does not prove macOS support.

Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), [`how-it-works`](../../../skills/how-it-works/README.en.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.en.md), [`sddx`](../../../skills/sddx/README.en.md).

To verify only `pre-sdd-review` or `sddx`, run:

```bash
python3 scripts/verify.py --skill pre-sdd-review
python3 scripts/verify.py --skill sddx
```

## Shared evidence sentences

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## Offline fixtures

The offline suites prove the deterministic contract only. Product fixture paths live in each product maintainer `testing.md`.

Current Korean offline coverage is 34 cases (`normative=10 preservation=8 noop=6 voice=4 trigger=6`). New Korean live evidence uses runner 18; historical runner receipts do not prove a runner 18 execution. Image coverage is 32 fixtures and 17 mutations.

For Korean candidates, hard failures take precedence as `failed`. After hard checks pass, unobserved meaning, attribution, or requested edit execution yields `partially_verified`; offline contract success alone is not a live status. For How It Works, fence/hop validity, loading, syntax, and meaning require separate evidence. The historical smoke remains `historical-unbound`; current metadata binding alone proves no model execution.

`pre-sdd-review` provider-free fixtures validate only instruction and package contracts. They do not prove reviewer independence, semantic completeness, or live review quality.

The evidence stage under `tests/products/pre-sdd-review/evidence/` checks `evidence.py`. It makes no network, model, provider, or telemetry call.

The Pre-SDD recorder reads and writes schema 4 only, and mutation commands require its checkout binding. Records in schema 2 and schema 3, written by recorders before 6.0.0, fail every command with `schema-unsupported`; `summary` counts them in `unsupported_records`. They never block a new run; delete them to clear them. `--version` emits one canonical JSON line containing `"schema":4,"skill_name":"pre-sdd-review"`, followed by one LF, and creates no evidence home. The exact bytes are in the [recorder README](../../../skills/pre-sdd-review/evidence/README.md).

A pass does not prove general quality. The license is Apache-2.0.

## Live execution

Korean live coverage remains 14 cases / 17 repeats.

Live evaluation is local only. It needs a positive flag, a named runtime, a bounded call budget, and an evidence root outside tracked source. CI never requires it. Provider processes are never silently substituted.

Status labels mean:

- `verified`: confirmed
- `partially_verified`: only part confirmed
- `failed`: failed
- `blocked`: stopped before a run
- `not_measured`: not checked in this environment yet

Status labels are `verified`, `partially_verified`, `failed`, `blocked`, and `not_measured`. Do not turn an offline pass into `partially_verified`. Do not turn an unavailable provider into a pass.

Korean live ceilings follow the 119 / 3 / 122 / 38 / 160 budgets in the maintainer protocol. Operator steps are in `tests/products/korean-writing-editor/live/README.md`. Do not commit user Korean text, provider responses, private reference images, generated images, credentials, or receipts.

## Limitations

Report measured support and fixture results only. Do not claim plugin-directory availability, support on every host, general quality, live image quality, settled reuse rights, or a better provider.
