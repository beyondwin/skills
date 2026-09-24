# Pre-SDD review evidence recorder

`evidence.py` is the optional local recorder for `pre-sdd-review`. It needs
Python 3.11+ and the standard library only, makes no model, provider, or
network call, and is never installed: run it from the skill root.

```sh
python3 "<skill-root>/evidence/evidence.py" --version
```

From a clone of this repository:

```sh
python3 skills/pre-sdd-review/evidence/evidence.py --version
```

The compatibility handshake is exactly `skill_name=pre-sdd-review` and
`schema=4`. The canonical version output is one JSON line followed by one LF:

```json
{"cli_version":"5.1.0","schema":4,"skill_name":"pre-sdd-review"}
```

## Data and checkout identity

Each run is one file, `~/.pre-sdd-review/runs/<run-id>.json`. The only
override for the evidence home is a non-empty absolute
`PRE_SDD_REVIEW_HOME`. Schema 4 records are at most 64 KiB. Readers validate
schema 2, 3, and 4 files in `runs/*.json`; `finish` and
`outcome` accept only schema 4. A schema 3 pending run may be `abandon`ed so an
in-flight run survives the upgrade; a schema 2 record stays fully read-only.

The recorder creates `.identity-salt` as private local state containing
exactly 32 random bytes. It never prints or records the salt. The normalized
Git directory and normalized checkout root feed HMAC-SHA-256 only; a schema 3
or 4 record stores the repository display name in `repo` and the derived
digest in `repo_key`. It never stores either identity input path.

The binding belongs to the current checkout, evidence home, and salt. A moved
checkout, clone, other worktree, lost salt, or different evidence home cannot
be treated as the original binding. Start a new run. Never infer identity from
the display name or infer a checkout identity for a historical record.

Schema 2 remains readable as `historical-unbound`. A schema 2 pending run is
read-only: preserve it and start a new run if recording is still wanted.
Attempts to mutate it fail with `legacy-record-read-only`.

## Locks and commands

Mutations serialize identity creation with `.identity.lock` and a run change
with `locks/<run-id>.lock`. After the command releases the lock, it removes
that lock file. These locks require supported OS file locking.
Read-only `show`, `summary`, and `--version` do not require locking. Windows
is not a supported OS; this uses POSIX `fcntl.flock`.

| Command | Arguments | Effect |
| --- | --- | --- |
| `--version` | none | Print the canonical schema 4 handshake |
| `start` | `--skill-root --repo --plan [--design] [--ledger] [--prior-plan ...] --client --model --mode` | Create the identity if needed, hash documents, read Git state, write a checkout-bound `pending` record, print `run_id` |
| `finish` | `--run-id --repo` and one JSON object on stdin | Require the original checkout binding, recompute end hashes and Git state, validate, write `completed`, print `run_id`, `verdict`, and this run's `anomalies` |
| `abandon` | `--run-id --reason` | Close a schema 4 pending run, or a schema 3 pending run left over from before the upgrade; reason is `user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`, or `other` |
| `outcome` | `--run-id --label [--note]` | Record `good`, `false-ready`, `noisy`, or `abandoned` on a completed schema 4 run; may be re-recorded |
| `show` | `--run-id` | Validate the record, then return its original bytes unchanged |
| `summary` | `[--repo NAME] [--last N]` | Scan and validate records, then print the aggregate JSON below |

`finish` reads exactly these keys: `execution` (`full`, `degraded`,
`blocked`), `reviewers` (0–2), `trigger` (`runtime-removal`,
`schema-migration`, `auth-boundary`, `data-boundary`, `external-side-effect`,
or null), `degraded_reasons` (list of `primary-role-not-obtained`,
`focused-role-not-obtained`, `agent-reused-within-invocation`,
`agent-reused-across-plans`, or `other`), `verdict`, `block_reason`,
`review_passes` (1–4), `repair_passes` (0–3), and `findings`.

Each finding has `id` (`PSDR-001`), `severity`, `class`, `pattern`, `status`,
`source` (`reviewer`, `ledger-pass`, `machine-check`), `repair_pass` (null or
0–3, where `0` marks a pre-pass ledger or machine-check repair), `location` (`path`,
`locator`), `evidence` (relative paths), `consequence`, and `fix`.

A schema 4 record adds `baseline` (`head` plus the ordered `prior_plans` this
plan's turn assumes) and `ledger` (the shared-file ledger's `path` and `sha`, or
null). `git` adds `head_start_is_ancestor_of_head_end`: true when the checkout
moved forward, false when it did not, null when the question is moot. Each
finding adds `source`.

`source` is the only finding key schema 4 added, so a schema 2 or 3 finding does
not carry it and stays readable without it; a legacy finding that does carry it
is `schema-invalid`. Every other finding key is the same across schema 2, 3, and
4. A schema 2 or 3 `degraded_reasons` entry is likewise read back as free text
rather than against the schema 4 vocabulary.

Shape, enum and count ranges, record-size limits, safe repository-relative
paths, and required fields are rejected input when invalid. Semantic review
still follows the verdict, reviewer, finding, and repair rules in
`references/reviewer-protocol.md`. Structurally valid deviations from those
rules remain observed values and appear in `anomalies`; the recorder does not
rewrite or override the semantic verdict.

## Reading the log

The log is for agents. Before `start`, run `summary --repo <display name>`
and find the plan in `runs` and `chains`. Close a same-plan `pending` run.
Never reuse the handoff of a run whose `execution` is `blocked` or
`degraded`; for a `full` `REVISE` or `BLOCKED` run, reuse it only when its
document hashes, `git.head_end`, and the request are all unchanged. After
`finish`, print the `anomalies` it returned; do not look the run up in a windowed
`summary`. `summary` returns `runs`, `counts`, `cost`, `chains`
(checkout-bound plans reviewed more than once), `findings` (with
`repeated_patterns`), and `anomalies`; every drill-down entry carries `run_id`
values for `show`. Start from `anomalies` and `chains`.

`invalid_records` is the number of invalid files found across the entire scan
before any filters. `--repo` filters only the display name in `repo`; it is not
an identity or checkout filter. `--last` selects from the validated records in
their canonical start-time and `run_id` order.

`counts.verdict` counts every validated completed record. The separate
`counts.normal_verdict` and `counts.anomalous_verdict` maps split those same
completed verdicts by whether `anomalies` observed a contradiction. The
`counts.observation` map gives the normal and anomalous run totals, and
`counts.binding` reports `checkout-bound` and `historical-unbound` records.
Historical records do not form `chains` because they have no `repo_key`.

These summaries are descriptive local observations. They are not model-quality
measurements, proof that a verdict was correct, or a signed audit claim.

## Boundary

Records hold repository-relative paths, a directory name, `repo_key`, hashes,
enum values, integers, timestamps, and short paraphrases. Never put source
text, absolute paths, prompts, transcripts, command output, credentials, salt,
or identity path material in a note, consequence, or fix. Files are local and
unsigned: self-improvement evidence, not an audit log. The recorder does not
detect secrets.

The reviewer protocol remains authoritative for semantic behavior. Recording
is optional. If the recorder is unavailable or fails, report
`Evidence: not_recorded; reason=<code>`; this cannot change `READY`, `REVISE`,
or `BLOCKED`.

## Errors

Failures print one line to stderr, `{"error":{"code":"…","message":"…"}}`,
and exit 2. Codes: `invalid-arguments`, `schema-invalid`, `run-not-found`,
`not-git-repository`, `outside-repository`, `already-finished`,
`evidence-home-unwritable`, `identity-unavailable`,
`legacy-record-read-only`, and `locking-unavailable`.
