# korean-writing-editor change protocol

Keep trigger, mode, output, evidence, fixtures, and version in lockstep. A prompt-only edit that leaves fixtures or the public guides stale is a contract break. Public install guidance lives in `docs/ko/` and `docs/en/`, not in the installed payload.

## Contract changes

Synchronize these files together. Do not ship a behavior change in only one of them.

- Trigger or near-miss change: update `skills/korean-writing-editor/SKILL.md` activation text, positive and near-miss fixtures in `tests/korean-writing-editor/offline/cases.json`, and the paired public guides.
- Mode or output-contract change (`diagnose`, `correct`, `polish`, default edited-text-only output, or the hold note): update `SKILL.md`, `skills/korean-writing-editor/references/editorial-guide.md`, fixtures, and the paired public guides.
- Model-tier change (`fast`, `balanced`, `frontier`, routing, or delegation): update routing fixtures in `tests/korean-writing-editor/offline/cases.json` and the paired public guides. Do not hard-code provider model names or call a classifier model.

## Evidence changes

- Normative claim change: update the authoritative source locator in `skills/korean-writing-editor/references/sources.md` and add or adjust a fixture that encodes the claim boundary.
- External project use: record the pinned revision, license, checked date, and an explicit adopted/rejected boundary in `references/sources.md`. Do not copy third-party rule lists or corpora.

## Fixture changes

Keep the thirty-one property cases and mutation checks honest in `tests/korean-writing-editor/offline/cases.json` and `tests/korean-writing-editor/offline/run.py`.

- Trigger work needs both positive and near-miss records.
- Mode, output, preservation, and tier work needs matching `expected_mode`, `expected_tier`, and `expected_noop` records.
- Voice cases protect small register or stance spans. They must not require the whole candidate string to equal the source.
- Mixed normative cases may protect an already-correct obligation or modality span in the same record as a local spelling fix.
- A candidate with process preamble must fail the replaced `norm-spacing-can-01` properties.
- Passing fixtures proves the offline oracle contract. It does not prove live model quality.
- Live-harness changes keep `tests/korean-writing-editor/live/live_cases.json`, `live_matrix.py`, `test_live_matrix.py`, and `tests/korean-writing-editor/live/README.md` in sync. Live cases remain synthetic; none of these artifacts may contain private manuscripts or full transcripts.
- Live budget changes keep the 119-producer, 3-reviewer, 122-baseline, 38-remediation, and 160-total dry-run and parser assertions synchronized. Report-bearing resume changes need a real temporary-Git test for both the absent-report first publication and a crash after report publication before report-state persistence.
- Remediation needs one or more immutable planned producer call IDs, in canonical full-plan order, bound into the run identity. It never dispatches reviewer calls unless a separately approved reviewer mechanism is designed. Reserve a report target and its matching state before any paid dispatch; do not treat a final report write as the first ownership claim.

## Live harness invariants

Dry-run must emit `producer_calls=119`, `reviewer_calls=3`, `baseline_calls=122`, `remediation_calls=38`, and `approved_total_ceiling=160`. Starting multiple cycles does not turn them into one approved 160-call result.

Before every Codex or Cursor provider process invocation, the runner validates CLI availability, argv, immutable run identity, and the active report lease, then durably records one immutable attempt reservation immediately before process invocation. The reservation binds the complete run identity, logical and actual call IDs, positive gap-free global call number, producer or reviewer kind, host, requested model, case ID, and repeat index. Only a true zero-provider `not_measured` receipt may use call number zero without a reservation; every `verified`, `partially_verified`, `failed`, or `blocked` receipt must match one positive reservation exactly, and a reviewer receipt cannot match a producer reservation. Crash-only reservations remain charged, drive unique `:attempt-N` retry IDs, and count in budgets and reports.

After producer dispatch, and again after reviewer dispatch for a baseline, the controller reloads attempt reservations and receipts from disk, validates their exact linkage, and requires one durable terminal receipt for every planned logical call. Review packets, reports, statuses, and counts use only those reloaded durable artifacts, never in-memory dispatch return values. Remediation dispatches producers only and has no reviewer plan.

Dispatcher returns are completion claims only: every returned receipt must match the exact canonical bytes of one reloaded durable receipt. Each normalized producer or reviewer body must be owned by the receipt's exact positive call path and match its `response_sha256`.

One `ReportLease` holds one `O_RDWR` and `O_NOFOLLOW` target file FD plus one open evidence-root `reports` directory FD from pending report reservation through every producer and reviewer call and final publication. Reports live under `<evidence-root>/reports/`, not tracked docs. The lease never replaces the report pathname.

## Versioning

- Behavior change: bump SemVer in `SKILL.md` `metadata.version`.
- Documentation-only wording change: do not bump the version unless behavior also changes.
- A live-harness or dated-report-only change does not bump the skill version.

## Required verification

```bash
python3 scripts/verify.py
python3 tests/korean-writing-editor/offline/run.py --scope full
python3 tests/korean-writing-editor/live/live_matrix.py --dry-run
git diff --check
```

Live canaries remain opt-in and are reported separately. Do not describe offline fixture results as live invocation or model-quality evidence. Keep provider IDs out of `SKILL.md`.
