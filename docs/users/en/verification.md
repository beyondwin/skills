# Verification

[한국어](../ko/verification.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md)

Required verification runs without credentials or models.

```bash
python3 scripts/verify.py
```

That command is `--profile full`. Stages run in this order: contract, korean-offline, image-contract, image-inspector, korean-live-unit, korean-live-dry-run, python-compile. The first failing stage stops the command. `windows-portable` excludes the Codex-only `image-contract` and `image-inspector` stages. Live `--execute` is not included.

```bash
python3 scripts/verify.py --profile full
python3 scripts/verify.py --profile windows-portable
```

Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), [`how-it-works`](../../../skills/how-it-works/README.en.md).

## Shared evidence sentences

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## Offline fixtures

The offline suites prove the deterministic contract only.

- `korean-writing-editor`: trigger, mode, preservation, and output fixtures under `tests/products/korean-writing-editor/offline/`
- `image-workbench`: routing, authorization, ImageSpec, handoff, and inspector fixtures under `tests/products/image-workbench/`
- `how-it-works`: synthetic DNS and rebase contract fixtures in `tests/products/how-it-works/cases.json` and payload contracts in `tests/products/how-it-works/test_contract.py`. They lock the in-chat required deliverable (one-sentence claim, Mermaid, numbered hop list, rung-specific body, adjacent slices, one next move).

A pass does not prove general Korean editing quality, semantic equivalence, live image quality, commercial permission, a better provider, or runtime parity. The license is Apache-2.0.

## Live execution

Live evaluation is local only. It needs a positive flag, a named runtime, a bounded call budget, and an evidence root outside tracked source. CI never requires it. Provider processes are never silently substituted.

Status labels are `verified`, `partially_verified`, `failed`, `blocked`, and `not_measured`. Do not turn an offline pass into `partially_verified`, and do not turn an unavailable provider into a pass.

Korean live ceilings follow the 119 / 3 / 122 / 38 / 160 budgets in the maintainer protocol. Operator steps are in `tests/products/korean-writing-editor/live/README.md`. Do not commit user Korean text, provider responses, private reference images, generated images, credentials, or receipts.

## Limitations

Report measured support and fixture results only. Do not claim plugin-directory availability, support on every host, general quality, live image quality, settled reuse rights, or a better provider. An offline `how-it-works` pass does not prove live quality on Codex or Claude Code. Live execution is local, explicit, optional, potentially billable, and never required by CI.
