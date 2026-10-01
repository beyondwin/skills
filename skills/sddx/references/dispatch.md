# Implementer dispatch

## Controller procedure

`P` is waygent's `<repo root>/.waygent/<plan-slug>/`. Every path below lives
under it, and `.waygent/.gitignore` keeps all of it out of commits.

1. `python3 "<skill-root>/scripts/resolve_backend.py" --backend <id> --json`.
   If `available` is false, stop and report `reason`. Do not switch backends.
2. Build the brief (below) at a new path under `$P/briefs/`.
3. Grok: `prepare` → `run_worker.py run` in the background → `wait` → the
   `status` windows you need → confirm the worker and its descendants have
   exited → `cleanup`. Cursor: the same run/wait/status path without
   prepare/cleanup.
4. Process exit 0 is not DONE. Judge from the report, actual test exits,
   the trailer commit, the tools index, and the native review. Do not paste
   the log.

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
  with no trailing `-fast` (for example `grok-4.7-high`, `grok-4.7-xhigh`). Cursor Grok
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

The runner sets `GROK_CURSOR_MCPS_ENABLED=0`,
`GROK_CLAUDE_MCPS_ENABLED=0`, and `CMUX_GROK_HOOKS_DISABLED=1` only in the Grok
child's environment, on both new and resumed attempts. The last one matters
when `grok` on PATH is the cmux wrapper: it stops the wrapper from installing
its hooks before it starts the real CLI, and hooks already installed stay. This prevents imported Cursor/Claude MCP startup from
adding unrelated handshake failures. It does not modify user configuration,
credentials, or session storage. Native Grok and plugin MCP initialization may
still happen. Init/inspect server listings can still include configured
servers; they do not prove a connection or a tool invocation. Inspect the
actual stderr and tool calls/results. Other startup warnings remain visible.
Cursor keeps its environment and existing approval/sandbox policy.

## Build the brief

Do not use waygent's brief template as is: its worker could read the plan, and
this one cannot. Extract the task section in the controller:

    python3 "<skill-root>/scripts/extract_task.py" <plan-file> --heading "Task 1: Save state" --global-constraints --output "$P/briefs/task-1.md"

`--heading` is the complete heading text without the leading `#` marks. Exit 0
is success, 2 is a file or argument error, and 3 is a section-selection error:
the heading is absent, duplicated, or has an empty body. Missing, duplicate, or
empty `Global Constraints` / `Global constraints` is also exit 3, and the
controller must not dispatch. A plan whose run-wide rules sit under another
title gets `--constraints-heading "<exact title>"` beside
`--global-constraints`, once that title is a recorded ruling; the flag replaces
the two default titles. The command never overwrites an existing output file,
so write each extraction to a new path.

A brief with no plan heading of its own (a fix, a retry, the final batch)
starts from the constraints section alone:
`extract_task.py <plan-file> --heading "Global Constraints" --output <new-path>`,
or the ruled title in place of `Global Constraints`.
If the plan points at another plan's constraints, extract from that plan. Do not
copy constraints by hand or from a cached `/tmp` file.

Then append, in this order, and nothing from the plan beyond it:

- `Task N of M: <title>.` and `Read <P>/guide.md first.` guide.md is an
  explicitly listed task reference.
- `Depends on:` names and signatures from earlier tasks, nothing else.
- waygent's test-first paragraph and trailer rule, verbatim from its brief:
  the task's last commit carries `Waygent-Task: N` (`Waygent-Task: final` for
  the final batch) in its last paragraph.
- `Search paths:` concrete source/test files or directories. Keep planning
  documents out of it; a glob without a target path can still search the whole
  repository.
- `Worker checks:` the local commands the worker runs and reports with actual
  exit codes. `Host checks:` the ones only this host can run; the worker names
  outstanding ones in `NEEDS_CONTEXT` or `BLOCKED` instead of claiming them.
  Run a task's Host checks before that task's review, not batched at the end.
- Any ruling the task needs. Complete a missing decision here rather than ask
  the worker to recover it from the plan.

A fix brief adds the High and Medium findings verbatim. A continuation brief
names the previous `report.md` and the commits already made. waygent's brief
length limit does not apply to these briefs.

`Search paths` limits content searches. Filename-only listings inside the
current worktree, including its root, and direct reads of repository
ignore/build/test configuration needed for this task are allowed inspection.
These actions alone are not scope deviations. They never permit reading
full-plan content, credentials, or secrets.

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

Complete brief → Grok profile prepare → run → `wait` → the
status windows you need → confirm the worker and anything it started have
exited → Grok cleanup → the existing native review.

Never start a new worker before the previous cleanup has finished on the same
journal path.

For Grok, immediately before starting the worker, prepare its worktree
profile:

    python3 "<skill-root>/scripts/prepare_grok_sandbox.py" prepare --worktree "<repo root>" --state "$P/grok-sandbox.json"

`<skill-root>`, `<repo root>`, and `$P` are absolute paths the run already
knows, not requests for more user input. The state file must be under
`.waygent/`. If preparation fails, do
not start the worker. Read `profile` out of the successful JSON and pass it to
the runner as `--sandbox-profile`; the runner substitutes it for the resolved
prefix's sandbox value itself. `run_worker.py` never prepares or cleans up.

## Run

    python3 "<skill-root>/scripts/run_worker.py" run --backend <c|cursor|g|grok> --worktree <worktree> \
        --brief <brief-file> --attempt-dir <new-attempt-dir> --effort <high|xhigh> \
        [--model <confirmed-grok-id>] [--resume <known-id>] [--sandbox-profile <prepared-profile>] \
        [--idle-timeout <seconds>] [--timeout <seconds>]

`--attempt-dir` must be a new directory under `$P/attempts/` (for example
`task-3`, `task-3-fix`, `task-3-retry`, `final`). The runner refuses a path
outside the repository's `.waygent/` directory. Create `$P/attempts/` before the
first run; the runner refuses a missing parent. Do not pipe `run`, `status`, or
`wait` through `tail` or another filter that hides the exit code; a JSON filter
on `status` is fine after `set -o pipefail`.
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
none. If a fix has no reported session ID — `session_id` null, `Worker
session: none` in the current-state block — dispatch a fresh worker with a
continuation brief that names the previous attempt's `report.md`. Never guess
an ID.

`--idle-timeout <seconds>` ends an attempt when neither `worker.jsonl` nor
`stderr.log` has grown for that many seconds, at any point from launch
onward, new or resumed. It defaults to 900, and `--idle-timeout 0` disables
it. `--timeout <seconds>` is an optional wall-clock bound on one attempt; it
defaults to 0, which waits without a bound. When either fires the runner
sends the worker SIGTERM, waits ten seconds, kills it if it is still alive,
records `state` `timed_out` with the real `exit_code`, keeps the first
session ID already copied (or scans once more if that field is still null),
and exits 124. Only
the worker process itself is signalled. It shares the controller's process
group so that a terminal interrupt reaches it, so descendants the worker
started are not pursued and no process tree is cleaned up here. Those
processes (for example a backgrounded shell, a build daemon, or Cursor's
`worker-server`, which was seen reparented to pid 1 after its worker exited)
can outlive the worker, so confirm and end them by pid yourself before cleanup.

An attempt ended by the idle timeout records `timed_out`, exit 124, and
`error` `the worker wrote no output for <N> seconds`, where `<N>` is the
`--idle-timeout` value written as a plain number (`900`, `0.5`; `the worker
wrote no output for 900 seconds` by default). The wall-clock bound records `the attempt exceeded its timeout`
instead, and wins when both have passed. After an idle timeout, check the
worktree for partial changes, then do not resume that session; dispatch a
fresh worker with a continuation brief that names the previous `report.md`
and the commits already made. Do not raise either bound to re-run it. Grok
writes nothing to its stream while it waits on a long command, whether that
command runs in the foreground or was backgrounded, so such a wait is silent
the whole time; running it in the background does not keep the attempt alive.
When a brief names a command expected to run longer than the idle window,
raise `--idle-timeout` above that command's expected duration before launching
the attempt, including the fresh continuation attempt when its brief names
that command.

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

Never end your turn while an attempt runs. A headless host (`claude -p`,
`codex exec`) ends the session when the turn ends, and the runner is killed
with it: the 8.0.0 live check lost its first attempt that way. Start `run` in
the background, then block in the foreground:

    python3 "<skill-root>/scripts/run_worker.py" wait --attempt-dir <attempt-dir>

- Claude Code: start `exec python3 "<skill-root>/scripts/run_worker.py" run …`
  as the Bash tool's background command, with no trailing `&`, so the
  background task is the runner itself. Run each `wait` in a foreground Bash
  call with `timeout: 600000`; the default of 120000 ms kills a 540-second wait.
- Codex: start `run` in its own `exec_command`. Run each `wait` through
  `exec_command` with the largest `yield_time_ms` the tool accepts, at least
  (`--max-seconds` + 10) × 1000. Do not poll with `write_stdin` or `status`
  between waits.

`wait` is read-only. It returns exit 0 with a one-line summary (`over`,
`state`, `exit_code`, `error`, `pid_alive`, `stale`, `session_id`,
`reported_model`, `report_exists`) once the attempt is over, or exit 3 after
`--max-seconds` (default 540) while it is still running; then call it again.
An attempt directory the runner has not made yet, or one with no `run.json`
yet, counts as not started for the first `--start-grace` seconds (default 15)
of each call, so the first `wait` needs no `sleep` before it; still absent
after that, the launch was refused (exit 2). Codex `wait_agent` is only for native reviewers.

    python3 "<skill-root>/scripts/run_worker.py" status --attempt-dir <attempt-dir>
    python3 "<skill-root>/scripts/run_worker.py" status --attempt-dir <attempt-dir> --stream stdout|stderr --offset N --max-bytes N

`status` is read-only. Ask it instead of dumping the log.

An attempt is over when `state` is not `running` and `pid_alive` is false; a
worker can still be writing `report.md` after its record changed. Do not start
the next attempt while the previous attempt's `pid_alive` is true.
`run.json.pid` and `pid_alive` are the worker's. To stop an attempt, send
SIGTERM to the runner: on Claude Code, stop the background task that runs it
with the host's own stop (the `exec` launch makes that task the runner);
otherwise signal the parent of the recorded pid (`ps -o ppid= -p <pid>`). Do
not signal `run.json.pid` itself, and never `pkill -f`, which can miss the
worker or hit another run. If that parent is pid 1, the runner is already gone
and the worker is an orphan; only then stop the worker by `run.json.pid`
(SIGTERM, then SIGKILL if it stays).

Read the bounded windows you need. Do not print a raw log wholesale into this
session, and do not write a new execution script for a run. Do not re-query
the same offset in a short loop.

## Clean up

For Grok, confirm the worker and any work it started have exited, then clean
up after every success or failure:

    python3 "<skill-root>/scripts/prepare_grok_sandbox.py" cleanup --worktree "<repo root>" --state "$P/grok-sandbox.json"

Do not clean up while a process is still running or overlap it with a new
worker. New tasks, resumed fixes, and retries use the same prepare, launch, exit,
and cleanup order. If cleanup fails, do not overwrite other files to repair
it; record the remaining difference and state path in `progress.md`.

## Evidence

`worker.jsonl` is the CLI's tool-call/results stream and stays local and
uncommitted with the rest of the attempt directory. Preserve test commands and
their actual exits. A shell whose command ends in `; echo …$?` proves nothing
about the test exit: the index records the echo's exit, so do not count it as
RED or GREEN evidence. The index keeps only the first 200 characters of a
command; a command cut there hides its end, so its exit is not evidence either. If the trace is unavailable or incomplete, record role
compliance as UNVERIFIED. A final message alone is not a tool trace.

Record the attempt path and the confirmed session ID in the current-state
block described by `references/current-state.md`. Take the id from the first
`wait` output that shows it, exit 3 or 0; do not call `status` for it between
waits and do not parse the log for it. `run.json` stays the attempt's process record; `progress.md`
stays the run's record. The progress line's `impl=` value comes from this
record: `reported_model` when the stream named one, else `model (requested)`,
and `configured_effort`, else `unknown`.

Read what a native reviewer actually ran on from the host's own transcript,
not from the dispatch and not from the reviewer's own words:

    python3 "<skill-root>/scripts/observed_model.py" claude-code --agent-id <agentId>
    python3 "<skill-root>/scripts/observed_model.py" claude-code --session-id <this session>
    python3 "<skill-root>/scripts/observed_model.py" codex --thread-id <thread id>

It prints one JSON line: `found`, `source`, `models` and `efforts` with counts,
and `reason` (`not_found`, `ambiguous`, `no_model_turns`, or null). It reads
only those fields and prints no transcript text. When `found` is false, write
the dispatched value followed by `(requested)`.

Do not pass `--plugin-dir`. Do not approve extra MCP servers.

## Runner already does this

`run.json` holds process facts only: `schema_version` 2, `backend`,
`identity`, `model`, `worktree`, `attempt_dir`, `brief_sha256`, `resume_id`,
`session_id`, `reported_model`, `requested_effort`, `configured_effort`, `skill_version`,
`runner_pid`, `state`, `pid`, `exit_code`, `started_at`, `ended_at`, `error`.
`skill_version` is the installed skill's `release.toml` version, written once
at start. A missing or unreadable version refuses the launch before the
attempt directory is created. `runner_pid` is the runner's own pid, written
at `starting`. Older schema 2 records without either field stay readable. `state` is one of
`starting`, `running`, `exited`, `launch_failed`, `timed_out`, or `interrupted`.
That is process state, not task state; process exit 0 is not a clean DONE.

The wrapper exit follows the worker's exit. A POSIX signal returns
`128 + signal` while `run.json.exit_code` keeps the real negative returncode.
A launch failure is 2, a handled runner interrupt is 130, and an attempt
ended by its wall-clock or idle timeout is 124. On SIGTERM or Ctrl-C, from its
first record onward, the runner records
`interrupted` at once, then ends the worker process itself the way a timeout
does (SIGTERM, ten seconds, SIGKILL) and records the exit it recovered; a
second interrupt during that wait, or an interrupt during a timeout's own wait,
goes straight to SIGKILL. That `exit_code` is `null` when the worker could not
be confirmed ended, so check `pid_alive` before cleanup. The `error` is
`the runner was interrupted (SIGTERM or Ctrl-C)`: the runner cannot know who
sent the signal, so it does not say. SIGTERM to the worker remains
`exited` (or `timed_out` when the runner sent it) with the worker's own exit:
`-15` when the signal ended it, or `143` when the CLI caught it and exited
(Cursor 2026.09.26 and Grok 1.0.44 recorded 143). SIGKILL still cannot write a
terminal state. An interrupt before the worker started (while the backend is
resolved) records `interrupted` with `pid` null, and one after the worker
started records its `pid`; one that lands inside the process start can still
leave a stray worker, so check the host for one before
starting another attempt. An interrupt after a terminal record (`exited`,
`launch_failed`) keeps that record and still exits 130.
Confirm the worker and anything it started have exited yourself either way,
before Grok cleanup. Exit 2 is ambiguous between a launch failure and a worker
that legitimately exited 2, so read `run.json.state` to tell them apart; if
the attempt directory is absent after the start grace, or present without
`run.json`, the launch was refused before the attempt was created and the
`BLOCKED:` line on stderr is the reason.

The default answer is metadata, log sizes, whether `report.md` exists,
`pid_alive`, `stale`, `session_id_in_log`, and a bounded tools index — never a
log body. Role compliance is still the controller's.

- `session_id` is the first id already copied into `run.json`, including while
  `state` is `running`. Status does not put one there from the log.
- `metadata.reported_model` is the model the worker's own `system`/`init`
  event named (Grok `grok-4.7`, Cursor for example `Grok 4.7 256K High`),
  copied once and never replaced. `model` stays the requested id. Grok reports
  no effort, so `configured_effort` (the flag value) is the only effort fact
  there.
- An `interrupted` or `stale` attempt is a stopped runner, not a failed task.
  When the task's trailer commit and `report.md` are there, judge it as a
  finished attempt; otherwise resume its session at the same effort (SKILL.md
  "Timeouts and errors").
  An `exited` attempt with no trailer commit is a task failure, whatever its
  exit code.
- `session_id_in_log` is the id the log reports, offered only when the record
  holds none, and `null` otherwise. Resume from it instead of re-running a task
  whose runner was killed before it could record the session.
- `pid_alive` is whether the recorded worker pid is still alive.
- `stale` is the judgement that nobody is left to close the record: a
  `starting` or `running` record whose runner (`runner_pid`) and worker are
  both gone. A live runner with a dead worker is about to record the exit, so
  it is not stale. A record without `runner_pid` is stale only at `running`
  with no live worker. Status does not write it to `run.json` or rewrite the
  record.
- `tools` holds `reads` (paths), `searches` (`pattern` / `path`), `shells`
  (`exit_code` / `command`), and `truncated`. Caps are 64 / 32 / 32 / 200
  command characters. It reads Cursor `tool_call` events and Grok `tool_use`
  items; a Grok `list_dir` is a search with `pattern` null. A shell's
  `exit_code` is null when no integer exit came back (a background task, or a
  worker stopped first), on both backends. A shell is indexed once it returns
  or moves to the background, so a shell still running in the foreground is
  not in the index yet; do not read its absence as "no command ran". Unknown
  tool shapes are empty lists, not an error. File contents, stdout, stderr,
  and thinking stay out.

A window needs `--stream`; it defaults to 2048 bytes with a maximum of 8192,
and the whole JSON answer is capped at 64 KiB.

`pending_bytes > 0` means a UTF-8 character is only half written. Wait for
new bytes; do not re-query the same offset in a short loop.
