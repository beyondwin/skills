# Pre-SDD review evidence CLI

`pre-sdd-review-evidence` is the optional, provider-neutral local recorder used
by `pre-sdd-review`. It requires Python 3.11 or newer and uses only the Python
standard library. It does not call a model, provider, telemetry service, or
network endpoint.

## Install

Choose an existing directory that is already intended for `PATH`; the
installer neither creates a PATH directory nor edits `PATH` or a shell
profile. From this skill checkout, run:

```sh
python3 skills/pre-sdd-review/evidence/install.py \
  --bin-dir "$HOME/.local/bin"
pre-sdd-review-evidence --version
```

When running the installer from somewhere else, name the loaded skill copy
explicitly:

```sh
python3 /path/to/pre-sdd-review/evidence/install.py \
  --skill-root /path/to/pre-sdd-review \
  --bin-dir /existing/path-directory
```

Do not pipe a remote download to a shell. Install only from a skill copy whose
files you have inspected. The installer validates the exact runtime manifest
and version constants without importing the supplied source, copies only the
listed runtime files, and refuses to replace a nonidentical target. An
identical reinstall is safe and idempotent.

On POSIX, installation creates the executable
`pre-sdd-review-evidence`. On Windows, it creates
`pre-sdd-review-evidence.pyz` and `pre-sdd-review-evidence.cmd`; the wrapper
quotes the Python interpreter selected at installation. Portable wrapper
tests on another operating system do not prove native Windows behavior.

## Data location and commands

Receipts live under `~/.pre-sdd-review/`. The only supported override is an
absolute, non-empty `PRE_SDD_REVIEW_HOME`. The launcher and the data root are
separate: installing, updating, or removing the launcher does not create,
change, or delete receipts. `--version` also does not inspect or create the
data root.

The command surface is:

```text
start             begin a private pending review run
finish-review     create the immutable review receipt
abandon           close an interrupted pending run
show              display one validated run
pending           classify pending runs without changing them
doctor            report local state problems without repairing them
resolve           match the current repository and exact plan hash
record-outcome    create one terminal downstream outcome
summary           aggregate validated receipts on demand
candidates        list or explicitly export sanitized fixture candidates
prune             preview, then explicitly confirm, bounded deletion
```

Use each subcommand's `--help` for its exact fields. Review and outcome inputs
must contain bounded paraphrases only. Do not put source or document text,
absolute paths, prompts, provider transcripts, command output, credentials,
or environment-variable values in a reason, finding, basis, or other bounded
field. The CLI validates shapes and obvious prohibited values; it does not
perform automatic secret detection and cannot recognize every sensitive
short string.

## Update

The installer has no force or overwrite flag. First identify and inspect the
exact installed target:

```sh
command -v pre-sdd-review-evidence
ls -l "$HOME/.local/bin/pre-sdd-review-evidence"
pre-sdd-review-evidence --version
```

An identical package can be installed again directly. To replace different
bytes, inspect the path above, remove only that exact launcher, and rerun the
installer from the new skill copy:

```sh
rm -- "$HOME/.local/bin/pre-sdd-review-evidence"
python3 /path/to/pre-sdd-review/evidence/install.py \
  --skill-root /path/to/pre-sdd-review \
  --bin-dir "$HOME/.local/bin"
```

On Windows, inspect `Get-Command pre-sdd-review-evidence` and the exact `.cmd`
and `.pyz` targets before removing those two files and reinstalling them.

## Backup and removal

Back up the complete evidence root, including `identity.key` and
`config.json`, if repository identity continuity matters. For example, after
ensuring no evidence command is writing:

```sh
cp -a "$HOME/.pre-sdd-review" "/path/to/backup/pre-sdd-review"
```

Before removing the launcher, inspect the exact target again:

```sh
command -v pre-sdd-review-evidence
ls -l "$HOME/.local/bin/pre-sdd-review-evidence"
rm -- "$HOME/.local/bin/pre-sdd-review-evidence"
```

Removing a launcher does not remove `~/.pre-sdd-review/` or an overridden data
root. Receipt deletion is a separate explicit operation; inspect a `prune`
dry-run and confirm only its exact selection.

## Evidence boundary

Create-only local storage provides atomicity and consistency for cooperating
clients. It is not a signed audit log and does not prevent malicious local
tampering. Structured downstream observations, assessment basis, and confidence
are observer-supplied. The CLI derives `good`, `false-ready`, `noisy`, and
`prevented-rework` deterministically from those observations. Both the inputs
and derived labels are self-improvement evidence rather than objective or
audit-grade proof.

Schema 1 records one immutable review and at most one immutable terminal
outcome. Before `record-outcome`, represent every known dispute and uncertainty
honestly in the single structured outcome input. Record finding disputes only
in the bounded `disputed_findings` field and use the applicable structured
observation fields for other uncertainty. Confidence and assessment basis do
not alter the deterministic label. `inconclusive` occurs only when the
structured downstream observations reach the approved derivation fallback. A
completed outcome with no escaped, disputed, or prevented-rework observation,
for example, derives `good` even when confidence is low. After the create-only
outcome is recorded, schema 1 cannot correct or amend it. It has no correction
or amendment command; an erroneous recorded outcome is an uncorrectable
residual risk, not a correction path. Candidate thresholds are inspection
heuristics: they do not mutate the skill, judge quality automatically, or rank
clients or models.
