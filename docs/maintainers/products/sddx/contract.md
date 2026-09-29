# sddx contract

What SDDx promises, in the words tests lock. The runtime text is
`skills/sddx/SKILL.md` and its `references/`. Before changing behavior, read this
page and "Files to change together" at the end.

## Terms

| Term | Meaning |
| --- | --- |
| Host | The program that runs the skill: `claude-code` or `codex` only. |
| Controller | The host session that received `/sddx` or `$sddx`. It never writes code. |
| Worker | The outside CLI that writes the code: Cursor Agent or Grok Build. |
| Backend | Which worker: `cursor` or `grok`. |
| Brief | The one-task sheet a worker reads. |
| Attempt | One worker run, in its own folder. |
| Runner | `scripts/run_worker.py`, which starts a worker and records the attempt. |
| Effort | How hard the model thinks: High or XHigh. |

## Who owns what

SDDx is waygent with an outside coder. It reads the installed waygent skill
(`<skill-root>/../waygent/SKILL.md`) as its base loop and does not copy it.

- waygent owns the loop: the branch, `.waygent/<plan-slug>/` with `progress.md`,
  `guide.md`, and `reviews/`, one task at a time, test first, the
  `Waygent-Task: N` trailer, one review and one fix per task, one final review,
  retry once after a failure, resume from Git, and the report. Reviewers are
  native and follow waygent's Models section.
- sddx owns: when it turns on, picking the backend, `resolve_backend.py`,
  building the brief (`extract_task.py`), launching and watching workers
  (`run_worker.py`), the Grok sandbox (`prepare_grok_sandbox.py`), checking
  worker evidence, implementer effort, and recording the models that actually
  ran (`observed_model.py`).

If the waygent skill is missing, SDDx stops as BLOCKED. waygent's "not for
`/sddx`" line is about activation only.

## When it turns on

It turns on only when the user message contains `/sddx` or `$sddx`. Not for `/waygent`,
native SDD, executing-plans (including Native), writing-plans, pre-sdd-review,
or an outside-implementation request without the slash or dollar call.

## Arguments and backend

`sddx <plan-file> [cursor|grok|c|g]`. `c` is `cursor`, `g` is `grok`. A plan file
is required; ask once if it is missing. `/sddx` alone resumes the one folder
under `.waygent/` that has an SDDx block.

- A backend argument means no question. Without one, ask once per plan and keep
  the answer.
- With only one backend available, still confirm; do not pick it silently.
- A missing requested backend stops the run. Never switch automatically.
- Both backends run only Grok 4.7, never a `-fast` id.

## Tasks and workers

- One plan task is one worker attempt: one worker never bundles several plan
  tasks.
- The worker cannot read the plan. Each brief is the `extract_task.py` output
  with `--global-constraints`, plus waygent's lines (guide.md, test first,
  trailer), `Search paths`, `Worker checks`, and `Host checks`. A fix, retry, or
  final batch brief starts from
  `extract_task.py <plan> --heading "Global Constraints"`.
- A fix resumes the same worker session at the same effort. A retry after a
  failure is a fresh worker at XHigh. Final-review fixes and the app walk are one
  worker attempt.
- Implementer effort is High or XHigh per task, from the table in `SKILL.md`.
  It is not the session effort, and design ambiguity is a ruling, not XHigh.
- Run a task's Host checks before that task's review.
- The worker never pushes, publishes, or updates a shared branch; it returns
  BLOCKED instead. Host credentials never go into a brief.

## Judging a worker

Process exit 0 is not done. The controller reads `report.md`, the trailer commit,
the fast check, and the `run_worker.py status` tools index, and records role
compliance as PASS, FAIL, or UNVERIFIED.

- A successful read of the plan, credentials, or secrets is FAIL, even when tests
  pass. A missing or partial tool record is UNVERIFIED. Neither is a clean DONE.
- Filename listings and reading repository ignore/build/test settings are
  allowed and are not scope deviations.
- BLOCKED, NEEDS_CONTEXT, a missing report, or an unclear result is not DONE.

## Recording models

The progress line records what actually ran:

    task N: done <sha7> impl=<backend>:<reported_model>/<effort> review=<...> reviewer=<model>/<effort> tests=<...> role=<...>

- Worker: `run.json` keeps `model` (what was asked for), `reported_model` (what
  the worker's own `system`/`init` event said), and `configured_effort`.
  `reported_model` is copied once and never replaced.
- Reviewers and the controller: `observed_model.py` reads the host's own
  transcript (Claude Code `agent-<id>.jsonl` or the session file; Codex
  `rollout-*-<thread>.jsonl`) and prints models and efforts with counts. It
  prints no transcript text.
- A value nothing confirmed is written with `(requested)`.

## Current state

`progress.md` keeps waygent's lines. Right under its header lines sits one block
between `<!-- sddx:current:start -->` and `<!-- sddx:current:end -->`, replaced
on each update. `references/current-state.md` owns its fields. A field that
disagrees with Git or the attempt folder is fixed before the next dispatch. No
other state file.

## Runner and status

Launch only through `run_worker.py run`; read attempts only through
`run_worker.py status`. Attempt folders live under `$P/attempts/`, and the runner
refuses any path outside the repository's `.waygent/` directory. The Grok sandbox
state file also lives under `.waygent/`.

- `run.json` holds process facts only, including `session_id`, `reported_model`,
  `requested_effort`, `configured_effort`, and `skill_version`. Its `state` is
  process state, not task state.
- `status` gives metadata, `pid_alive`, `stale`, `session_id_in_log`, and a
  bounded tools index (Cursor `tool_call`, Grok `tool_use`). It never returns a
  log body unless asked for a window.
- A Grok shell still running in the foreground is not in the index yet.
- Stopping: send SIGTERM to the runner (`ps -o ppid= -p <pid>`), never
  `pkill -f`. If that parent is pid 1, the runner is gone; only then signal the
  worker pid.
- On SIGTERM or Ctrl-C the runner records `interrupted` with
  `the runner was interrupted (SIGTERM or Ctrl-C)` and ends the worker. If the
  worker could not be confirmed ended, `exit_code` is null, so check
  `pid_alive` before cleanup.
- The runner signals only the worker process. Anything the worker started (a
  background shell, a build daemon, Cursor's `worker-server`) can outlive it;
  end them by pid.

### Timeouts

- `--idle-timeout` defaults to 900 seconds; `0` turns it off. It ends an attempt
  when neither log grows for that long, with
  `the worker wrote no output for <N> seconds`.
- `--timeout` defaults to 0 (no wall-clock bound).
- After an idle timeout, do not resume that session. Start a fresh worker whose
  brief names the previous `report.md` and the commits already made.
- Grok writes nothing while it waits on a long command, and moving it to the
  background does not keep the attempt alive. When a brief names a command
  longer than the idle window, raise `--idle-timeout` above that command's
  expected duration before launch.

## Backend resolution

`resolve_backend.py` uses no network, writes nothing, and starts no worker. A
missing backend is exit 0 with `available: false` and a `reason`
(`not_found`, `identity_mismatch`, `missing_flags`, `no_model_list`,
`model_list_unreadable`, `no_grok_model`, `no_grok_4_7`). The only Grok
candidate is `grok`; Cursor is `cursor-agent` or `cursor` with a Cursor
identity; `agent` is never either. Grok needs `--disallowed-tools` and `--deny`
(MCP tools are removed); Cursor needs headless print, `--trust`,
`--auto-review`, `--sandbox`, `stream-json`, and a positional prompt. Both need
a `--resume` that takes a value. `tests/products/sddx/test_resolve_backend.py`
locks the details.

## Supported OS

macOS only. The product CLIs refuse Windows.

## Files to change together

- Hosts or backends: `products.toml`, this page, the README pair,
  `compatibility.md`, `tests/products/sddx/`
- Activation and the loop split: `skills/sddx/SKILL.md`,
  `references/dispatch.md`, `references/worker-prompt.md`,
  `tests/products/sddx/cases.json`, `tests/products/sddx/test_contract.py`
- waygent section names SDDx relies on (`Start or resume`, `Per task`,
  `When a task fails`, `Final review, once`, `Models`): also
  `docs/maintainers/products/waygent/contract.md`
- Runner, status, and records: `scripts/run_worker.py`, `references/dispatch.md`,
  `test_run_worker.py`, `test_worker_status.py`
- Model records: `scripts/observed_model.py`, `test_observed_model.py`
- Versions: `release.toml`, `SKILL.md` `metadata.version`, `CHANGELOG.md`,
  `tests/repository/test_release_contract.py`
