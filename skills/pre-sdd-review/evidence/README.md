# Pre-SDD review evidence CLI

`pre-sdd-review-evidence` is an optional, provider-neutral local recorder. It
requires Python 3.11+ and the standard library only. It makes no model,
provider, telemetry, or network call.

## Install

Choose an existing directory already intended for `PATH`. The installer
neither creates a PATH directory nor edits `PATH` or a shell profile.

```sh
python3 skills/pre-sdd-review/evidence/install.py \
  --bin-dir "$HOME/.local/bin"
pre-sdd-review-evidence --version
```

For another inspected skill copy, pass both paths explicitly:

```sh
python3 /path/to/pre-sdd-review/evidence/install.py \
  --skill-root /path/to/pre-sdd-review \
  --bin-dir /existing/path-directory
```

Do not pipe a remote download to a shell. The installer validates the release
identity and exact seven-file runtime manifest without importing the source,
then copies only those files. An ordinary real `__pycache__` containing only
regular `.pyc` files is ignored; a symlinked cache, nested entry, non-bytecode
file, extra source file, or missing runtime file is rejected. Installation is
create-only: an identical reinstall is idempotent, and different bytes are
never overwritten.

POSIX installation creates `pre-sdd-review-evidence`. Windows installation
creates a `.pyz` plus a quoted `.cmd` wrapper. Portable construction on another
OS does not prove native Windows behavior.

## Basic flow

Receipts live under `~/.pre-sdd-review/`. The only override is a non-empty,
absolute `PRE_SDD_REVIEW_HOME`. The launcher and data root are separate:
installing, updating, removing, or running `--version` does not create, change,
or delete receipts.

The normal lifecycle is:

1. `start` creates a private pending run.
2. `finish-review` creates its immutable review, or `abandon` closes an
   interrupted pending run.
3. `record-outcome` creates at most one immutable terminal outcome after
   downstream work ends.
4. `summary` and `candidates` aggregate validated receipts on demand.

Inspection and maintenance commands are:

```text
show       display one validated run
pending    classify pending runs without changing them
doctor     report local state problems without repairing them
resolve    match the repository identity and exact plan hash
prune      preview, then explicitly confirm, bounded deletion
```

Use each subcommand's `--help` for exact fields.

## Safety and evidence boundary

Review and outcome inputs must contain bounded paraphrases only. Do not put
source or document text, absolute paths, prompts, provider transcripts,
command output, credentials, or environment-variable values in any bounded
field. The CLI validates shapes and obvious prohibited values; it does not
perform automatic secret detection and cannot recognize every sensitive short
string.

Create-only local storage provides atomicity and consistency for cooperating
clients. It is not a signed audit log and does not prevent malicious local
tampering. Structured downstream observations, assessment basis, and confidence
are observer-supplied. The CLI derives `good`, `false-ready`, `noisy`, and
`prevented-rework` deterministically from those observations. Both inputs and
labels are self-improvement evidence, not objective or audit-grade proof.

Before `record-outcome`, represent every known dispute and uncertainty honestly
in the single structured outcome input. Put finding disputes only in
`disputed_findings`; use the applicable structured observation for other
uncertainty. Confidence and assessment basis do not alter the deterministic
label. `inconclusive` occurs only when the structured downstream observations
reach the approved derivation fallback. After the create-only outcome is
recorded, schema 1 cannot correct or amend it. There is no correction or
amendment command, so an erroneous outcome is an explicit residual risk.

Candidate thresholds are inspection heuristics: they do not mutate the skill,
judge quality automatically, or rank clients or models.

## Update, backup, and removal

The installer has no force flag. Inspect the exact target first:

```sh
command -v pre-sdd-review-evidence
ls -l "$HOME/.local/bin/pre-sdd-review-evidence"
pre-sdd-review-evidence --version
```

For different bytes, remove only that verified launcher and reinstall from the
new inspected copy. On Windows, verify and remove the exact `.cmd` and `.pyz`
pair. Removing a launcher does not remove `~/.pre-sdd-review/` or an overridden
data root.

Back up the complete evidence root, including `identity.key` and `config.json`,
when repository identity continuity matters. Stop evidence writers first.
Receipt deletion is a separate operation: inspect `prune --dry-run`, then
confirm only its exact selection.

## Limits and measured support

`review.json` has a 16 KiB soft and 32 KiB hard limit; `outcome.json` has a
4 KiB soft and 8 KiB hard limit; a completed run has a 40 KiB hard limit.
Reporting reads and validates each receipt snapshot once and remains an
on-demand linear scan—there is no database or index.

The native macOS atomic no-replace path and provider-free portable construction
are measured. Native Linux and Windows execution remain `not_measured` until
the full evidence and installer stages pass under Python 3.11+ on those
platforms. The local receipts are unsigned, immutable outcomes have no
amendment path, and same-user mutation outside cooperating CLI operations is
not prevented.
