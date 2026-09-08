# Pre-SDD review evidence recorder

`evidence.py` is the optional local recorder for `pre-sdd-review`. It needs
Python 3.11+ and the standard library only, makes no model, provider, or
network call, and is never installed: run it from the skill root.

```sh
python3 "<skill-root>/evidence/evidence.py" --version
```

The compatibility handshake is exactly `skill_name=pre-sdd-review` and
`schema=3`. The canonical version output is one JSON line followed by one LF:

```json
{"cli_version":"3.0.0","schema":3,"skill_name":"pre-sdd-review"}
```

## Data and checkout identity

Each run is one file, `~/.pre-sdd-review/runs/<run-id>.json`. The only
override for the evidence home is a non-empty absolute
`PRE_SDD_REVIEW_HOME`. Schema 3 records are at most 64 KiB. Readers validate
both schema 2 and schema 3 files in `runs/*.json`; mutation commands accept
only schema 3.

The recorder creates `.identity-salt` as private local state containing
exactly 32 random bytes. It never prints or records the salt. The normalized
Git directory and normalized checkout root feed HMAC-SHA-256 only; a schema 3
record stores the repository display name in `repo` and the derived digest in
`repo_key`. It never stores either identity input path.

The binding belongs to the current checkout, evidence home, and salt. A moved
checkout, clone, other worktree, lost salt, or different evidence home cannot
be treated as the original binding. Start a new run. Never infer identity from
the display name or infer a checkout identity for a historical record.

Schema 2 remains readable as `historical-unbound`. A schema 2 pending run is
read-only: preserve it and start a new run if recording is still wanted.
Attempts to mutate it fail with `legacy-record-read-only`.

## Locks and commands

Mutations serialize identity creation with `.identity.lock` and a run change
with `locks/<run-id>.lock`. These locks require supported OS file locking.
Read-only `show`, `summary`, and `--version` do not require locking. Native
Windows mutation support is not advertised because this implementation uses
POSIX `fcntl.flock` when a mutation needs a lock.

| Command | Arguments | Effect |
| --- | --- | --- |
| `--version` | none | Print the canonical schema 3 handshake |
| `start` | `--skill-root --repo --plan [--design] --client --model --mode` | Create the identity if needed, hash documents, read Git state, write a checkout-bound `pending` record, print `run_id` |
| `finish` | `--run-id --repo` and one JSON object on stdin | Require the original checkout binding, recompute end hashes and Git state, validate, write `completed` |
| `abandon` | `--run-id --reason` | Close a schema 3 pending run; reason is `user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`, or `other` |
| `outcome` | `--run-id --label [--note]` | Record `good`, `false-ready`, `noisy`, or `abandoned` on a completed schema 3 run; may be re-recorded |
| `show` | `--run-id` | Validate the record, then return its original bytes unchanged |
| `summary` | `[--repo NAME] [--last N]` | Scan and validate records, then print the aggregate JSON below |

`finish` reads exactly these keys: `execution` (`full`, `degraded`,
`blocked`), `reviewers` (0–2), `trigger` (`runtime-removal`,
`schema-migration`, `auth-boundary`, `data-boundary`, `external-side-effect`,
or null), `degraded_reasons` (list), `verdict`, `block_reason`,
`review_passes` (1–3), `repair_passes` (0–2), and `findings`. Each finding has
`id` (`PSDR-001`), `severity`, `class`, `pattern`, `status`, `repair_pass`,
`location` (`path`, `locator`), `evidence` (relative paths), `consequence`, and
`fix`.

Shape, enum and count ranges, record-size limits, safe repository-relative
paths, and required fields are rejected input when invalid. Semantic review
still follows the verdict, reviewer, finding, and repair rules in
`references/reviewer-protocol.md`. Structurally valid deviations from those
rules remain observed values and appear in `anomalies`; the recorder does not
rewrite or override the semantic verdict.

## Reading the log

The log is for agents. `summary` returns `runs`, `counts`, `cost`, `chains`
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
