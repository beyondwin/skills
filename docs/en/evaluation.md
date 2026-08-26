# Evaluation

[한국어](../ko/evaluation.md) · [Compatibility](compatibility.md) · [Privacy and rights](privacy-and-rights.md)

Required verification for repository version `2.0.0` runs without credentials or models.

```bash
python3 scripts/verify.py
```

That command is `--profile full`. Stages run in this order: contract, korean-offline, image-contract, image-inspector, korean-live-unit, korean-live-dry-run, python-compile. The first failing stage stops the command. `windows-portable` excludes the Codex-only `image-contract` and `image-inspector` stages. Live `--execute` is not included.

```bash
python3 scripts/verify.py --profile full
python3 scripts/verify.py --profile windows-portable
```

## Shared evidence sentences

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## Offline fixtures

The offline suites prove the deterministic contract only.

- `korean-writing-editor`: trigger, mode, preservation, and output fixtures under `tests/korean-writing-editor/offline/`
- `image-workbench`: routing, authorization, ImageSpec, handoff, and inspector fixtures under `tests/image-workbench/`

A pass does not mean general Korean editing quality, semantic equivalence, live image quality, commercial permission, a better provider, or runtime parity. The license is Apache-2.0.

## Live execution

Live evaluation is local only. It needs a positive flag, a named runtime, a bounded call budget, and an evidence root outside tracked source. CI never requires it. Provider processes are never silently substituted.

Status labels are `verified`, `partially_verified`, `failed`, `blocked`, and `not_measured`. Do not turn an offline pass into `partially_verified`, and do not turn an unavailable provider into a pass.

Korean live ceilings follow the 119 / 3 / 122 / 38 / 160 budgets in the maintainer protocol. Operator steps are in `tests/korean-writing-editor/live/README.md`. Do not commit user Korean text, provider responses, private reference images, generated images, credentials, or receipts.

## Limitations

Report measured support and fixture results only. Do not claim plugin-directory availability, support on every host, general quality, live image quality, settled reuse rights, or a better provider.
