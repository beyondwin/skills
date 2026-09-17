# Changelog

All notable changes to this product are documented in this file.

## Unreleased

No entries yet.

## 3.0.0 - 2026-09-18

### Breaking

- Grok now requires value-taking `--disallowed-tools` and `--deny` options.
  Workers remove `search_tool,use_tool` and deny `MCPTool(*)`.

- Cursor resolution now requires the CLI to declare headless print (`--print`
  or `-p`), `--trust`, `--auto-review`, `--sandbox`, a confirmed `stream-json`
  output format, and at least one Grok model id returned by a successful model
  list. A Cursor CLI that declares none of `--auto-review`, `--sandbox`, and
  the structured output format now resolves as `available: false` with
  `reason: missing_flags` instead of falling back to `--force`/`--yolo`.
  Blanket approval is gone and no flag brings it back.
- Grok resolution reports the same `available: false` shape; `reason` is one of
  `not_found`, `identity_mismatch`, `missing_flags`, or `no_grok_model`.
- Implementer attempts must be launched with `scripts/run_worker.py run`.
  Hand-composed provider commands and per-run execution scripts are no longer
  part of the contract.
- The run's current state lives in exactly one delimited block at the top of
  the Superpowers SDD ledger. Separate controller state files are prohibited.
- Windows is unsupported; product CLIs refuse it.

- Cursor's unavailable `reason` splits the single `no_grok_model` into three.
  `no_model_list` means no declared listing command returned a listing;
  `model_list_unreadable` means one was returned that no model id could be read
  from; `no_grok_model` keeps its name for the one case it was ever true of —
  ids were read and none is Grok. Only the last says anything about which
  models exist. A controller that matched on `no_grok_model` for any of the
  three now has to match the reason it means.

### Added

- `run.json.session_id` is copied from the worker stream as soon as it appears,
  including while `state` is `running`. A later stream id does not replace it.
- SIGTERM to the runner uses the existing `interrupted` record (exit 130) and
  does not kill the worker tree.
- `run_worker.py status` adds `pid_alive` and a bounded tools index (read
  paths, search patterns, shell exit codes and commands). It still does not
  include log bodies or judge role compliance.

- `run_worker.py status` adds `stale` and `session_id_in_log`. `stale` is true
  when the record says `running` and the process is gone — the judgement SKILL.md
  asked a controller to make, made once here instead. `session_id_in_log` carries
  the session the worker reported when the record holds none, so an attempt whose
  runner was killed before it could write one is resumable rather than re-run from
  scratch. Neither field is written to `run.json`; `status` still writes nothing,
  and `session_id` keeps reporting the record's own value.

- Model listings are read without their colour. Escape sequences are stripped
  before a line is parsed, and every probe runs with `FORCE_COLOR=0`,
  `NO_COLOR=1` and `CLICOLOR=0` while inheriting the rest of the environment.
  The trigger is an inherited `FORCE_COLOR`: `cursor-agent` reads it before it
  looks for a terminal, so an orchestrator that exports it makes the CLI colour
  a pipe, and `NO_COLOR`, `CLICOLOR` and `TERM=dumb` do not override it. Every
  id then failed to parse and the resolver answered `no_grok_model` for models
  it had just been shown. Both layers are independent: the environment request
  stops the colour, and the parser reads the ids even when something else forces
  colour anyway. `parse_listed_ids(text)` is the listing-wide reader
  `parse_model_ids` filters.

- Grok workers disable imported Cursor/Claude MCP discovery in their own
  environment on both new and resumed attempts. Global settings and Cursor
  execution are preserved.

- `scripts/extract_task.py <plan-file> --heading "<heading text without #>"
  --output <file>` copies one task section out of a plan. Exit 0 is success,
  2 is a file or argument error, and 3 means the section is absent,
  duplicated, or empty. It never overwrites an existing output file.
- `scripts/run_worker.py run` launches one attempt into a new directory under
  the worktree's `.superpowers/` and preserves `brief.md`, `dispatch.md`,
  `worker.jsonl`, `stderr.log`, `run.json`, and `report.md`. The worker writes
  `report.md`; the runner never does. The runner never prepares or cleans up
  the Grok sandbox profile.
- `scripts/run_worker.py status` reads one attempt. A log window needs
  `--stream` and is bounded: 2048 bytes by default, 8192 maximum, with the
  whole JSON answer capped at 64 KiB.
- `resolve_backend.py --json` adds `launch` (`cwd_flag`, `prompt_flag`,
  `effort_flag`, `output_format`, or null when unavailable) and `model_ids`.
- `references/current-state.md` holds the ledger current-state block template.
- `run.json` and `status` carry `session_id` from the worker's own stream,
  including while `state` is `running`, so `--resume` can use an id the
  previous run actually reported instead of always falling back to a fresh
  worker.
- `run.json` records `skill_version` from the installed skill's `release.toml`.
  A missing or unreadable version refuses the launch before the attempt
  directory is created. Older schema 2 records without the field stay readable.
- `scripts/run_worker.py run --timeout <seconds>` bounds one attempt's
  wall-clock, defaulting to 3600; `0` waits indefinitely. On expiry the runner
  sends SIGTERM, waits ten seconds, then SIGKILL, records `state: timed_out`
  with the real `exit_code`, and returns 124. Descendants the worker started
  are not pursued, for the same reason the interrupt path leaves the process
  tree alone.

### Changed

- `run.json` records process facts only, at `schema_version` 2. `state` is one
  of `starting`, `running`, `exited`, `launch_failed`, `interrupted`, or
  `timed_out`, which is process state and not task state. Process exit 0 is
  still not a clean DONE.
- The wrapper exit follows the worker's exit. A POSIX signal returns
  `128 + signal` while `run.json.exit_code` keeps the real negative return
  code; a launch failure is 2 and a handled interrupt is 130. Exit 2 is
  ambiguous between a launch failure and a worker that legitimately exited 2,
  so `run.json.state` is the discriminator; if the attempt directory is absent,
  or present without `run.json`, the launch was refused before the attempt was
  created and the `BLOCKED:` line on stderr is the reason. A timeout is 124.
- Requested and configured effort are recorded separately. Cursor carries
  effort in the model id, so `run_worker.py run` refuses a `--model` whose
  declared effort contradicts `--effort`, and `configured_effort` holds the
  effort read off the id. An id that declares no effort is still accepted and
  leaves `configured_effort` null, because the applied effort is then genuinely
  unknown.
- There is no automatic retry in any helper.
- A change to the shared product source applies to new runs only. No run in
  progress is converted or restarted automatically; resume an existing run
  explicitly after checking its ledger record and its processes.
- Product README now matches the measured macOS host/worker table instead of
  saying all four combinations are `not_measured`.
- Default `status` and the contract now describe `pid_alive` and the bounded
  tools index in the same terms the runner actually returns.

- Every brief carries the plan's run-wide constraints in full under a
  `Global constraints` heading, fix rounds included, instead of "relevant
  constraints" chosen per task. A worker cannot read the plan, so a constraint
  left out of the brief does not exist for it and the review reports it later as
  a defect the worker had no way to avoid.

- The native reviewer has a stated fallback order when its host cannot be
  reached: wait for the limit to clear, then another native path on the same
  orchestrator model, then stop and ask. Only the user's answer moves a review
  off the native host, and the implementer's own model family is the last
  choice even then. The host, model, and reason are recorded in the
  current-state block and on every review line they produced.

- The current-state block names when it is rewritten — before each dispatch, on
  task completion, on a fix round opening or closing, on a ruling that changes
  the run, and on a scope change. A field the evidence on disk contradicts is a
  defect to fix before the next dispatch, and a superseded value is replaced
  rather than appended.

### Fixed

- A recursive JSON line in `worker.jsonl` is skipped by the tools index instead
  of failing the whole `status` query.

## 1.1.1 - 2026-09-12

### Fixed

- Grok sandbox config rewrite no longer requires POSIX `fchmod`, so an existing `sandbox.toml` can be prepared and restored on Windows.
- Backend resolution runs Windows `.cmd`/`.bat` PATH wrappers through `cmd.exe`, so identity probes work for batch launchers.

## 1.1.0 - 2026-09-11

### Added

- A bundled Claude Code reviewer agent raises review effort to XHigh without a new install step; the existing skill link carries it.

### Changed

- Native reviewers follow the active orchestrator model, and effort is High unless a named trigger in the changed paths calls for XHigh. This overrides generic SDD model selection.

### Fixed

- Worker dispatch supplies complete task context and repeats the boundary against retrieving the full plan, including through shell and search tools.
- Completion checks compare tool-call and results evidence with the worker's required scope-deviations report; missing evidence cannot count as verified compliance.
- Test reports preserve full wrapper commands and distinguish test exits from wrapper exits.
- Define Search paths as content-search boundaries; allow filename-only inspection within the worktree and direct reads of task-needed repository ignore/build/test configuration.
- Align worker, dispatch and reviewer rules so permitted inspection alone is reported without a scope concern; full-plan content and secrets remain prohibited.

## 1.0.1 - 2026-09-11

### Fixed

- Grok dispatch prepares a temporary worktree Git write profile so the worker can commit, then restores or removes the generated configuration after exit.
- Worker exit code 0 no longer counts as task completion when the report is blocked, missing, or unclear.

### Changed

- Grok backend resolution now requires the sandbox, rules, and disabled web-search flags.

## 1.0.0 - 2026-09-11

### Changed

- Resolver treats Grok identity as Grok Build, xAI Grok, or a line that starts with `grok `, not any substring `grok `.

### Notes

- First standalone release. Superpowers SDD stays the workflow owner; this skill overrides implementer dispatch only.
- No GitHub tag or GitHub Release is created.
