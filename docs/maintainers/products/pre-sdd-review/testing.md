# pre-sdd-review testing

This document sets how far each kind of check proves anything: contract checks
that run without a model, small synthetic fixtures, and optional live checks
that call a real model. It does not claim to measure real review quality.

Provider-free tests and fixtures live in `tests/products/pre-sdd-review/`.

## Provider-free evidence

Run the product contract with no provider credentials and no model calls.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_c*.py' -v
```

This runs `test_contract.py` (package identity, instructions, fixtures,
activation boundary) together with `test_campaign_schedule.py` (discovery
waves, serial repairs, dirty propagation). It does not include the evidence
suite. It does not prove live review, semantic quality, or equal support on
other hosts.

The `evidence/evidence.py` recorder contract runs as a separate provider-free
stage. It checks the schema 4 checkout binding, refusal of old schema 2 and 3
records (`schema-unsupported`), mutation locks, quarantine of damaged records,
the six commands, and summary observation counts. The recorder runs as
`python3 skills/pre-sdd-review/evidence/evidence.py` and is not installed.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
```

This stage calls no network or provider, and adds no database or index.

The schema 4 document checks in `test_contract.py` are only consistency
evidence: they check that the installed instructions, the recorder guide, and
the maintainer contract describe the same lifecycle. The evidence suite owns
proof of real recorder behavior. This approved scope calls no provider or real
model, so real model review quality is `not_measured`.

## Fixture boundary

`cases.json` owns exactly fifty-one cases covering activation, default flow,
review-only, verdicts, risk, freshness, evidence, and near-miss requests.
`fixtures/` owns exactly seven synthetic repositories:
`ready`, `missing-coverage`, `false-verification`, `runtime-removal`,
`repair-induced-schema-consumer`, `state-machine-vacuous-pass`, and
`conditional-edit-surface`. Each holds only `design.md`, `plan.md`,
`repository.json`, `expected.json`.

Fixtures are a bounded synthetic contract, not a corpus. Never store user
documents, private prompts, credentials, transcripts, or full model responses
in fixtures, test logs, or committed live records.

### Case inventory

- `default-auto-improve`
- `explicit-review-only`
- `ready-zero-findings`
- `missing-spec-coverage`
- `nonexistent-command`
- `extension-collision`
- `false-positive-smoke`
- `task-interface-order`
- `runtime-removal-risk-review`
- `third-review-role`
- `unmapped-repairable-finding`
- `unmapped-authority-finding`
- `stale-document-hash`
- `required-base-not-in-head`
- `ambiguous-multiple-plans`
- `evidence-cli-recorded`
- `evidence-cli-unavailable`
- `evidence-review-only`
- `evidence-resolution-blocked`
- `evidence-outcome-optional`
- `summary-before-start`
- `serialize-split-plans`
- `zero-findings-skip-closure`
- `repair-pass-accounting`
- `red-flag-seeded-retry`
- `red-flag-anomalous-ready`
- `blocked-execution-restarts`
- `near-miss-write-spec`
- `near-miss-write-plan`
- `near-miss-code-review`
- `near-miss-release-review`
- `ledger-required-for-multiple-plans`
- `baseline-reconstruction-required`
- `partial-closure-not-a-new-finding`
- `degraded-handoff-not-reused`
- `zero-findings-but-dirty`
- `closure-requires-repair-diff`
- `host-limit-waves-not-reuse`
- `head-break-no-ready`
- `no-automatic-second-campaign`
- `residual-pass-closes-small-remainder`
- `open-blocker-forces-blocked`
- `repair-last-no-ready`
- `unanswered-decision-no-redispatch`
- `three-new-decisions-return-to-design`
- `continuation-skips-discovery`
- `continuation-after-committed-docs`
- `continuation-needs-docs-only-diff`
- `continuation-needs-recorded-run`
- `focused-only-degraded-continues`
- `continuation-after-recorded-decision`

### Fixture inventory

- `conditional-edit-surface`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `false-verification`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `missing-coverage`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `ready`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `repair-induced-schema-consumer`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `runtime-removal`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `state-machine-vacuous-pass`: `design.md`, `expected.json`, `plan.md`, `repository.json`

## Optional live checks

Live checks are local, explicit, and optional. They may cost money. CI does
not require them. They use only a fresh Codex session and a non-sensitive
synthetic design and plan. The record keeps only host, client version, date,
case identifier, and verdict. Never turn a provider-free result into a live
quality claim. Never store user documents or full model responses.

The v1.1 forward check calls `repair-induced-schema-consumer`,
`state-machine-vacuous-pass`, and `conditional-edit-surface` separately, with
the expected answers hidden. Each call keeps a verdict for its own plan only.
It must show no false `READY`, no unrelated edit, and no authority drift. The
existing `ready` fixture is the provider-free positive control. This check does
not replace repeated evaluation or general quality measurement.

Controller boundary probes inject a fixed intermediate state into a real model
to check one `SKILL.md` branch. Each builds a synthetic Git repository and an
empty evidence home, and pins `PRE_SDD_REVIEW_HOME` to that home for every
`evidence.py` call. Probe records never land in the default home
`~/.pre-sdd-review/`. The controller gets only `SKILL.md` and the skill root,
never the answer or the expected result. Scoring reads the decision or report
file the controller writes.

- Re-review on changed repository evidence: name a required base in the plan,
  create a `BLOCKED` record with `execution=blocked` and `reviewers=0` while
  that ref is missing, then create the ref at `HEAD`. Document hashes do not
  change. Pass if the controller reaches `start`; fail if it reuses the earlier
  handoff.
- Re-ask for incomplete records: present a reviewer that returned only a
  summary and a verdict, and capture the next message to a file. Pass if it
  asks only for the missing fields and names no finding, path, symbol, or fix.
- Anomalous READY report: present a record finished with `reviewers=2` and no
  trigger, and capture the final report. Pass if the `Anomalies:` line contains
  `full_reviewer_count_mismatch` and `READY` stands.
- Out-of-window run report: as above, but after that run starts, start and
  finish twenty runs from another repository, then `finish` that run. Pass if
  the `Anomalies:` line shows that run's anomalies. Looking it up in
  `summary --last` instead of the `finish` output misses it.

These probes are optional and CI does not require them. One result per case is
not a model quality measurement.

Evidence tests use only temporary Git repositories and synthetic skill roots.
Records never hold source text, raw paths, prompts, transcripts, or
credentials. `outcome` labels and the normal/anomalous verdict split are
observer input, not model quality or audit-grade proof. Damaged-record counts
come from a full scan before filtering. Windows and Linux are not supported.
Claude Code, Cursor, and Grok stay `not_measured` until their own native or
live stage runs separately.
