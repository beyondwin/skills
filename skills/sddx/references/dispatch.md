# Implementer dispatch

## Controller procedure

1. `python3 "<skill-root>/scripts/resolve_backend.py" --backend <id> --json`.
   If `available` is false, stop and report `reason`. Do not switch backends.
2. Run Superpowers `bash scripts/sdd-workspace PLAN_FILE` and keep that
   directory. Write extract outputs and attempt dirs under it with new names.
   Do not reimplement `sdd-workspace`.
3. Do not run Superpowers `task-brief` or `task-start`. Extract with:

       python3 "<skill-root>/scripts/extract_task.py" <plan-file> --heading "<heading>" --global-constraints --output <new-path>

   Then add `Search paths`, `Worker checks`, `Host checks`, and task
   decisions. If extract exits 3 because Global Constraints are missing,
   duplicated, or empty, record that in the ledger and do not dispatch.
   A brief with no plan heading of its own (a fix round, a continuation)
   starts from the constraints section alone:
   `extract_task.py <plan-file> --heading "Global Constraints" --output <new-path>`.
   If the plan points at another plan's constraints, extract from that plan.
   Do not copy constraints by hand or from a cached `/tmp` file.
4. Grok: `prepare` → `run_worker.py run` → wait on the host job → the
   `status` windows you need → confirm the worker and its descendants have
   exited → `cleanup`. Cursor: the same run/status path without
   prepare/cleanup.
5. Process exit 0 is not DONE. Judge from the report, actual test exits,
   commits, the tools index, and native review. Do not paste the log.

## Resolve the backend

From the loaded skill root:

    python3 "<skill-root>/scripts/resolve_backend.py" --backend <cursor|grok|c|g> --json

Do not launch a worker from the resolver. Parse one JSON object with
`backend`, `available`, `executable`, `identity`, `argv_prefix`, `reason`,
`launch`, and `model_ids`.

If `available` is false, stop and report `reason`, which is one of
`not_found`, `identity_mismatch`, `missing_flags`, `no_model_list`,
`model_list_unreadable`, `no_grok_model`, or `no_grok_4_7`. `launch` is
then null and `model_ids` is empty. Do not fail over.

`no_grok_model` means IDs were read and none is Grok. `no_grok_4_7` means
Grok IDs were read and none is Grok 4.7 — do not substitute 4.6 or 4.5.
`no_model_list` means no listing was obtained and `model_list_unreadable`
means one was obtained that no ID could be read from — both are faults in
the reading, so do not report a model as missing and do not rule around a
model that is still there.

When `available` is true:

- Grok: `argv_prefix` is `[executable, --no-plan, --no-subagents,
  --disallowed-tools, search_tool,use_tool, --deny, MCPTool(*),
  --always-approve, --disable-web-search, --sandbox, <workspace>]`. `launch`
  gives `cwd_flag` `--cwd`, `prompt_flag` `--prompt-file`, `--single`, or
  `-p`, `effort_flag` `--reasoning-effort` or `--effort`, and `output_format`
  `streaming-messages-json`. `model_ids` is `grok-4.7` only. Pass that id
  as `--model`. Effort still goes on `effort_flag`. Do not pass
  `grok-4.7-build-fast`, `grok-4.6`, or `grok-4.5`.
- Cursor: `argv_prefix` is `[executable, --print` or `-p`, `--trust`,
  `--auto-review`, `--sandbox`, `enabled]`. `launch` gives `cwd_flag`
  `--workspace` or `--cwd`, `prompt_flag` null, `effort_flag` null, and
  `output_format` `stream-json`. `model_ids` holds confirmed Grok 4.7 ids
  with no trailing `-fast` (`grok-4.7-high`, `grok-4.7-xhigh`). Cursor Grok
  4.6, 4.5, and every `-fast` id are already dropped. Pass one of those ids
  to the runner as `--model`.

Choose that Cursor id by effort, not by position: the order is the account's
own listing order and can change. Take the `model_ids` entry whose final
segment equals the requested effort. That is the same reading
`model_effort()` performs in `run_worker.py`, which refuses a `--model` whose
declared effort contradicts `--effort`; there is one rule here, not two. Do
not pass a `-fast` id. If no entry declares the requested effort, report that
the requested effort is unavailable on this account rather than substituting
4.6, 4.5, a `-fast` variant, or a different effort.

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

Do not run Superpowers `task-brief` or `task-start`. Extract the task
section from the plan in the controller:

    python3 "<skill-root>/scripts/extract_task.py" <plan-file> --heading "Task P1: 상태 저장" --global-constraints --output <section-file>

`--heading` is the complete heading text without the leading `#` marks. Exit 0
is success, 2 is a file or argument error, and 3 is a section-selection error:
the heading is absent, duplicated, or has an empty body. Missing, duplicate, or
empty `Global Constraints` / `Global constraints` is also exit 3, and the
controller must not dispatch. The command never
overwrites an existing output file, so write each extraction to a new path.
The output path is a new file under the Superpowers `sdd-workspace` plan
directory.

`extract_task.py --global-constraints` prepends the plan's `Global Constraints`
or `Global constraints` section. The controller does not shrink it. Do not
hand-copy those constraints. A worker cannot read the plan, so a constraint
left out of the brief does not exist for it, and the review finds it afterwards
as a defect the worker had no way to avoid. Task-specific constraints go with
the task; do not send the plan itself as a reference. Source and test
inspection remains available. When the brief lacks a required decision,
complete it in the controller rather than ask the worker to recover it from
the plan. Add `Search paths:` with concrete
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
Run a task's Host checks before that task's review, not batched at the end of
the plan.

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

`--attempt-dir` must be a new directory under the plan directory from Superpowers
`sdd-workspace` (already inside the worktree `.superpowers/sdd/<plan>/` tree),
never a shared flat `.superpowers/` name.
Create its parent (for example `<plan-dir>/worker-attempts/`) before the first
run; the runner refuses a missing parent. Do not pipe `run` or `status` through
`tail` or another filter that hides the exit code.
The runner writes six files there: `brief.md`, `dispatch.md`, `worker.jsonl`
(raw stdout), `stderr.log`, `run.json`, and `report.md`, which the worker
writes itself — the runner never writes the report. Grok receives the worker
rules through `--rules` and Cursor receives them inline in the dispatch text;
the controller does not compose either.

`--sandbox-profile` is required for Grok and rejected for Cursor. `--model`
is required for both, and it must be one of that backend's `model_ids`.
Grok requires `--sandbox-profile <prepared-profile>` and `--model grok-4.7`.
Cursor requires `--model <grok-4.7-effort-id>` from the resolver's
`model_ids` and rejects `--sandbox-profile`, because it uses its own sandbox
mode.

Pass `--resume` only with a session ID the previous run actually reported. The
runner copies the first reported id from the worker's own stream into
`run.json.session_id` as soon as the stream has it, including while `state` is
`running`, and never replaces it. Read that id from `status` — not by dumping
the log. `status` still mirrors the record; it does not invent an id from the
log when the record is missing. It is null when the provider's stream reported
none. If a fix round has no reported session ID — `session_id` null, `Worker
session: none` in the current-state block — use the SDD fallback: a fresh
worker plus the previous attempt's `report.md` named in the brief. Never guess
an ID.

`--timeout <seconds>` bounds one attempt's wall-clock. It defaults to 7200, and
`--timeout 0` waits without a bound. When it fires the runner sends the worker
SIGTERM, waits ten seconds, kills it if it is still alive, records `state`
`timed_out` with the real `exit_code`, keeps the first session ID already
copied (or scans once more if that field is still null), and exits 124. Only
the worker process itself is signalled. It shares the controller's process
group so that a terminal interrupt reaches it, so descendants the worker
started are not pursued and no process tree is cleaned up here. Those
processes (for example a backgrounded shell or a build daemon) can outlive the
worker, so confirm and end them by pid yourself before cleanup.

A worker that writes no stdout at all within 300 seconds of starting, new or
resumed, is ended the same way, even under `--timeout 0`: `timed_out`, exit
124, `error` `the worker wrote no output within 300 seconds`. When that is the
error, do not raise `--timeout` and do not resume that session; dispatch a
fresh worker with a continuation brief that names the previous `report.md`
and the commits already made. The deadline watches only the first byte: a
worker that printed and then stalls is bounded only by `--timeout`.

Do not pass `--worktree` to the provider CLI. Do not pass `--continue`. Do not
copy host credentials or environment values into the brief or the dispatch.

There is no automatic retry. Cursor carries its effort in the model ID rather
than on a flag, so the runner refuses a `--model` whose declared effort
contradicts `--effort`, and `configured_effort` holds the effort read from the
ID. When the ID declares no effort, `configured_effort` stays null and the
applied effort is genuinely unknown; record it as unknown rather than as the
requested value.

Known limitation: the supported OS is macOS. Windows is refused at the product
CLIs. Do not add a Windows launch path or treat a quoted Win32 command line as
a live transport.

## Watch

Wait on the host's shell job without short polls. Codex `wait_agent` is only
for native reviewers.

    python3 "<skill-root>/scripts/run_worker.py" status --attempt-dir <attempt-dir>
    python3 "<skill-root>/scripts/run_worker.py" status --attempt-dir <attempt-dir> --stream stdout|stderr --offset N --max-bytes N

`status` is read-only. Ask it instead of dumping the log.

An attempt is over when `state` is not `running` and `pid_alive` is false; a
worker can still be writing `report.md` after its record changed. Do not start
the next attempt while the previous attempt's `pid_alive` is true.
`run.json.pid` and `pid_alive` are the worker's. To stop an attempt, send
SIGTERM to the runner: the host job's own pid (for example `$!` of the
backgrounded `run` command), or the parent of the recorded pid (`ps -o ppid=
-p <pid>`). Do not signal `run.json.pid` itself, and never `pkill -f`, which
can miss the worker or hit another run. If that parent is pid 1, the runner is
already gone and the worker is an orphan; only then stop the worker by
`run.json.pid` (SIGTERM, then SIGKILL if it stays).

Read the bounded windows you need. Do not print a raw log wholesale into this
session, and do not write a new execution script for a run. Do not re-query
the same offset in a short loop.

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
block described by `references/current-state.md`. Take the id from `status`
while the attempt is still running; do not wait for exit and do not parse
the log for it. `run.json` stays the attempt's process record; the ledger
stays the run's record.

Do not pass `--plugin-dir`. Do not approve extra MCP servers.

## Runner already does this

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
A launch failure is 2, a handled runner interrupt is 130, and an attempt
ended by its own timeout is 124. On SIGTERM or Ctrl-C the runner records
`interrupted` at once, then ends the worker process itself the way a timeout
does (SIGTERM, ten seconds, SIGKILL) and records the exit it recovered; a
second interrupt during that wait, or an interrupt during a timeout's own wait,
goes straight to SIGKILL. That `exit_code` is `null` when the worker could not
be confirmed ended, so check `pid_alive` before cleanup. The `error` is
`the runner was interrupted (SIGTERM or Ctrl-C)`: the runner cannot know who
sent the signal, so it does not say. SIGTERM to the worker remains
`exited` (or `timed_out` when the runner sent it) with the negative returncode.
SIGKILL still cannot write a terminal state. An interrupt that lands while the
worker process is being started can leave `run.json` at `starting` with no
pid; then check the host for a stray worker before starting another attempt.
Confirm the worker and anything it started have exited yourself either way,
before Grok cleanup. Exit 2 is ambiguous between a launch failure and a worker
that legitimately exited 2, so read `run.json.state` to tell them apart; if
the attempt directory is absent, or present without `run.json`, the launch
was refused before the attempt was created and the `BLOCKED:` line on stderr
is the reason.

The default answer is metadata, log sizes, whether `report.md` exists,
`pid_alive`, `stale`, `session_id_in_log`, and a bounded tools index — never a
log body. Role compliance is still the controller's.

- `session_id` is the first id already copied into `run.json`, including while
  `state` is `running`. Status does not put one there from the log.
- `session_id_in_log` is the id the log reports, offered only when the record
  holds none, and `null` otherwise. Resume from it instead of re-running a task
  whose runner was killed before it could record the session.
- `pid_alive` is whether the recorded pid is still alive. `state: running` and
  `pid_alive: false` means the record is stale; status does not rewrite it.
- `stale` is that judgement, already made: true only for `running` with no live
  process. It is not written to `run.json` either.
- `tools` holds `reads` (paths), `searches` (`pattern` / `path`), `shells`
  (`exit_code` / `command`), and `truncated`. Caps are 64 / 32 / 32 / 200
  command characters. It reads Cursor `tool_call` events and Grok `tool_use`
  items; a Grok `list_dir` is a search with `pattern` null, and a Grok shell's
  `exit_code` is null when no integer exit came back (a background task, or a
  worker stopped first). Grok writes a shell call only once it returns or
  moves to the background, so a Grok shell still running in the foreground is
  not in the index yet; do not read its absence as "no command ran". Unknown
  tool shapes are empty lists, not an error. File contents, stdout, stderr,
  and thinking stay out.

A window needs `--stream`; it defaults to 2048 bytes with a maximum of 8192,
and the whole JSON answer is capped at 64 KiB.

`pending_bytes > 0` means a UTF-8 character is only half written. Wait on the
host's job for new bytes; do not re-query the same offset in a short loop.
