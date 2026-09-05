# Pre-SDD Review Evidence Simplification Design

**Status:** Approved in chat on 2026-09-05; implementation has not started

**Scope:** Replace the `pre-sdd-review-evidence` package, installer, and
schema 1 receipts with one standard-library script that records what is needed
to judge whether `pre-sdd-review` works, and exposes that data in a form an
agent reads directly. Fix the two evidence-quality defects that the first
eighteen real receipts exposed. Release as `pre-sdd-review` 2.0.0.

**Out of scope:** Changing the review semantics (authority order, two-pass
repair loop, repair-impact map, reviewer roles, verdict rules, handoff packet);
changing host support claims; migrating or reading schema 1 receipts;
uploading evidence; adding a daemon, database, or index; tagging, publishing,
or pushing.

## Context

The evidence loop shipped in 1.2.0 recorded eighteen real runs between
2026-09-02 and 2026-09-04 (13 completed, 5 abandoned; READY 4, REVISE 8,
BLOCKED 1; clients codex 12, grok 4, cursor 1). Reading those receipts against
the code produced these facts:

1. Half of the recorder is unused. `record-outcome` was never called
   (0 of 13), so `verified_false_ready`, `noisy_findings`,
   `prevented_rework`, and `candidates` are permanently `not_measured`. The
   outcome contract requires a matching plan hash, four structured
   observation lists, a basis, and a confidence; nobody pays that cost after
   SDD.
2. The CLI's `**Spec:**` parser disagrees with the controller. Two real plans
   used forms the parser rejects (a backticked path followed by a
   parenthetical; a Markdown link). The controller resolved both designs and
   ran full reviews, but the receipts record `spec-path-invalid` and
   `design-missing` with a null or malformed design path. One further run was
   abandoned only to reformat the field.
3. Schema 1 accepts a READY receipt with `repair_passes=1` and zero findings,
   so repaired findings can vanish from the record.
4. `summary` omits the most basic questions: verdict distribution, abandoned
   runs (28% of all runs), HEAD or dirty-state changes during a review, and
   how many attempts a plan needed before READY (one plan took seven runs).
5. Several fields are never or inconsistently populated because SKILL.md does
   not tell the controller how: `client.version` null in 16 of 18,
   `token_usage` null in 18 of 18, five free-form abandon reasons.
6. Three of thirteen `repo-reality` findings cite only the design or plan
   document. The reviewer protocol allows "repository or cross-document fact",
   so a repository-reality claim can currently rest on no repository evidence.
7. The installed launcher is a copy that drifts from the skill source and
   pins the skill version inside `install.py`, so every patch release must
   also change the installer.

The current recorder is 3,834 lines of runtime and 7,512 lines of tests for
five commands that are used. The owner's priority is, in order: the skill must
demonstrably work, then it must stay light.

## Goals

1. Record, per run, the minimum data that answers "did this review work":
   what was reviewed, under which skill fingerprint and client, how it ended,
   whether protocol was kept, what it cost, what was found and repaired, and
   whether READY later held.
2. Make the downstream truth signal cheap enough to be recorded: one command,
   one label, one optional note, correctable.
3. Remove the parser disagreement by making the controller the only resolver
   of the design path.
4. Expose aggregates as stable JSON with run identifiers attached, so an agent
   can move from a summary to a specific run without scanning files.
5. Eliminate installation: the script runs from the loaded skill root, so the
   recorder is always the version of the skill that produced the review.
6. Reduce the runtime to one file and the tests to one file, both standard
   library only, without weakening the offline and provider-free contract.

## Non-goals

- Guaranteeing tamper evidence. Receipts are local self-improvement records.
- Cross-platform atomic no-replace publication. A temporary file plus
  `os.replace` is sufficient.
- Reading, converting, or deleting schema 1 receipts.
- Automatic skill mutation, ranking of clients or models, or fixture export.
- Any change to `products.toml` host support.

## Decisions

### 1. One script, no installer

The recorder is `skills/pre-sdd-review/evidence/evidence.py`, a single Python
3.11+ file using only the standard library. The controller invokes it with the
skill root it already loaded:

```text
python3 "<skill-root>/evidence/evidence.py" <command> ...
```

There is no launcher, PATH entry, zipapp, or Windows wrapper. The script and
the skill that calls it always share one version and one checkout.

`evidence.py --version` prints exactly one canonical JSON line:

```json
{"cli_version":"2.0.0","schema":2,"skill_name":"pre-sdd-review"}
```

The controller accepts only `skill_name=pre-sdd-review` and `schema=2`.

### 2. Data root and layout

The data root stays `~/.pre-sdd-review/`; the only override is a non-empty
absolute `PRE_SDD_REVIEW_HOME`. Each run is one file:

```text
~/.pre-sdd-review/runs/<run-id>.json
```

`run-id` is a canonical lowercase UUID4. Readers consider only
`runs/*.json` whose top-level `schema` equals 2; anything else, including the
schema 1 `runs/<year>/<month>/` directories, `config.json`, and
`identity.key`, is ignored and never written. Directories are created with
mode `0o700` and files with `0o600`.

Writes go to a sibling temporary file followed by `os.replace`. Distinct
run IDs make concurrent runs independent; a single run is written by one
controller, so no lock is needed. A hard limit of 64 KiB applies to every
record.

### 3. Record schema (schema 2)

Every run file has these top-level keys. `null` is used where a value is not
yet known or does not apply.

| Key | Type | Meaning |
| --- | --- | --- |
| `schema` | `2` | Record schema |
| `run_id` | UUID string | Run identity |
| `status` | `pending` / `completed` / `abandoned` | Lifecycle state |
| `started_at`, `completed_at` | RFC 3339 UTC or null | Timestamps set by the CLI |
| `elapsed_s` | integer or null | `completed_at - started_at` in seconds |
| `skill` | `{version, sha256}` | `metadata.version` from SKILL.md; SHA-256 of SKILL.md bytes followed by reviewer-protocol bytes |
| `client` | `{id, model}` | `id` in `codex`, `claude-code`, `cursor`, `grok`, `other`, `unknown`; `model` is the host-reported string, at most 100 chars, or `unknown` |
| `repo` | string | Repository root directory name |
| `mode` | `default` / `review-only` | Requested mode |
| `plan` | `{path, sha_start, sha_end}` | Repository-relative POSIX path; `sha_end` null until finish |
| `design` | same shape or null | Null when the controller could not resolve `**Spec:**` |
| `git` | `{head_start, head_end, dirty_start, dirty_end}` | `head` is a commit hash or `unborn`; `dirty` is a boolean |
| `execution` | `full` / `degraded` / `blocked` or null | Protocol level actually achieved |
| `reviewers` | 0..2 or null | Logical review roles used |
| `trigger` | one of the five risk triggers or null | Conditional second role trigger |
| `degraded_reasons` | list of strings | Required non-empty when `execution` is `degraded`; each at most 100 chars |
| `review_passes`, `repair_passes` | integers or null | 0..3 and 0..2 |
| `verdict` | `READY` / `REVISE` / `BLOCKED` or null | Final verdict |
| `block_reason` | string or null | Required when `verdict` is `BLOCKED`; at most 100 chars |
| `abandon_reason` | enum or null | See Decision 4 |
| `findings` | list | See below |
| `outcome` | `{label, note, recorded_at}` or null | See Decision 5 |

Each finding is:

| Key | Constraint |
| --- | --- |
| `id` | `PSDR-` followed by three or more digits, unique within the run |
| `severity` | `BLOCKER` / `IMPORTANT` |
| `class` | `authority-drift` / `repo-reality` / `coverage` / `ordering` / `verification-gap` |
| `pattern` | `[a-z0-9][a-z0-9._-]{0,79}` |
| `status` | `repaired` / `unresolved` / `blocked-by-authority` / `accepted-as-is` |
| `repair_pass` | 1, 2, or null; never greater than `repair_passes` |
| `location` | `{path, locator}`; relative path, locator at most 200 chars |
| `evidence` | list of relative repository paths, deduplicated |
| `consequence`, `fix` | single-line paraphrases, at most 300 chars each |

Removed relative to schema 1, with the reason: identity HMAC and `repo_id`
(local-only data does not need a keyed hash; the directory name is what a
reader wants), the seven `resolution_status` values (the controller resolves
the design; `design: null` is the only failure state the record needs),
`consequence_category` (a pre-implementation guess), `token_usage` (never
populated), `client.version` (almost never populated), `fresh_reviewer` and
`read_only_enforced` (implied by `execution: full`), `recorder_elapsed_ms`,
and the three-tier size limits.

Invariants checked at `finish`:

- `READY` permits no finding whose status is not `repaired`.
- `REVISE` requires at least one `unresolved` finding.
- `BLOCKED` requires `block_reason`.
- `repair_passes > 0` requires at least one `repaired` finding.
- `mode = review-only` requires `repair_passes = 0`.
- `execution = full` requires `reviewers` equal to 2 when `trigger` is set and
  1 otherwise, and an empty `degraded_reasons`.
- `execution = degraded` requires a non-empty `degraded_reasons`.
- Every path is a relative POSIX path with no empty, `.`, or `..` segment, no
  backslash, and no drive prefix.

### 4. Commands

| Command | Arguments | Behaviour |
| --- | --- | --- |
| `--version` | none | Print the canonical version line; exit 0 |
| `start` | `--skill-root --repo --plan [--design] --client --model --mode` | Resolve the Git root from `--repo`; require plan (and design, when given) to exist inside it; hash them; read HEAD and dirty state; read skill version and hash from `--skill-root`; write a `pending` record; print `{"run_id": ...}` |
| `finish` | `--run-id --repo`, JSON object on stdin | Require a `pending` record; recompute end hashes and Git state; accept exactly the keys `execution`, `reviewers`, `trigger`, `degraded_reasons`, `verdict`, `block_reason`, `review_passes`, `repair_passes`, `findings`; validate the invariants; write `completed`; print `{"run_id": ..., "status": "completed"}` |
| `abandon` | `--run-id --reason` | Require a `pending` record; reason in `user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`, `other`; write `abandoned` with `completed_at` |
| `outcome` | `--run-id --label [--note]` | Require a `completed` record; label in `good`, `false-ready`, `noisy`, `abandoned`; `false-ready` requires `verdict = READY`; note at most 300 chars; overwrite any previous outcome |
| `show` | `--run-id` | Print the record file verbatim |
| `summary` | `[--repo NAME] [--last N]` | Print the aggregate JSON in Decision 6 |

Path arguments given to `start` may be absolute or relative to the current
directory; only the repository-relative form is persisted. `--repo` may be any
path inside the repository. `finish` and `abandon` verify that `--repo`
resolves to the same root directory name recorded at `start`; a mismatch is
`outside-repository`.

### 5. Controller contract (SKILL.md)

The "Optional local evidence" section of SKILL.md is rewritten to say exactly
this, in its own words:

- Run `python3 "<skill-root>/evidence/evidence.py" --version` first and
  continue only when `schema` is 2 and `skill_name` is `pre-sdd-review`.
- Call `start` before semantic review and `finish` once, after the verdict
  and repairs are final. The same lifecycle applies to `review-only`.
- Pass the design path the controller resolved from the plan's `**Spec:**`
  field as `--design`. If the field cannot be resolved, omit `--design` and
  return `BLOCKED`. The CLI does not parse `**Spec:**`.
- `--client` is the host running the skill; `--model` is the model string the
  host reports, or `unknown`.
- If the invocation ends before `finish`, call `abandon` with one of the five
  reasons. Do not leave a run `pending`.
- Keep `run_id` controller-local and out of user documents. Print exactly one
  line: `Evidence: recorded; run_id=<id>` or
  `Evidence: not_recorded; reason=<code>`. Recorder failure never changes the
  verdict.
- `outcome` is not a controller duty. After SDD or implementation ends, the
  user or the SDD worker may record one label for the run.

Reviewer protocol gains one sentence under Pass 2: a `repo-reality` finding
must cite at least one repository path that is neither the reviewed design nor
the reviewed plan.

### 6. Summary output

`summary` prints one JSON object. Every count that refers to runs carries the
run IDs it counts, so a reader can go directly to `show`.

```json
{
  "schema": 2,
  "runs": [
    {"run_id": "…", "started_at": "…", "repo": "Blog", "plan": "docs/…",
     "status": "completed", "verdict": "REVISE", "findings": 13, "elapsed_s": 3336}
  ],
  "counts": {
    "status": {"completed": 13, "abandoned": 5, "pending": 0},
    "verdict": {"READY": 4, "REVISE": 8, "BLOCKED": 1},
    "execution": {"full": 12, "degraded": 0, "blocked": 1},
    "abandon_reason": {"input-changed": 2, "user-cancelled": 1},
    "outcome": {"recorded": 0, "good": 0, "false-ready": 0, "noisy": 0, "abandoned": 0}
  },
  "cost": {
    "elapsed_s": {"median": 1090, "max": 3627},
    "review_passes_avg": 2.2,
    "repair_passes_avg": 1.2
  },
  "chains": [
    {"repo": "Blog", "plan": "docs/…",
     "runs": [{"run_id": "…", "status": "abandoned", "verdict": null},
              {"run_id": "…", "status": "completed", "verdict": "READY"}]}
  ],
  "findings": {
    "total": 57,
    "by_severity": {"BLOCKER": 22, "IMPORTANT": 35},
    "by_status": {"repaired": 41, "unresolved": 16},
    "by_class": {"verification-gap": 17, "repo-reality": 13},
    "repeated_patterns": [
      {"class": "…", "pattern": "…", "count": 2, "run_ids": ["…", "…"]}
    ]
  },
  "anomalies": {
    "repair_without_repaired_finding": ["…"],
    "head_changed_during_review": ["…"],
    "design_unresolved_but_full_execution": ["…"],
    "repo_reality_citing_documents_only": [{"run_id": "…", "finding_id": "PSDR-007"}]
  }
}
```

Rules: `runs` is ordered by `started_at`; `chains` lists only plans with two
or more runs, grouped by `repo` and `plan.path`; `repeated_patterns` lists
`(class, pattern)` pairs seen in two or more runs; `cost` uses completed runs
only; `--repo` filters by directory name before aggregation; `--last N` keeps
the N most recent runs before aggregation. There is no text renderer.

The anomaly rules are exactly:

- `repair_without_repaired_finding`: completed, `repair_passes > 0`, and no
  finding with `status = repaired`. Schema 2 rejects this at `finish`; the
  anomaly exists to surface hand-edited or future-schema records and stays in
  the contract so the rule is documented in one place.
- `head_changed_during_review`: completed and `git.head_start != git.head_end`.
- `design_unresolved_but_full_execution`: completed, `design` null, and
  `execution = full`.
- `repo_reality_citing_documents_only`: a finding with `class = repo-reality`
  whose `evidence` list is empty or contains only `plan.path` or
  `design.path`.

### 7. Privacy boundary

Records hold repository-relative paths, a directory name, hashes, enum values,
integers, timestamps, and short paraphrases. They never hold absolute paths,
document or source text, prompts, transcripts, command output, environment
values, or credentials. The CLI enforces shape and length; it does not detect
secrets. Records are local files and are not a signed audit log.

### 8. Errors

Every failure writes one JSON line to stderr and exits 2:

```json
{"error":{"code":"<code>","message":"<single line, at most 300 chars>"}}
```

Codes: `invalid-arguments`, `schema-invalid`, `run-not-found`,
`not-git-repository`, `outside-repository`, `already-finished`,
`evidence-home-unwritable`. `finish` and `abandon` on a run that is already
`completed` or `abandoned` return `already-finished`; `outcome` on a run that
is not `completed` returns `schema-invalid`.

### 9. Versioning

`pre-sdd-review` moves to 2.0.0: the command, installation, and schema all
change incompatibly. `release.toml` is the version source and `SKILL.md`
`metadata.version` mirrors it. The CHANGELOG 2.0.0 entry lists removed
commands, the new invocation, schema 2, and the reviewer-protocol sentence.

## Package and repository impact

| Area | Change |
| --- | --- |
| `skills/pre-sdd-review/evidence/` | Add `evidence.py`; remove `install.py` and `pre_sdd_review_evidence/`; shorten `README.md` to invocation, commands, privacy, limits |
| `skills/pre-sdd-review/SKILL.md` | Rewrite the evidence section per Decision 5; bump `metadata.version` and `updated_at` |
| `skills/pre-sdd-review/references/reviewer-protocol.md` | Add the repo-reality evidence sentence |
| `skills/pre-sdd-review/README.md`, `README.en.md` | Replace installer and evidence text; add one paragraph telling an agent to read `summary` starting from `anomalies` and `chains` |
| `skills/pre-sdd-review/CHANGELOG.md`, `release.toml` | 2.0.0 |
| `scripts/release.py` | New payload list (`evidence/README.md`, `evidence/evidence.py`); `--version` smoke runs `python3 evidence/evidence.py --version` from the extracted payload and compares the canonical line |
| `scripts/lib/verification.py` | No change; test discovery path is unchanged |
| `tests/products/pre-sdd-review/test_contract.py` | New payload set; new SKILL.md and protocol hash pins; evidence case wording; offline AST contract applied to `evidence/evidence.py` |
| `tests/products/pre-sdd-review/cases.json` | `evidence-resolution-blocked` becomes "design unresolved: omit `--design`, record null, return BLOCKED"; `evidence-combined-sdd-outcome` becomes "outcome is an optional post-SDD label, not a controller duty"; invocation strings updated |
| `tests/products/pre-sdd-review/evidence/` | Replace seven files with `test_evidence.py` and a small `support.py` if needed |
| `tests/repository/test_public_docs.py` | Replace pins for `--bin-dir`, `command -v pre-sdd-review-evidence` with pins for the `evidence.py` invocation and `~/.pre-sdd-review/` |
| `docs/maintainers/products/pre-sdd-review/*.md` | Evidence paragraphs in contract, testing, release, compatibility |
| `docs/users/{ko,en}/{installation,verification,safety-and-privacy}.md` | Evidence paragraphs |

Outside the repository, on the owner's machine, the launcher
`~/.local/bin/pre-sdd-review-evidence` becomes dead and may be deleted; the
schema 1 receipts under `~/.pre-sdd-review/runs/2026/` are ignored by the new
CLI and may be kept or deleted. Neither step is part of the repository change.

## Verification design

All verification is offline and provider-free, run through the existing
`unittest` stages.

`tests/products/pre-sdd-review/evidence/test_evidence.py` creates a temporary
Git repository with a plan and design and covers:

- `--version` output bytes and rejection of extra arguments.
- `start` with and without `--design`; absolute and relative plan arguments;
  plan outside the repository; `--repo` not in a Git repository; skill root
  with a missing or malformed SKILL.md.
- `finish` happy path with two findings; each invariant in Decision 3
  failing individually; wrong stdin keys; `--repo` in a different repository;
  second `finish` returns `already-finished`; end hashes and HEAD change
  after a commit between `start` and `finish`.
- `abandon` with each reason and with an invalid reason; on a completed run.
- `outcome` on completed run, overwrite, `false-ready` on a REVISE run
  rejected, on a pending run rejected.
- `show` prints the file verbatim.
- `summary` on a mixed set of records (completed, abandoned, pending, a
  schema 1 file in a nested directory, a non-JSON file) produces the exact
  documented keys, correct chains, repeated patterns, and each of the four
  anomalies; `--repo` and `--last` filter before aggregation.
- Every record and error is canonical single-line JSON; records are `0o600`;
  no absolute path appears in any record.
- A record above 64 KiB is rejected at `finish`.

`test_contract.py` keeps the AST-based offline contract (no network modules,
no provider identifiers, `subprocess` only for `git`) and applies it to
`evidence.py`. The SKILL.md and reviewer-protocol hash pins are updated to the
final documents.

`scripts/release.py check|build|verify-download --product pre-sdd-review` must
pass with the new payload.

## Rollout

1. Write the new script and its tests; make the evidence stage green.
2. Rewrite SKILL.md, reviewer protocol, and skill docs; update contract tests,
   cases, hash pins, and release payload; make the contract and repository
   stages green.
3. Delete the old package, installer, and tests.
4. Run `python3 scripts/verify.py --skill pre-sdd-review` and
   `python3 scripts/release.py check --product pre-sdd-review`.
5. Optionally run one real review with the new recorder from Codex and one
   from Claude Code, then `summary`, to confirm the round trip on real data.
   This does not change host support claims.

## Success criteria

- `skills/pre-sdd-review/evidence/` contains exactly `README.md` and
  `evidence.py`; `evidence.py` is under 600 lines and imports only the
  standard library.
- `tests/products/pre-sdd-review/evidence/` is under 800 lines.
- A real run from any host records `client.id`, `client.model`, `design`
  (or null with a BLOCKED verdict), `execution`, and findings without a
  parser rejecting a plan the controller accepted.
- `summary` answers, without further file reads: verdict distribution,
  abandoned-run share and reasons, attempts per plan, repeated finding
  patterns, outcome coverage, and the four anomaly lists.
- Recording an outcome costs one command with one label.
- `python3 scripts/verify.py --profile full` and `--profile windows-portable`
  pass; `release.py check` passes for `pre-sdd-review` 2.0.0.
- No review-semantics text in SKILL.md changed except the evidence section;
  the reviewer protocol changed by exactly one sentence.
