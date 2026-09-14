# Implementer dispatch

## Resolve the backend

From the loaded skill root:

    python3 "<skill-root>/scripts/resolve_backend.py" --backend <cursor|grok|c|g> --json

Do not launch a worker from the resolver. Parse one JSON object with
`backend`, `available`, `executable`, `identity`, `argv_prefix`, `reason`,
`launch`, and `model_ids`.

If `available` is false, stop and report `reason`, which is one of
`not_found`, `identity_mismatch`, `missing_flags`, or `no_grok_model`.
`launch` is then null and `model_ids` is empty. Do not fail over.

When `available` is true:

- Grok: `argv_prefix` is `[executable, --no-plan, --no-subagents,
  --disallowed-tools, search_tool,use_tool, --deny, MCPTool(*),
  --always-approve, --disable-web-search, --sandbox, <workspace>]`. `launch`
  gives `cwd_flag` `--cwd`, `prompt_flag` `--prompt-file`, `--single`, or
  `-p`, `effort_flag` `--reasoning-effort` or `--effort`, and `output_format`
  `streaming-messages-json`. `model_ids` is empty: Grok takes no model
  argument.
- Cursor: `argv_prefix` is `[executable, --print` or `-p`, `--trust`,
  `--auto-review`, `--sandbox`, `enabled]`. `launch` gives `cwd_flag`
  `--workspace` or `--cwd`, `prompt_flag` null, `effort_flag` null, and
  `output_format` `stream-json`. `model_ids` holds the confirmed Grok model
  ids; pass one of them to the runner as `--model`.

Choose that id by effort, not by position: the order is the account's own
listing order and can change. Strip one trailing `-fast` first — it is a
serving variant, not an effort — and take the `model_ids` entry whose final
segment then equals the requested effort. That is the same reading
`model_effort()` performs in `run_worker.py`, which refuses a `--model` whose
declared effort contradicts `--effort`; there is one rule here, not two. Among
several matches prefer the highest version, comparing the dot-separated
components as numbers so that `4.10` outranks `4.9`, and then the entry without
`-fast`. If no entry declares the requested effort, report that the requested
effort is unavailable on this account rather than substituting a different one.

Use the `output_format` value this host's resolver returned. Do not hardcode a
format per backend, and do not add a second `--sandbox` or a second approval
flag: the resolved prefix already carries the headless and approval flags this
CLI actually declares.

## Grok worker tool boundary

Grok must declare value-taking `--disallowed-tools` and `--deny`; otherwise
resolution returns `missing_flags`. The prefix removes `search_tool` and `use_tool`, and denies `MCPTool(*)`.
Do not add `Agent` or `task` to the denylist: the measured CLI also removes
background shell output/termination tools with that group. `--no-subagents`
and the worker rule remain, but toolset-level subagent exclusion is not
claimed. MCP filters do not claim shell or filesystem isolation.

The runner sets `GROK_CURSOR_MCPS_ENABLED=0` and
`GROK_CLAUDE_MCPS_ENABLED=0` only in the Grok child's environment, on both new
and resumed attempts. This prevents imported Cursor/Claude MCP startup from
adding unrelated handshake failures. It does not modify user configuration,
credentials, or session storage. Native Grok and plugin MCP initialization may
still happen. Init/inspect server listings can still include configured
servers; they do not prove a connection or a tool invocation. Inspect the
actual stderr and tool calls/results. Other startup warnings remain visible.
Cursor keeps its environment and existing approval/sandbox policy.

## Build the brief

Before dispatch, use SDD's task-brief output and supply all decisions and
task reference paths needed for this task. Extract the task section from the
plan in the controller:

    python3 "<skill-root>/scripts/extract_task.py" <plan-file> --heading "Task P1: 상태 저장" --output <section-file>

`--heading` is the complete heading text without the leading `#` marks. Exit 0
is success, 2 is a file or argument error, and 3 is a section-selection error:
the heading is absent, duplicated, or has an empty body. The command never
overwrites an existing output file, so write each extraction to a new path.

Include relevant constraints from the plan in the brief; do not send the plan
itself as a reference. Source and test inspection remains available. When the
brief lacks a required decision, complete it in the controller rather than ask
the worker to recover it from the plan. Add `Search paths:` with concrete
source/test file or directory paths to the brief. Keep planning documents out
of that list. The worker starts with direct reads of named files and targets
content searches at these paths; a glob without a target path can still search
the whole repository.
`Search paths` limits content searches. Filename-only listings inside the
current worktree, including its root, and direct reads of repository
ignore/build/test configuration needed for this task are allowed inspection.
These actions alone are not scope deviations. They never permit reading
full-plan content, credentials, or secrets.

Split verification in the brief under two headings. `Worker checks` are the
local commands the worker runs and reports with actual exit codes.
`Host checks` are the ones only this host can run; the worker names the
outstanding ones in `NEEDS_CONTEXT` or `BLOCKED` instead of claiming them.

The runner writes this reading boundary into every dispatch, new or resumed,
alongside the brief and report paths (it also remains in the worker rules):

> Read the brief first. Use its requirements and explicitly listed task
> references. The controller owns the full plan; do not read it or follow
> links to it, including through shell/search tools. Missing decisions go
> back as NEEDS_CONTEXT. Read named source/test files directly first; content
> searches must target the brief's Search paths, not the whole workspace.
> Within this worktree, filename-only listings and direct reads of repository
> ignore/build/test configuration needed for this task are allowed and are
> not scope deviations. Never read full-plan content, credentials, or secrets
> through these inspections. Report actual scope deviations even if tests pass.

## Order of one attempt

Complete brief → Grok profile prepare → run → wait on the host's job → the
status windows you need → confirm the worker and anything it started have
exited → Grok cleanup → the existing native review.

Never start a new worker before the previous cleanup has finished on the same
journal path.

For Grok, immediately before starting the worker, prepare its worktree
profile:

    python3 "<skill-root>/scripts/prepare_grok_sandbox.py" prepare --worktree "<worktree>" --state "<evidence-dir>/grok-sandbox.json"

`<skill-root>`, `<worktree>`, and `<evidence-dir>` are absolute paths already
established by SDD, not requests for more user input. If preparation fails, do
not start the worker. Read `profile` out of the successful JSON and pass it to
the runner as `--sandbox-profile`; the runner substitutes it for the resolved
prefix's sandbox value itself. `run_worker.py` never prepares or cleans up.

## Run

    python3 "<skill-root>/scripts/run_worker.py" run --backend <c|cursor|g|grok> --worktree <worktree> \
        --brief <brief-file> --attempt-dir <new-attempt-dir> --effort <high|xhigh> \
        [--model <confirmed-grok-id>] [--resume <known-id>] [--sandbox-profile <prepared-profile>] \
        [--timeout <seconds>]

`--attempt-dir` must be a new directory under the worktree's `.superpowers/`.
The runner writes six files there: `brief.md`, `dispatch.md`, `worker.jsonl`
(raw stdout), `stderr.log`, `run.json`, and `report.md`, which the worker
writes itself — the runner never writes the report. Grok receives the worker
rules through `--rules` and Cursor receives them inline in the dispatch text;
the controller does not compose either.

`--model` and `--sandbox-profile` are each required for one backend and
rejected for the other. Grok requires `--sandbox-profile <prepared-profile>`
and rejects `--model`, because it selects its own model. Cursor requires
`--model <confirmed-grok-id>` from the resolver's `model_ids` and rejects
`--sandbox-profile`, because it uses its own sandbox mode.

Pass `--resume` only with a session ID the previous run actually reported. The
runner reads that ID out of the worker's own stream and records it as
`run.json.session_id`, which the `status` output carries too; take it from
there rather than from the raw log. It is null when the provider's stream
reported none. If a fix round has no reported session ID — `session_id` null,
`Worker session: none` in the current-state block — use the SDD fallback: a
fresh worker plus the previous attempt's `report.md` named in the brief. Never
guess an ID.

`--timeout <seconds>` bounds one attempt's wall-clock. It defaults to 3600, and
`--timeout 0` waits without a bound. When it fires the runner sends the worker
SIGTERM, waits ten seconds, kills it if it is still alive, records `state`
`timed_out` with the real `exit_code` and the session ID the stream reported,
and exits 124. Only the worker process itself is signalled. It shares the
controller's process group so that a terminal interrupt reaches it, so
descendants the worker started are not pursued and no process tree is cleaned
up here. Confirm those have exited yourself before cleanup.

Do not pass `--worktree` to the provider CLI. Do not pass `--continue`. Do not
copy host credentials or environment values into the brief or the dispatch.

`run.json` holds process facts only: `schema_version` 2, `backend`,
`identity`, `model`, `worktree`, `attempt_dir`, `brief_sha256`, `resume_id`,
`session_id`, `requested_effort`, `configured_effort`, `skill_version`, `state`,
`pid`, `exit_code`, `started_at`, `ended_at`, `error`. `skill_version` is the
installed skill's `release.toml` version, written once at start. A missing or
unreadable version refuses the launch before the attempt directory is created.
Older schema 2 records without the field stay readable. `state` is one of
`starting`, `running`, `exited`, `launch_failed`, `timed_out`, or `interrupted`.
That is process state, not task state; process exit 0 is not a clean DONE.

The wrapper exit follows the worker's exit. A POSIX signal returns
`128 + signal` while `run.json.exit_code` keeps the real negative returncode.
A launch failure is 2, a handled controller interrupt is 130, and an attempt
ended by its own timeout is 124. A handled interrupt records the exit it
recovered, which may be none, and `run.json` does not say which of two routes
reached that record: an interrupt while the runner was only waiting signals
nothing at all and leaves the worker running, while an interrupt during a
timeout's own SIGTERM and SIGKILL arrives after the worker has been signalled
and is probably dead. Confirm the worker and anything it started have exited
yourself either way, before Grok cleanup. Exit 2 is ambiguous between a
launch failure and a worker that legitimately exited 2, so read
`run.json.state` to tell them apart; if the attempt directory is absent, or
present without `run.json`, the launch was refused before the attempt was
created and the `BLOCKED:` line on stderr is the reason.

There is no automatic retry. Cursor carries its effort in the model ID rather
than on a flag, so the runner refuses a `--model` whose declared effort
contradicts `--effort`, and `configured_effort` holds the effort read from the
ID. When the ID declares no effort, `configured_effort` stays null and the
applied effort is genuinely unknown; record it as unknown rather than as the
requested value.

Known limitation: the worker rules and the Cursor dispatch text are
multi-line, and a `cmd.exe` command line cannot carry a newline, so launching
through an npm-style `.cmd` shim is recorded as a launch failure instead of
being silently mangled. Do not route around it. A native Win32 image is
launched with a quoted command line so those newlines survive.

## Watch

Wait on the host's shell job without short polls. Codex `wait_agent` is only
for native reviewers.

    python3 "<skill-root>/scripts/run_worker.py" status --attempt-dir <attempt-dir>
    python3 "<skill-root>/scripts/run_worker.py" status --attempt-dir <attempt-dir> --stream stdout|stderr --offset N --max-bytes N

`status` is read-only and interprets nothing. The default answer is metadata,
log sizes, and whether `report.md` exists — never a log body. A window needs
`--stream`; it defaults to 2048 bytes with a maximum of 8192, and the whole
JSON answer is capped at 64 KiB. Read the bounded windows you need. Do not
print a raw log wholesale into this session, and do not write a new execution
script for a run.

`pending_bytes > 0` means a UTF-8 character is only half written. Wait on the
host's job for new bytes; do not re-query the same offset in a short loop.

## Clean up

For Grok, confirm the worker and any work it started have exited, then clean
up after every success or failure:

    python3 "<skill-root>/scripts/prepare_grok_sandbox.py" cleanup --worktree "<worktree>" --state "<evidence-dir>/grok-sandbox.json"

Do not clean up while a process is still running or overlap it with a new
worker. New tasks and resumed fix rounds use the same prepare, launch, exit,
and cleanup order. If cleanup fails, do not overwrite other files to repair
it; record the remaining difference and state path in the ledger.

## Evidence

`worker.jsonl` is the CLI's tool-call/results stream and stays local and
uncommitted with the rest of the attempt directory. Preserve test commands and
their actual exits. If the trace is unavailable or incomplete, record role
compliance as UNVERIFIED. A final message alone is not a tool trace.

Record the attempt path and the confirmed session ID in the current-state
block described by `references/current-state.md`. `run.json` stays the
attempt's process record; the ledger stays the run's record.

Do not pass `--plugin-dir`. Do not approve extra MCP servers.
