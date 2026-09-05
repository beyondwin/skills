# Pre-SDD review evidence recorder

`evidence.py` is the optional local recorder for `pre-sdd-review`. It needs
Python 3.11+ and the standard library only, makes no model, provider, or
network call, and is never installed: run it from the skill root.

```sh
python3 "<skill-root>/evidence/evidence.py" --version
```

## Data

Each run is one file, `~/.pre-sdd-review/runs/<run-id>.json`. The only
override for the root is a non-empty absolute `PRE_SDD_REVIEW_HOME`. Records
are schema 2 and at most 64 KiB; anything else under the root, including
schema 1 receipts, is ignored and never written.

## Commands

| Command | Arguments | Effect |
| --- | --- | --- |
| `--version` | none | Print `{"cli_version":"2.0.0","schema":2,"skill_name":"pre-sdd-review"}` |
| `start` | `--skill-root --repo --plan [--design] --client --model --mode` | Hash the documents, read Git state, write a `pending` record, print `run_id` |
| `finish` | `--run-id --repo` and one JSON object on stdin | Recompute end hashes and Git state, validate, write `completed` |
| `abandon` | `--run-id --reason` | Close a pending run; reason is `user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`, or `other` |
| `outcome` | `--run-id --label [--note]` | Record `good`, `false-ready`, `noisy`, or `abandoned` on a completed run; may be re-recorded |
| `show` | `--run-id` | Print the record verbatim |
| `summary` | `[--repo NAME] [--last N]` | Print the aggregate JSON below |

`finish` reads exactly these keys: `execution` (`full`, `degraded`,
`blocked`), `reviewers` (0–2), `trigger` (`runtime-removal`,
`schema-migration`, `auth-boundary`, `data-boundary`, `external-side-effect`,
or null), `degraded_reasons` (list), `verdict`, `block_reason`,
`review_passes` (1–3), `repair_passes` (0–2), and `findings`. Each finding has
`id` (`PSDR-001`), `severity`, `class`, `pattern`, `status`, `repair_pass`,
`location` (`path`, `locator`), `evidence` (relative paths), `consequence`, and
`fix`. `READY` permits only repaired findings, `REVISE` needs an unresolved
one, `BLOCKED` needs `block_reason`, a repair pass needs a repaired finding,
and `review-only` permits no repair pass.

## Reading the log

The log is for agents. `summary` returns `runs`, `counts`, `cost`, `chains`
(plans reviewed more than once), `findings` (with `repeated_patterns`), and
`anomalies`; every entry carries `run_id` values for `show`. Start from
`anomalies` and `chains`.

## Boundary

Records hold repository-relative paths, a directory name, hashes, enum
values, integers, timestamps, and short paraphrases. Never put source text,
absolute paths, prompts, transcripts, command output, or credentials in a
note, consequence, or fix. Files are local and unsigned: self-improvement
evidence, not an audit log.

## Errors

Failures print one line to stderr, `{"error":{"code":"…","message":"…"}}`,
and exit 2. Codes: `invalid-arguments`, `schema-invalid`, `run-not-found`,
`not-git-repository`, `outside-repository`, `already-finished`,
`evidence-home-unwritable`.
