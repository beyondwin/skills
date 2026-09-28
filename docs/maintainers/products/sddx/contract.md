# sddx contract

This document is the normative contract for what SDDx owns, when it turns on,
how it launches workers, and how it judges their results. Before changing
behavior, check this document and "Files to change together" at the end.

## What is in this document

- Product name, ownership, and when it turns on: "Product identity", "Hard gate"
- Call arguments and picking the worker kind: "Invocation and backend choice"
- Reviewer model, reasoning effort, and the XHigh reviewer definition: "Reviewers and effort"
- How tasks are split among workers: "Task unit"
- Implementation worker model, effort, and session reuse: "Implementation worker model and effort"
- What a worker must not do: "Worker side effects and secrets"
- Grok sandbox preparation and cleanup: "Grok sandbox profile"
- Writing the brief and the worker's read and search scope: "Brief and read scope"
- When a task counts as done: "Completion judgment"
- `resolve_backend.py` output and required flags: "Backend resolution"
- Grok tool limits: "Grok worker tools and MCP startup"
- Commands, records, exit codes, and timeouts of `extract_task.py` and `run_worker.py`: "Execution helpers and attempt evidence"
- The current-state block in the ledger: "Current state"

## Terms

| Term | Meaning |
| --- | --- |
| Host | The program that runs the skill. Only `claude-code` and `codex`. |
| Controller (orchestrator) | The host session that received `/sddx` or `$sddx`. It dispatches tasks, checks results, and runs reviews. |
| Worker | The outside CLI process that does only implementation: Cursor Agent or Grok Build. |
| Backend | The CLI kind used as the worker: `cursor` or `grok`. |
| Picker | The one-time question to the user when no backend argument is given. |
| Ledger | The progress file Superpowers SDD keeps per plan. |
| Dispatch | Handing work to a worker or reviewer and launching it. |
| Brief | The one-task sheet a worker gets. |
| Runner | `scripts/run_worker.py`, which launches the worker and records the attempt. |
| Attempt | One worker run. Each attempt gets its own folder. |
| Worktree | The Git worktree Superpowers uses. A linked worktree is one added with `git worktree`. |
| Effort | Reasoning effort: High or XHigh. XHigh thinks harder. |
| Ruling | A decision the controller makes when a worker is blocked or the design is unclear. |
| Fix round | One round of fixing defects found in review. |

## Product identity

The product ID, skill `name`, and directory name are `sddx`. The display name
is `SDDx`. It is called with `/sddx` in Claude Code and `$sddx` in Codex.

The supported hosts are only `claude-code` and `codex`. The Cursor CLI and the
Grok CLI are implementation workers, not hosts, so `cursor` and `grok` are not
in `supported_hosts`.

Ownership is split as follows. Do not copy the SDD text into this skill.

- Superpowers SDD: the worktree, the ledger, `sdd-workspace`, review-package,
  reviewer prompts, the fix loop, the whole-branch review, and the workspace and
  report file names.
- `sddx`: argument parsing, backend choice, `resolve_backend.py`, the
  implementation worker argv, checking worker limits and run evidence, choosing
  the review model and effort, and task section extraction (`extract_task.py`).

## Hard gate

Follow the installed Superpowers `subagent-driven-development` flow, but SDDx
rules win for dispatching implementation workers, review model and effort, and
checking worker evidence. Do not edit Superpowers files. Do not implement in
the controller session.

Activate only when the user message contains `/sddx` or `$sddx`. Do not turn
on for an outside-implementation request without the slash or dollar call, for
native SDD, executing-plans (including Native), writing-plans, or
pre-sdd-review.

## Invocation and backend choice

The arguments are `sddx <plan-file> [cursor|grok|c|g]`. `c` means `cursor` and
`g` means `grok`. One call is one plan. If the plan path is missing or is not a
file, do not guess; ask once.

- With a backend argument, do not ask.
- Without one, ask once for this plan. Claude Code uses AskUserQuestion; Codex
  offers numbered choices. Ask once and wait for the answer. The choices are
  Grok CLI and Cursor Agent (Grok). Do not ask again per task.
- Record the choice in the ledger as `Backend: cursor|grok` and keep it for
  every task of that plan.
- Even when only one backend is available, do not pick it automatically. Show
  that fact and the missing backend's `reason`, and if there was no backend
  argument, proceed only after confirmation.
- If the requested backend is missing, stop instead of switching. If both are
  missing, it is `BLOCKED`.

## Reviewers and effort

Task reviewers, scoped re-reviewers, and the final reviewer are host native.
Claude Code launches them with Task, Codex with `spawn_agent`. The only outside
process is the implementation worker.

### Model

- The controller keeps the model and effort of the session that received
  `/sddx` or `$sddx`. Do not switch to a cheaper model, a top model for the
  final review, or the implementation worker's model family.
- Every task review, re-review, and final review uses the controller's model at
  dispatch time. This rule wins over plain SDD's cheap-model choice and its
  top-model choice for the final review.
- Inherit the model when the host supports it; when it must be named, use the
  same confirmed model ID. Do not pin a model family or move only reviews to a
  different model.
- If the model ID cannot be confirmed, do not guess; record that it was
  inherited and that the ID is unconfirmed.

If a native reviewer cannot be reached (quota spent, cannot spawn), do not
quietly move the review elsewhere. The order is:

1. Wait until the blocking condition clears, then dispatch natively again.
2. Use another native route the controller host offers.
3. Stop and ask the user.

Only the user's answer justifies moving a review off native, and even then the
implementer's model family is the last choice. Reviewing your own work removes
the independence this section protects. Record the changed host, model, and
reason in the current-state block and on each affected review line.

### Effort

- Review effort is set separately from session effort. In Claude Code, High is
  dispatching as SDD always did, with no `model` argument; XHigh is also no
  `model` argument, with `subagent_type` set to `sddx:sddx-reviewer-xhigh`. Do
  not pass a `model` override to reviewers.
- XHigh triggers are changes to locks, ordering, or shared state; changes to
  auth, permission, secret, or sandbox boundaries; round 4-5 re-reviews; and a
  defect missed repeatedly.
- Decide from the review-package stat, the task brief, the changed file paths,
  and the ledger. Do not decide by reading the diff body.
- File count, line count, implementation difficulty, a short diff, or being the
  final review are not triggers. A re-review keeps the original defect's risk.
- If the session effort is already XHigh or higher, do not raise it, and do not
  lower the session.
- Record every review dispatch in the ledger. High is one line; XHigh also
  records the trigger and concrete paths. If no trigger can be named, it is
  High.

### XHigh reviewer definition

The definition file is `agents/sddx-reviewer-xhigh.md` and the Task name is
`sddx:sddx-reviewer-xhigh`. The file's frontmatter name alone is not enough for
Task to find it.

- Do not put an `agents` key in `plugin.json`. The default `agents/*.md` scan
  fills both the Claude Code inventory and Task registration. A nested path or a
  `plugin.json` `agents` field makes `plugin details` report Agents (0).
- The two install links stay as they are; no new install step is added.
- When the definition is missing (always on Codex, and on Claude Code when it
  fails to load), report that the requested effort cannot be set, then dispatch
  the default way. Do not substitute another model or effort, do not create a
  definition, and do not set the run to `BLOCKED` because it is missing.

## Task unit

Rule: one worker never bundles several plan tasks. One plan heading is one worker and
one review-package section. Do not bundle even same-shaped one-line fixes.

Do not descend into nested native SDD. Do not hand
`subagent-driven-development` as a whole to a subagent one level down.

Ask once before dispatching work the plan does not name. "Run it to the end"
covers only the tasks in the plan.

## Implementation worker model and effort

Both backends use only Grok 4.7. `-fast` variants are not supported.

- Grok: pass the resolver-confirmed `grok-4.7` with `--model`, and effort with
  `--reasoning-effort` or `--effort`. Do not pass `grok-4.7-build-fast`,
  `grok-4.6`, or `grok-4.5`.
- Cursor: pass only a confirmed id whose version segment is `4.7` and that does
  not end in `-fast`.

Implementation effort is High or XHigh per task, from the task difficulty
table.

- Do not copy the session effort to implementation. An XHigh reviewer does not
  force an XHigh implementer.
- High: clear, local, mechanical changes and simple integration.
- XHigh: concurrency, races, locks, ordering, shared state; auth, permission,
  secret, or sandbox boundaries; side effects across several subsystems.
- Resolve design ambiguity with a controller ruling, not XHigh. If no reason
  can be named, it is High.

Session reuse rules:

- A new task gets a new worker. Raised effort gets a new worker.
- Fix rounds 1-3 resume the same worker session only when the requested effort
  is the same. Rounds 4-5 use a new worker at XHigh.
- When a worker returns `NEEDS_CONTEXT` or `BLOCKED`, make a ruling, then
  dispatch again to the same backend.
- Do not pass `--worktree` to the worker. The cwd is the current Superpowers
  worktree.

## Worker side effects and secrets

Do not put host credentials or environment values in the worker prompt or
`--prompt-file`. If a worker needs a side effect outside the host, such as a
push, a publish, or updating a shared branch, it stops as `BLOCKED`. Do not
count that result as a review-passed `DONE`.

## Grok sandbox profile

Follow this order when dispatching a Grok worker, for new tasks and resumes
alike.

1. Call `prepare_grok_sandbox.py prepare` right before launching the worker. If
   prepare fails, do not start the worker.
2. Replace the single `--sandbox` value in the resolver `argv_prefix` with the
   returned working profile. Pass the whole worker prompt with `--rules`.
3. When the worker and the jobs it ran have ended, success or failure, call
   `prepare_grok_sandbox.py cleanup`.

If cleanup fails, do not overwrite other files; record the remaining
difference and the state record location in the ledger. The generated settings
and restore state are neither product output nor something to commit.

## Brief and read scope

### Building the brief

- Before dispatching, the controller extracts the task with
  `extract_task.py --global-constraints` and fills in the needed conditions and
  task references.
- Constraints the plan writes once for the whole run are put at the front of
  the brief by that flag as the `Global Constraints` section. Do not copy them
  by hand. The worker cannot read the plan, so a constraint missing from the
  brief does not exist for the worker, and review later reports a defect the
  worker had no way to avoid.
- Do not pass the whole plan as a reference. For new calls and resumes alike,
  state the document boundary directly.
- Split the brief's checks into `Worker checks` and `Host checks`. A task's
  Host checks run before that task's review, not bunched at the end of the
  plan.

### Reading and searching

- List concrete source and test files and directories in the brief's
  `Search paths:`. The worker reads the named files directly first.
- When a content search is needed, pass these paths as tool arguments. Do not
  assume a file glob alone limits the paths. Without search paths, read the
  named files directly or ask the controller for the missing path. Do not run
  a content search over the whole workspace.
- The worker may read the source and tests it needs, but never the whole plan,
  including through links, shells, searches, or Git history. A missing decision
  is `NEEDS_CONTEXT`.
- `Search paths` limits content search. Listing file names inside the current
  worktree (root included) and directly reading the repository ignore, build,
  and test settings the task needs are allowed checks. They alone do not need a
  scope deviation or a separate ruling; with no other deviation,
  `Scope deviations: none` is correct. This allowance does not cover reading
  the whole plan body, credentials, or secrets.

### Worker report

- The scope deviations item is required. Record the action tried or done, its
  target, and the result; do not copy the plan text again. A deviation that was
  later corrected is still not a clean `DONE`.
- When a test wrapper is used, separate the exit of the whole command from the
  exit of the actual tests.

## Completion judgment

A process exit of 0 alone does not complete a task. Check the test results in
the worker report, the task's change commits, the actual tool-call/results
record, and the native review.

- Record role compliance in the ledger as `PASS`, `FAIL`, or `UNVERIFIED`.
- Tell a read attempt apart from actual content returned, and check shell and
  search tool results too. A search that returns some lines of the plan counts
  as reading plan content.
- A successful forbidden document read is `FAIL` regardless of test success; a
  missing or incomplete record is `UNVERIFIED`. Neither is promoted to a clean
  `DONE`.
- Pass observations that differ from the report on to the reviewer. A later
  admission or a later proper call does not erase an earlier violation. Decide
  the needed action with the existing ruling process.
- `BLOCKED`, `NEEDS_CONTEXT`, a missing report, or an unclear result is not
  `DONE`.
- Handle `DONE_WITH_CONCERNS` through the existing ruling process; a
  verification-only answer does not need a new commit.

## Backend resolution

The controller runs `scripts/resolve_backend.py` from the loaded skill root.
This command uses no network, writes no files, and launches no worker.

- On success, stdout is one JSON object followed by LF.
- A missing backend is exit code 0 with `available: false`. Only bad arguments
  give a nonzero code. Do not pick another backend from the exit code alone.

### Candidate executables

- The only Grok candidate is `grok` on PATH.
- Cursor candidates are `cursor-agent`, then `cursor` whose identity is the
  Cursor Agent CLI. A Grok Build identity is not accepted as Cursor.
- `agent` is neither a Grok nor a Cursor candidate.

### JSON output

The keys are `backend`, `available`, `executable`, `identity`, `argv_prefix`,
`reason`, `launch`, and `model_ids`.

- `launch` holds `cwd_flag`, `prompt_flag`, `effort_flag`, and
  `output_format`. When `available` is false, `launch` is `null` and
  `model_ids` is an empty list.
- `output_format` is used exactly as the host's resolver returned it and is
  not hardcoded per backend.
- For either available backend, `model_ids` holds only Grok 4.7. Grok Build
  returns only a listed `grok-4.7`; Cursor returns only Grok ids whose version
  segment is `4.7` and that do not end in `-fast`. `4.6`, `4.5`, and `-fast`
  variants are dropped even when listed.

A missing backend's `reason` is one of `not_found`, `identity_mismatch`,
`missing_flags`, `no_model_list`, `model_list_unreadable`, `no_grok_model`, or
`no_grok_4_7`. The four about the model list state different facts.

| `reason` | Meaning |
| --- | --- |
| `no_model_list` | No list was obtained at all. |
| `model_list_unreadable` | A list came back but no id could be read. |
| `no_grok_model` | Ids were read but none is Grok. |
| `no_grok_4_7` | Grok ids were read but none is 4.7. Also used when only `-fast` remains. |

The first two do not claim the model is absent. On `no_grok_4_7`, do not
switch to 4.6 or 4.5.

### Required flags

The Grok resolver checks the required run flags, including `--sandbox`,
`--rules`, and `--disable-web-search`, and puts `--sandbox workspace` in the
default `argv_prefix`. The tool-limit flags are in "Grok worker tools and MCP
startup".

Cursor requires the following.

- `prompt_flag` is fixed at `null`, so `build_argv` appends the prompt as an
  unnamed positional argument. The Usage line must therefore show `[prompt]` or
  `[prompt...]` to pass.
- The breaking changes of `2.0.0` are required Cursor features. The Cursor
  resolver requires headless print (`--print` or `-p`), `--trust`,
  `--auto-review`, `--sandbox`, a confirmed `stream-json` output format, and
  Grok 4.7 ids returned by a model list command that actually succeeded. An
  older Cursor CLI that does not declare `--auto-review`, `--sandbox`, or a
  structured output format is `available: false` with `reason: missing_flags`.
- The old `--force`/`--yolo` blanket-approval fallback is gone and cannot be
  brought back with a flag. The resolved prefix already holds the headless and
  approval flags, so do not append a second `--sandbox` or a second approval
  flag.

`--resume` must be declared as taking a value (`<id>` or `[id]`) for both
Cursor and Grok. `build_argv` puts `--resume <id>` right before the positional
prompt, so a `--resume` that takes no value pushes the prompt out of place. If
either a value-taking `--resume` or Cursor's positional prompt declaration is
missing, it is `missing_flags`.

## Grok worker tools and MCP startup

- The Grok resolver requires value-taking `--disallowed-tools` and `--deny`
  declarations. If either is missing, it is `missing_flags`, with no fallback to
  a weaker run.
- `--disallowed-tools search_tool,use_tool` removes the MCP call tools, and
  `--deny MCPTool(*)` is passed with it.
- The runner sets `GROK_CURSOR_MCPS_ENABLED=0` and
  `GROK_CLAUDE_MCPS_ENABLED=0` only on the Grok child process, for new calls
  and resumes alike. It does not change the parent environment, global
  settings, or auth and session locations. It does not apply to Cursor.
- The supported OS is macOS only; Windows command transport is not part of the
  product contract.

This covers only MCP startup imported from Cursor/Claude and the boundary on
specific tools. Its limits:

- Excluding `Agent`/`task` would also remove the command result and stop
  tools, so it is not used.
- Subagents are limited by the existing `--no-subagents` and the worker
  instructions, but tool removal is not guaranteed.
- It is not isolation that blocks Grok's own or plugin MCP startup, calls
  through a shell, and all file access.
- A server list shown by init/inspect is not evidence of an actual connection
  or tool call, so check stderr and the actual tool record. Do not hide other
  CLI startup warnings.

## Execution helpers and attempt evidence

### Task extraction

To extract a task section from the plan, the controller uses
`scripts/extract_task.py <plan-file> --heading "<full heading without #>" --global-constraints --output <file>`.

- `--heading` is the full heading without the `#` marks. When extracting a task
  heading, `--global-constraints` is required.
- Exit 0 is success, 2 is a file or argument error, 3 is a missing or duplicate
  heading or an empty body. A `Global Constraints`/`Global constraints`
  section that is missing, appears more than once, or has an empty body is
  also exit 3, and then no worker is dispatched.
- An existing output file is never overwritten, so use a new path for each
  extraction.
- A brief without a plan heading (a fix round, a continuation) starts from the
  output of
  `extract_task.py <plan-file> --heading "Global Constraints" --output <file>`,
  which extracts only the constraints section. If the plan points at another
  plan's constraints, extract from that plan. Do not copy by hand or use a
  `/tmp` cache.

### Running the worker

- Run workers only through `scripts/run_worker.py run`. Do not assemble the
  provider command directly or write a new launch script per run.
- `--attempt-dir` is a new folder under the plan directory that Superpowers
  `sdd-workspace` made. That plan directory is `.superpowers/sdd/<plan-name>/`
  in the worktree. Do not use a flat shared `.superpowers/` name. Create the
  attempt parent folder before the first run.
- The runner leaves six files in the attempt folder: `brief.md`,
  `dispatch.md`, `worker.jsonl`, `stderr.log`, `run.json`, and `report.md`. The
  worker writes `report.md` itself; the runner does not.
- The runner does not call `prepare` or `cleanup`. The controller keeps the
  prepare → run → end check → cleanup order.
- No helper retries automatically.
- Do not pipe `run` or `status` output through something that hides the exit.
- `--model` is required for both backends and must be in that backend's
  `model_ids`. Grok requires `--sandbox-profile` and `--model grok-4.7`. Cursor
  requires a Grok 4.7 `--model` picked from the resolver `model_ids` and
  rejects `--sandbox-profile`.

### Checking an attempt

Check an attempt only with the read-only `scripts/run_worker.py status`.
Whether it is alive, the session ID, and which files were read come only from
this command; do not paste the whole log into the session.

The default answer is metadata, log sizes, whether `report.md` exists,
`pid_alive`, `stale`, `session_id_in_log`, and `tools`. It has no log body.
The controller judges role compliance (whether the plan was read, whether it is
`DONE`). A body window appears only with `--stream`, 2048 bytes by default and
8192 at most; the whole JSON answer is at most 64 KiB.

- `session_id` is the first ID the worker stream reported. It is copied to
  `run.json` as soon as it appears in the stream, even while `state` is
  `running`, and never changes once written. `status` shows only that record.
  It is not created from an ID in the log when the record has none. If the
  stream gives no ID, it is `null`.
- `pid_alive` is whether the recorded pid is alive now. It is not stored in
  `run.json`. If `state` is `running` but `pid_alive` is false, only the record
  is left. `status` does not rewrite that record to `interrupted`.
- `stale` is that judgment itself: true only when `state` is `running` and
  `pid_alive` is false. It is false for an ended state or a missing record, and
  is not stored in `run.json`.
- `session_id_in_log` shows the ID the log reported only when the record has
  none; when the record has an ID it is `null`. The rule that `session_id` is
  the only value used for resume stays, and the two can never disagree. This
  lets a worker session be resumed even if the runner died before recording
  it. It is not written to `run.json`.
- `tools` is a short list copied from the log: `reads` (paths), `searches`
  (query and path), `shells` (exit code and command), and `truncated`. It reads
  Cursor `tool_call` events and Grok `tool_use` entries.
  - A Grok `list_dir` is a search whose `pattern` is null.
  - A Grok shell that returned no integer exit code (a background job, a
    worker that stopped first) has a null `exit_code`.
  - Grok records a shell call only after it returns or is moved to the
    background, so a Grok shell still running in the foreground is not in the
    index yet. Do not read its absence as "the command did not run".
  - It holds no file contents, stdout, stderr, or thinking.
  - The limits are 64 reads, 32 searches, 32 shells, and 200 characters per
    command. An unknown tool shape is an empty list, not an error. Lines that
    are not JSON or are too deeply nested are skipped.

### Ending and stopping an attempt

An attempt has ended when `state` is not `running` and `pid_alive` is false.
Do not launch a new attempt while the previous attempt's `pid_alive` is true.

`run.json.pid` and `pid_alive` belong to the worker. To stop, send SIGTERM to
the runner: the pid of the host job, or the parent of the recorded pid found
with `ps -o ppid= -p <pid>`. Never send it to `run.json.pid` itself or use
`pkill -f`. If that parent is pid 1, the runner is already gone and the worker
is an orphan; only then stop the worker at `run.json.pid` directly (SIGTERM,
then SIGKILL if it remains).

### `run.json` and exit codes

`run.json` holds only process facts. With `schema_version` 2 it records
`backend`, `identity`, `model`, `worktree`, `attempt_dir`, `brief_sha256`,
`resume_id`, `session_id`, `requested_effort`, `configured_effort`,
`skill_version`, `state`, `pid`, `exit_code`, `started_at`, `ended_at`, and
`error`.

- `skill_version` is the installed skill's `release.toml` version, written
  once at start. If it is missing or unreadable, the run is refused before the
  attempt directory is created. Older schema 2 records without this field are
  still read.
- `state` is one of `starting`, `running`, `exited`, `launch_failed`,
  `timed_out`, or `interrupted`; it is not a task status. A process exit of 0
  is not a clean `DONE`.

The wrapper exit follows the worker's exit.

- When the worker ends by a POSIX signal, it returns `128 + signal`, and
  `run.json.exit_code` keeps the actual negative returncode.
- A launch failure is 2, a handled interrupt is 130, and a timeout end is 124.
  Exit 2 overlaps between a launch failure and a worker that really exited 2,
  so tell them apart with `run.json.state`.
- A missing attempt directory, or one without `run.json`, means the run was
  refused before the attempt was created; the `BLOCKED:` line on stderr gives
  the reason.

### Signals

Signals take two paths.

- When the runner (wrapper) gets SIGTERM or Ctrl-C, it first records
  `interrupted`, ends the single worker process the same way as a timeout
  (SIGTERM, 10 seconds, SIGKILL), records the reaped `exit_code` again, and
  exits 130. If the worker could not be confirmed ended, that `exit_code` is
  `null`, so check `pid_alive` before cleanup. A second interrupt during that
  wait, and an interrupt during the wait while a timeout ends the worker, go
  straight to SIGKILL. `error` is
  `the runner was interrupted (SIGTERM or Ctrl-C)` and does not name who sent
  the signal.
- When the worker gets SIGTERM, the result is `exited` (`timed_out` if the
  timeout sent it) with a negative `exit_code`. SIGKILL leaves no record, so
  check `pid_alive`.

Signals go to the single worker process only. The worker stays in the
controller's process group so a terminal interrupt reaches it, and the child
processes the worker started are not chased. The interrupt path and the
timeout path share this limit; never record that the process tree was cleaned
up.

- Processes the worker started (for example a background shell, a build
  daemon, or Cursor's `worker-server`, observed left behind reparented to pid 1
  after the worker ended) can outlive the worker, so check them by pid and end
  them by pid before cleanup.
- An interrupt while the worker process is being launched can leave `run.json`
  as `starting` with no pid. In that case, check the host for a leftover worker
  before launching the next attempt.

### Timeouts

- `--idle-timeout <seconds>` ends the attempt when neither `worker.jsonl` nor
  `stderr.log` grows for that long. It applies from right after launch until
  the end, for new attempts and resumes alike. It defaults to 900;
  `--idle-timeout 0` turns it off.
- `--timeout <seconds>` is an optional limit on one attempt's wall-clock time.
  It defaults to 0; `--timeout 0` waits without a bound.

When either fires, the runner sends SIGTERM to the worker, waits 10 seconds,
kills it if it is still alive, sets `state` to `timed_out`, and records the
actual `exit_code`. The session ID keeps the first value already copied; if it
is still null, the log is scanned once more. Then the runner exits 124.

The `error` text is as follows. If both have passed, the wall-clock limit wins.

- Idle timeout: `the worker wrote no output for <N> seconds`. `<N>` is the
  `--idle-timeout` value as a plain number (`900`, `0.5`; by default
  `the worker wrote no output for 900 seconds`).
- Wall-clock limit: `the attempt exceeded its timeout`.

After an idle timeout, check the worktree for partial changes, and do not
resume that session or rerun it with a higher limit. Instead dispatch a fresh
worker with a continuation brief that names the previous `report.md` and the
commits already made.

While Grok waits on a long command, foreground or moved to the background, it
writes nothing to the stream, so it is silent for the whole wait. Running the
command in the background does not keep the attempt alive past the idle
window. When a brief names a command expected to run longer than the idle
window, raise `--idle-timeout` above that command's expected duration before
launching the attempt. This includes a fresh continuation attempt that names
that command.

### Effort record

Requested and configured effort are recorded separately. Cursor carries effort
in the model ID, not a flag, so the runner rejects a model whose declared
effort disagrees with `--effort`, and records the effort read from the ID in
`configured_effort`. If the ID declares no effort, it stays `null` and the
applied effort is `unknown`. Neither proves the effort the model actually
applied, so never record the requested value as the applied value.

## Current state

A run's current state lives only in that plan's Superpowers SDD ledger.

- Right below the ledger's first line, keep one block wrapped in
  `<!-- sddx:current:start -->` and `<!-- sddx:current:end -->`, and replace
  only its content on each update. Leave the completed lines and the fix-round
  history below the block as they are.
- `skills/sddx/references/current-state.md` owns the block's fields.
- Rewrite the block right before each dispatch, on task completion, at the
  start and end of a fix round, on a ruling that changes the run, and on a
  user scope change.
- Every field describes the run as it is now. A field that disagrees with the
  evidence on disk (attempt directories, review lines below the block, Git
  HEAD) is a defect and is fixed before the next dispatch.
- History goes below the block, not inside it. Replace stale values instead of
  appending.
- Do not create separate state files such as `controller-current-state.md` or
  `controller-recovery.md`. `run.json` is one attempt's process record and the
  ledger is the run's record; do not sync them both ways.

Changing shared product source does not switch or restart a run in progress.
A change applies from the next run; resume an existing run explicitly after
checking its ledger and processes.

## Files to change together

Do not put a behavior change in one file only.

- Host or backend identity: `products.toml`, this contract, the product
  README, the public compatibility guide, `tests/products/sddx/`
- Activation, backend choice, hard gate: `skills/sddx/SKILL.md`,
  `skills/sddx/references/dispatch.md`,
  `skills/sddx/references/worker-prompt.md`,
  `tests/products/sddx/cases.json`, `tests/products/sddx/test_contract.py`,
  `scripts/lib/product_contract.py`, `tests/repository/test_repository.py`
- `resolve_backend.py` identity and flag rules:
  `skills/sddx/scripts/resolve_backend.py`,
  `tests/products/sddx/test_resolve_backend.py`
- Task extraction rules: `skills/sddx/scripts/extract_task.py`,
  `tests/products/sddx/test_extract_task.py`
- Run and status rules: `skills/sddx/scripts/run_worker.py`,
  `skills/sddx/references/dispatch.md`,
  `tests/products/sddx/test_run_worker.py`,
  `tests/products/sddx/test_worker_status.py`
- Current-state block: `skills/sddx/references/current-state.md`,
  `skills/sddx/SKILL.md`
- Version and installed files: `skills/sddx/release.toml`, `SKILL.md`,
  `CHANGELOG.md`, `skills/sddx/.claude-plugin/plugin.json`
