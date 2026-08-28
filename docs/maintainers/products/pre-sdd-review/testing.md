# pre-sdd-review testing

This document owns provider-free contract evidence, bounded fixtures, and the
optional live-check boundary. It does not claim to measure model review quality.

## Required provider-free command

Run the product contract without provider credentials or a model call:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

The command proves package identity, instructions, fixture shape, activation
boundaries, and documented contract facts. It does not prove a live review,
semantic quality, or equivalent support on another host.

## Exact fixture boundary

`cases.json` owns exactly fourteen activation, default-flow, review-only,
verdict, risk, freshness, and near-miss cases. `fixtures/` owns exactly four
named repositories: `ready`, `missing-coverage`, `false-verification`, and
`runtime-removal`. Each contains only `design.md`, `plan.md`,
`repository.json`, and `expected.json`.

Fixtures are bounded synthetic contracts, not a corpus. Do not store user
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
- `stale-document-hash`
- `near-miss-write-spec`
- `near-miss-write-plan`
- `near-miss-code-review`
- `near-miss-release-review`

### Fixture inventory

- `false-verification`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `missing-coverage`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `ready`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `runtime-removal`: `design.md`, `expected.json`, `plan.md`, `repository.json`

## Optional fresh-session live checks

A live check is local, explicit, optional, and may be billable; CI never
requires it. Use a fresh Codex session, a non-sensitive synthetic design and
plan, and record only host, client version, date, case identifier, and verdict.
Do not turn provider-free evidence into a claim about live quality. Do not
store user documents or full model responses.
