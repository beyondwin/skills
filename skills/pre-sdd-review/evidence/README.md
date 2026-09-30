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
`schema=5`. The canonical version output is one JSON line followed by one LF:

```json
{"cli_version":"6.0.0","schema":5,"skill_name":"pre-sdd-review"}
```

## Data and checkout identity

Each run is one file, `~/.pre-sdd-review/runs/<run-id>.json`. The only
override for the evidence home is a non-empty absolute
`PRE_SDD_REVIEW_HOME`. Records are at most 64 KiB. Every command reads and
writes schema 5 only.

The recorder creates `.identity-salt` as private local state containing
exactly 32 random bytes. It never prints or records the salt. The normalized
Git directory and normalized checkout root feed HMAC-SHA-256 only; a record
stores the repository display name in `repo` and the derived digest in
`repo_key`. It never stores either identity input path.

The binding belongs to the current checkout, evidence home, and salt. A moved
checkout, clone, other worktree, lost salt, or different evidence home cannot
be treated as the original binding. Start a new run. Never infer identity from
the display name.

## Records from earlier recorders

Recorders before 6.0.0 wrote schema 2, 3, or 4 files (schema 5 came from
4.0.0 through 5.1.0). This recorder does
not read, migrate, or close them. `show`, `finish`, `abandon`, and `outcome` on
such a run fail with `schema-unsupported` and leave the file unchanged.
`summary` skips it and counts it in `unsupported_records`. They never block
`start`: a new run is always schema 5. To clear them, delete each
`~/.pre-sdd-review/runs/<run-id>.json` whose top-level `schema` is 2, 3, or 4.

## Locks and commands

Mutations serialize identity creation with `.identity.lock` and a run change
with `locks/<run-id>.lock`. A command deletes its lock file while still
holding the lock; a waiter that then wakes on the deleted file retries on the
current one, so two commands never hold the same lock. These locks require supported OS file locking. Read-only
`show`, `summary`, and `--version` do not require locking. Windows is not a
supported OS; this uses POSIX `fcntl.flock`.

| Command | Arguments | Effect |
| --- | --- | --- |
| `--version` | none | Print the canonical schema 5 handshake |
| `start` | `--skill-root --repo --plan [--design] [--ledger] [--prior-plan ...] --client [--model] --mode` | Create the identity if needed, hash documents, read Git state, validate and write a checkout-bound `pending` record, print `run_id` and `status` |
| `finish` | `--run-id --repo` and one JSON object on stdin | Require the original checkout binding, recompute the design, plan, and ledger end hashes and Git state, validate, write `completed`, print `run_id`, `status`, `verdict`, and this run's `anomalies` |
| `abandon` | `--run-id --repo --reason` | Require the original checkout binding, then close a pending run; reason is `user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`, or `other` |
| `outcome` | `--run-id --label [--note]` | Record `good`, `false-ready`, `noisy`, or `abandoned` on a completed run; may be re-recorded |
| `show` | `--run-id` | Validate the record, then return its original bytes unchanged |
| `summary` | `[--repo NAME] [--plan PATH] [--last N]` | Scan and validate records, then print the aggregate JSON below |

`--client` is `codex`, `claude-code`, `cursor`, `grok`, `other`, or `unknown`.
`--mode` is `default` or `review-only`. `--model` defaults to `unknown`.
`--repo` on `start`, `finish`, and `abandon` is a path into the checkout;
`summary --repo` is the checkout directory's name and `summary --plan` is the
plan's repository-relative path.

`finish` reads exactly these keys: `execution` (`full`, `degraded`,
`blocked`), `reviewers` (0–2), `trigger` (`runtime-removal`,
`schema-migration`, `auth-boundary`, `data-boundary`, `external-side-effect`,
or null), `degraded_reasons` (list of `primary-role-not-obtained`,
`focused-role-not-obtained`, `agent-reused-within-invocation`,
`agent-reused-across-plans`, or `other`), `verdict`, `block_reason`,
`review_passes` (0–4; 0 only for `execution` `blocked` with `reviewers` 0),
`repair_passes` (0–3), and `findings`. Example:

```json
{"execution":"full","reviewers":1,"trigger":null,"degraded_reasons":[],"verdict":"READY","block_reason":null,"review_passes":1,"repair_passes":0,"findings":[]}
```

Each finding has `id` (`PSDR-001`), `severity`, `class`, `pattern` (a
lowercase slug for the defect shape), `status` (`repaired`,
`partially-closed`, `unresolved`),
`source` (`reviewer`, `ledger-pass`, `machine-check`), `repair_pass` (null or
0–3, where `0` marks a pre-pass ledger or machine-check repair), `location`
(`path`, `locator`), `evidence` (relative paths), `consequence`, and `fix`.

A record also carries `baseline` (`head` plus the ordered `prior_plans` this
plan's turn assumes) and `ledger` (the shared-file ledger's `path`,
`sha_start`, and `sha_end`, like `plan` and `design`; null when there is no
ledger). `git` carries `head_start_is_ancestor_of_head_end`: true when the
checkout moved forward, false when it did not, null when the question is moot.
Every stored finding must carry `source`, and every stored `degraded_reasons`
entry must come from the list above.

Shape, enum and count ranges, record-size limits, safe repository-relative
paths, and required fields are rejected input when invalid. Semantic review
still follows the verdict, reviewer, finding, and repair rules in
`references/reviewer-protocol.md`. Structurally valid deviations from those
rules remain observed values and appear in `anomalies`; the recorder does not
rewrite or override the semantic verdict. A campaign run (one with a
`ledger` or `prior_plans`) reports `document_changed_without_repair_pass` only
for its own plan: another plan's repair may change the shared design, and the
ledger is always shared. `repo_reality_citing_documents_only` counts the
ledger as a document, since it is derived evidence.

## Reading the log

The log is for agents.

- Before `start`, run `summary --repo <display name> --plan <plan>`; its
  `runs` are this plan's runs. Close a `pending` one with `abandon --repo`;
  `outside-repository` means it belongs to another checkout.
- A handoff is reusable only from a run whose `execution` is `full`, or
  `degraded` with `focused-role-not-obtained` as its only reason; never from a
  `blocked` run or any other `degraded` run. Reuse it only when its document
  hashes (design, plan, and ledger), `git.head_end`, and the request are all
  unchanged and
  `git diff --name-only <git.head_end>` plus
  `git ls-files --others --exclude-standard` names no path besides the design,
  plan, and ledger. A reuse records nothing and prints
  `Evidence: not_recorded; reason=reused-prior-run`.
- When only the design, plan, or ledger changed since a `REVISE` run, or since
  a `BLOCKED` run whose user decision the documents now record, the next
  invocation continues from closure; `show` supplies that run's findings.
- After `finish`, print the `anomalies` it returned; do not look the run up in
  a windowed `summary`.

`summary` returns `runs`, `runs_total`, `counts`, `cost`, `chains` (plans
reviewed more than once in the same checkout), `findings` (with
`repeated_patterns`), and `anomalies`; every drill-down entry carries `run_id`
values for `show`. Start from `anomalies` and `chains`. `runs` lists at most
the newest 50 of the filtered records, oldest first; `runs_total` counts all of
them, and every other section covers them all.

`invalid_records` is the number of invalid files found across the entire scan
before any filters. `unsupported_records` counts, the same way, the schema 2
and 3 files from earlier recorders. `--repo` filters only the display name in
`repo`; it is not an identity or checkout filter. `--last` selects from the validated records in
their canonical start-time and `run_id` order.

`counts.verdict` counts every validated completed record. The separate
`counts.normal_verdict` and `counts.anomalous_verdict` maps split those same
completed verdicts by whether `anomalies` observed a contradiction. The
`counts.observation` map gives the normal and anomalous run totals.

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
`evidence-home-unwritable`, `identity-unavailable`, `schema-unsupported`,
and `locking-unavailable`. `finish` needs every recorded document (design,
plan, ledger) still at its path; a missing one fails with
`outside-repository` and leaves the run `pending`, so close it with `abandon`.
