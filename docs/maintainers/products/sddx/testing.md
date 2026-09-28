# sddx testing

This document records what checks SDDx and what has been measured so far with the
real CLIs. It owns the contract checks that run without a provider (Cursor or Grok
account), the `resolve_backend.py` fixture boundaries, Git sandbox prepare and
cleanup, and narrow live re-checks. It does not stretch live observations into
general provider quality or run guarantees on other hosts.

## What this document covers

- The checks that run now and what each test file locks: "Provider-free evidence"
- The check commands: "Commands"
- The manual XHigh reviewer check done every release: "Reviewer effort evidence"
- Measurements by version, newest first: "Measurement log". These are
  observations from that time and do not change the current contract.

Fixtures (fake inputs and repositories for tests) live in `tests/products/sddx/`.
In this document, "live" means a run that called the real Cursor or Grok CLI,
"synthetic CLI" means a fake CLI the test builds, and "RED → GREEN" means the test
failed first and passed after the implementation.

## Provider-free evidence

The required evidence is `python3 scripts/verify.py --skill sddx`. No check calls
a provider or uses a real Cursor/Grok account.

What each test file locks:

- `tests/products/sddx/test_resolve_backend.py`: puts fake binaries on PATH to
  lock the identity rules. The synthetic CLIs pin stdout/stderr to LF so raw-byte
  assertions do not mix with text conversion. Details are in "Deterministic
  checks" below.
- `tests/products/sddx/test_prepare_grok_sandbox.py`: builds a temporary repository
  and a real linked worktree, then checks Git path resolution, restoring the
  original TOML text, re-entry, symlink refusal, rewrite without `fchmod`, and CLI
  success and failure output. Git paths are normalized with pathlib before
  comparison. It uses the standard `tomllib`, so it needs Python 3.11 or later.
- `tests/products/sddx/test_extract_task.py`: locks heading match, body
  boundaries, exit 3 for duplicate, missing, or empty bodies, exit 2 for argument
  and file errors, and not overwriting an existing output file.
- `tests/products/sddx/test_run_worker.py`: checks the six files in the attempt
  directory, argv construction, the per-backend exclusivity of
  `--model`/`--sandbox-profile`, `run.json` fields (including `skill_version`) and
  states, recording `session_id` while running, wrapper SIGTERM → `interrupted`,
  ending the worker when the runner is interrupted and the kill on a second
  interrupt, installing the SIGTERM handler before launch, the idle timeout (a
  worker silent from the start, a worker that stops after output, including
  resume; stdout or stderr growth counts as activity; `--idle-timeout 0` turns it
  off; bad values are refused; a shorter `--timeout` wins), the defaults
  (`--timeout` 0, `--idle-timeout` 900), the wrapper exit rules, closed stdin,
  and attempt path refusal.
- `tests/products/sddx/test_worker_status.py`: checks `stale` (true only when
  running and the pid is gone), `session_id_in_log` (filled only when the record
  has no ID), read-only responses, `pid_alive`, a bounded tools index for both the
  Cursor and Grok log shapes, that the default response has no log body, skipping
  JSON lines that are too deep, `--stream` default 2048 and max 8192 bytes, the
  64 KiB response cap, and offset handling.
- `tests/products/sddx/test_contract.py`: checks doc and instruction wording and
  the plugin payload. The reviewer definition items are in "Reviewer effort
  evidence".

The generated `sddx-worktree` profile's `read_write` allows the linked worktree's
Git directory and the shared `.git` directory. That also grants write access to
other branch refs inside the shared `.git`. This check only confirms that a normal
single-controller run preserves existing file changes. It does not prove a
security boundary against malicious concurrent changes, or that the Grok sandbox
actually runs.

The Win32 transport fixtures were deleted.
The Windows `.cmd` round-trip check (`skipUnless(os.name == "nt")`) was deleted.
Neither was evidence of Windows support. Do not say they run in CI, and do not
treat a skip as a pass or as Windows support. Windows is unsupported.

A passing payload contract proves only file identity, portable frontmatter, and
forbidden strings. This provider-free evidence alone does not measure the live
CLI, billing, or model quality.

### Deterministic checks

The rules that `test_resolve_backend.py` and `test_run_worker.py` lock:

- The only Grok candidate is `grok` on PATH. With only `agent`, the result is
  `not_found`.
- `agent` is not adopted as Cursor.
- `cursor-agent` or `cursor` with a Grok identity is `identity_mismatch`.
- Cursor must declare headless print (`--print` or `-p`), `--trust`,
  `--auto-review`, `--sandbox`, and a confirmed `stream-json` output format. If any
  is missing, the result is `missing_flags`; it never falls back to force/yolo
  blanket approval.
- Cursor and Grok `--resume` must be declared as taking a value (`<id>` or
  `[id]`). A bare name with no value is `missing_flags`.
- The Cursor Usage line must have `[prompt]` or `[prompt...]`. Without it, the
  result is `missing_flags`, because `build_argv` appends the prompt as a
  positional argument.
- Cursor model list:
  - If the list command succeeded and ids were read but none is Grok, the result
    is `no_grok_model`.
  - If there are Grok ids but none has version segment `4.7`, the result is
    `no_grok_4_7`. Having only `-fast` ids is also `no_grok_4_7`.
  - `cursor-grok-4.6-*`, `cursor-grok-4.5-*`, and ids ending in `-fast` never
    enter `model_ids`, even when listed.
  - If no list command is declared or all fail, the result is `no_model_list`; if
    a list came back but no id could be read, it is `model_list_unreadable`.
- Ids are read from the `* id (default)` and `- id` bullets of Grok Build
  `models` output. `model_ids` is exactly `grok-4.7`. `grok-4.7-build-fast`,
  `grok-4.6`, and `grok-4.5` are dropped. Without `grok-4.7`, the result is
  `no_grok_4_7`.
- `run_worker.py` passes `--model` for both Grok and Cursor. For Grok, the effort
  flag stays next to it unchanged. A worker never starts with an id outside
  `model_ids`.
- ANSI color escapes in a model list are not part of an id. A colored list reads
  exactly like a plain one. The probe runs with `FORCE_COLOR=0`, `NO_COLOR=1`, and
  `CLICOLOR=0` added and inherits the rest of the environment. The two defense
  layers (the color-off environment and the parser's escape stripping) are
  independent, and `test_resolve_backend.py` pins each one.
  - Measured (cursor-agent 2026.09.15-d2fe57e): the parent environment's
    `FORCE_COLOR` decides coloring first, then whether stdout is a TTY. With
    `FORCE_COLOR=1`, 904 escapes appear even in a pipe, and `NO_COLOR=1`,
    `CLICOLOR=0`, or `TERM=dumb` do not stop them.
  - Reproduce with either `FORCE_COLOR=1 cursor-agent --list-models | cat -v`,
    or by making stdout a real TTY with `pty.spawn`. On that real output, the
    parser before the fix read 0 grok ids; the fixed parser read 14.
- If Grok help has no `--cwd`, the result is `missing_flags`.
- argv has no `--worktree` or `--plugin-dir`. The fixed Grok flags include
  `--disable-web-search`.
- The JSON for a missing backend has `launch` set to `null` and an empty
  `model_ids` list.

## Commands

```bash
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py
python3 scripts/release.py check --product sddx
python3 -m unittest tests.products.sddx.test_resolve_backend
python3 -m unittest discover -s tests/products/sddx -p test_prepare_grok_sandbox.py -v
git diff --check
```

`release.py check` passes only when the product's owned paths and the shared
release code are clean in the working tree, so run it after committing.

Live runs are local, explicit, optional, and may cost money. CI does not require
them. Do not describe an offline pass as host quality.

## Reviewer effort evidence

How to confirm that the XHigh reviewer definition (`agents/sddx-reviewer-xhigh.md`)
actually loads. There are two parts: an offline check and a live check every
release.

The provider-free evidence is the contract check in
`tests/products/sddx/test_contract.py`. It confirms:

- The `.claude-plugin` payload is allowed only for sddx and refused for other
  products.
- `plugin.json` names the product, its version equals the `release.toml` version,
  and it has no `agents` key.
- `agents/` has exactly one markdown definition, `sddx-reviewer-xhigh.md`; its
  `name` equals the file name, `effort` is `xhigh`, it has no `model` key, and
  `disallowedTools` names Edit, Write, and NotebookEdit.

This check only confirms the declared fields. It does not confirm that the host
actually blocks those tools.

The live check is done with the shipped product files linked.

- `claude plugin details sddx@skills-dir` must show Agents (1)
  `sddx-reviewer-xhigh`.
- Task starts with `subagent_type: sddx:sddx-reviewer-xhigh` and is not found by
  the bare name.
- Also check that `effort` in the child transcript's assistant events is `xhigh`.
- The skill invocation name is `sddx`.

Confirmed in `4.0.3`: `plugin details` showed Agents (1). The Task child record
had `effort: xhigh` (the parent session was high). Worker smokes with Cursor
`2026.09.15-d2fe57e` and Grok `1.0.34` both ended `state: exited` with report
`DONE`.

The contract check proves only that the file exists. It cannot prove that Claude
Code keeps loading agents from a skills-dir plugin, so repeat the live check above
every release. If it fails, the definition has silently disappeared, so stop the
release.

## Measurement log

Observations by version, newest first. Each entry is what was seen in that
environment and CLI version; numbers and verdicts are the values from that time.
Within a version, offline checks come first and live checks after.

### 7.0.0 offline checks

The required evidence for 7.0.0 is `python3 scripts/verify.py --skill sddx`. With
synthetic CLIs it locks:

- If neither log grows for `--idle-timeout`, the attempt ends `timed_out`, exit
  124, `the worker wrote no output for <N> seconds` (silent from the start,
  stopped after output, stopped mid-run, and resume).
- A worker that keeps writing, and one that writes only to stderr, do not end
  even past the window.
- `--idle-timeout 0` turns it off; negative, infinite, and NaN values are refused
  before the attempt is created.
- The idle timeout still applies when `--timeout` is given.
- The default `--timeout` is 0, a given `--timeout` still ends the attempt, and
  when both pass, `--timeout` comes first.
- The rule wording is on every face.

After this change, `sddx-contract` has 348 tests: `test_contract` 36,
`test_extract_task` 38, `test_prepare_grok_sandbox` 23, `test_resolve_backend`
75, `test_run_worker` 122, `test_worker_status` 54. The live check is in
"7.0.0 live check" below.

The 900-second default is based on real attempt records outside the repository
(their content is not committed). Cursor stdout carries `timestamp_ms` on every
event. Across 3 attempts (12 to 20 minutes), the longest gap between events was
63.7 seconds. Grok stdout has no timestamps, so the Grok session record for the
same `session_id` (1-second resolution) was used instead. The gap between tool
call completions stood in for the gap between stdout lines; this is an
approximation that assumes record time equals write time. Across 66 attempts
(longest about 68 minutes), the longest gap was about 265 seconds, and gaps spent
waiting on backgrounded builds or tests were 200 to 223 seconds. 900 seconds is
about 3.4 times the observed maximum. One attempt that hit the then-default
3600-second elapsed limit had a longest gap of 162 seconds by the same method; it
was cut off while working.

### 7.0.0 live check

2026-09-24, macOS 26.5.2 arm64, `grok 1.0.41 (4220f3b224a6) [stable]` with model
`grok-4.7` High, and Cursor Agent `2026.09.18-9a7762b` with model
`grok-4.7-high`. Four real calls in a linked worktree of a new local repository
with no remote. Each Grok attempt ran `prepare`/`cleanup` before and after, and
each returned `cleaned: true`. Elapsed time is `started_at`/`ended_at` from
`run.json`; silent gaps come from sampling both log sizes every 0.5 seconds.
Receipts and logs were not committed. Cost was not visible in the output.

| # | Worker · idle setting | Expected | Observed | Verdict |
| --- | --- | --- | --- | --- |
| LT1 | Grok, `--idle-timeout 30`, foreground `sleep 90` | `timed_out`, 124, `the worker wrote no output for 30 seconds`, 30 to 45 seconds after the last output | wrapper 124, `timed_out`, `exit_code` -15, same message, 41.6 seconds. Ended 30.7 seconds after the last log growth, `pid_alive: false`, no Grok in ps. Neither log grew during the foreground sleep, and the shell call was not in the index (same as the 6.0.0 observation). The zsh and `sleep 90` the worker started stayed under pid 1 and were cleaned up by pid | Pass |
| LT2 | Grok, default 900, small commit | `exited`, idle not triggered | `exited` 0, 78.1 seconds, 3 `shells` all exit 0, report present, longest gap between log growth 20.7 seconds | Pass |
| LT3 | Cursor, default 900, same task | `exited`, idle not triggered | `exited` 0, 82.5 seconds, 3 `shells` all exit 0, report present, longest gap 17.2 seconds. A `worker-server` process Cursor started during the attempt (working directory the fixture worktree) stayed adopted by pid 1 after the worker exited and was cleaned up by pid. The runner does not manage the process tree, so 7.0.1 added it to the examples of processes that outlive the worker | Pass |
| LT4 | Grok, `--idle-timeout 30`, background `sleep 90` then wait | Per the advice, commit past the window | wrapper 124, `timed_out`, -15, same message, 54.6 seconds. The background call was indexed right away (`sleep 90` in `shells`, `exit_code: null`), then the attempt ended after 30.4 seconds of silence. No commit; the leftover zsh and `sleep 90` were cleaned up by pid | Runner pass, advice not confirmed |

Observation: Grok records a backgrounded shell call right away, but writes nothing
while it waits on that work. So in this sample, backgrounding did not get past the
idle window. On the controller's call, 7.0.1 removed the background advice and
replaced it with one rule: if a brief has a command that will run longer than the
idle window, raise `--idle-timeout` above that command's expected duration before
launch. This result is an observation on this Mac with these two CLI versions.

### 6.0.0 offline checks

The required evidence for 6.0.0 is `python3 scripts/verify.py --skill sddx`. It
locks that a runner interrupt ends the worker and a second interrupt leaves no
`running`; that an attempt with no output ends `timed_out` after
`FIRST_OUTPUT_SECONDS` (including `--timeout 0` and resume, a shorter `--timeout`
wins, a worker that outputs right away is excluded); the default timeout of 7200;
Grok `tool_use` indexing without copying result bodies; and that each rule's
wording is on every face. The live check is in "6.0.0 live check" below.
After this change, `sddx-contract` has 342 tests: `test_contract` 36,
`test_extract_task` 38, `test_prepare_grok_sandbox` 23, `test_resolve_backend`
75, `test_run_worker` 116, `test_worker_status` 54.

### 6.0.0 live check

2026-09-24, macOS 26.5.2 arm64, `grok 1.0.41 (4220f3b224a6) [stable]`, model
`grok-4.7` High. Eight real calls in a linked worktree of a new local repository
with no remote. Each attempt ran `prepare`/`cleanup` before and after, and each
returned `cleaned: true`. Receipts and logs were not committed.

| # | Check | Result |
| --- | --- | --- |
| Past logs | Index comparison on the same logs as 5.0.0 (no calls) | Two real Grok logs went from reads/searches/shells 0/0/0 to 26/32/15 and 64/32/32 (`truncated`). Two real Cursor logs were unchanged |
| L1 | Tool index | `exited` 0, 70 seconds. `reads` 2 (brief, README), `searches` 1 (`PAPAYA`), 4 `shells` all exit 0 (including `echo hi`). No file bodies in status |
| L2 | Resume the L1 session | `exited` 0 with the same `session_id`, 77 seconds. No-output deadline not triggered |
| L3 | SIGTERM to the runner pid only | wrapper 130 immediately, worker process gone, `interrupted`, `exit_code` -15, `the runner was interrupted (SIGTERM or Ctrl-C)`, `pid_alive: false`. The zsh and `sleep 120` the worker started were adopted by pid 1 and stayed (the runner does not chase them); cleaned up by pid |
| L4 | Resume the interrupted L3 session | `exited` 0, 18 seconds. No stall |
| L5 | `--timeout 45` | wrapper 124, `timed_out`, `exit_code` -15, worker gone. The backgrounded `sleep 120` was recorded in `shells` with `exit_code: null`. Grandchild processes stayed as in L3 and were cleaned up by pid |

After the runner edge hardening (97a5eec), L1, L3, and L5 were run again. L1b was
`exited` 0 (185 seconds), with exit codes recorded for 11 `shells`, including one
that exited 1. L3b was wrapper 130 (1 second), worker gone,
`interrupted`/-15/new message; grandchild processes stayed and were cleaned up by
pid. L5b was wrapper 124, `timed_out`/-15, worker gone, grandchild processes
cleaned up by pid. Every `cleanup` returned `cleaned: true`.

Observation: Grok records the assistant message holding a shell call only after
that call returns or moves to the background. So a shell running in the
foreground, as in L3, is not in the index yet.

The no-output deadline itself is proven offline with a synthetic CLI. Reproducing
the real E3 stall was not a goal, and it did not appear in L4 either. This result
is an observation on this Mac and this Grok version; the Cursor path has offline
evidence only.

### 5.0.0 offline checks

The required evidence for 5.0.0 is `python3 scripts/verify.py --skill sddx`. It
locks that the resolver drops non-Grok-4.7 ids and `-fast` ids from `model_ids`,
and that Grok `run` passes `--model grok-4.7`. In this change,
`python3 scripts/verify.py` exited 0 and `sddx-contract` had 320 tests. A live
worker re-run is not required. The 4.0.3 XHigh loading and worker smoke were not
re-run for this version.

### 4.0.3 offline checks

The required evidence for 4.0.3 is `python3 scripts/verify.py --skill sddx`. The
definition file is `agents/sddx-reviewer-xhigh.md`, and `plugin.json` has no
`agents` key.

### 4.0.2 offline checks

The required evidence for 4.0.2 is `python3 scripts/verify.py --skill sddx`. It
locks that SKILL.md writes `subagent_type: sddx:sddx-reviewer-xhigh`.

### 4.0.1 offline checks

The required evidence for 4.0.1 is `python3 scripts/verify.py --skill sddx`.
`test_resolve_backend.py` locks a `--resume` that takes no value, and a Cursor
Usage with no positional prompt, as `missing_flags`. A live worker re-run is not
required. The live result for XHigh definition loading is in "Reviewer effort
evidence" above.

### 4.0.0 offline checks

The required evidence for 4.0.0 is `python3 scripts/verify.py --skill sddx`. The
expect lock in `tests/products/sddx/test_contract.py` locks the description,
HARD-GATE, and cases wording. `tests/products/sddx/test_extract_task.py` locks
`--global-constraints` concatenation, absence, duplicates, empty bodies, and exit
3. A live worker re-run is not required.

### 2.0.0 verification

Evidence is recorded in four kinds, and one never stands in for another.

| Evidence kind | Status in this version |
| --- | --- |
| Offline helper and argv contract checks | Run |
| Instruction wording checks | Run |
| Native behavior probes | Not newly run in this version |
| Real provider runs | All four pairs run (`measured`). [Compatibility](compatibility.md) owns the per-pair and per-item status |

In this version, with the product owner's approval, real providers were called in
the two pairs with Claude Code as the host. Both were on macOS 26.6.2 arm64.

Cursor ran three worker attempts with `cursor-agent 2026.09.10-fd3934a` and model
`cursor-grok-4.6-high`, observing approval behavior, model ID acceptance and the
`configured_effort` record, session ID recovery and `--resume`, a real worker
timeout, and refusal before the attempt is created.

Grok ran two worker attempts with `grok 1.0.30 (04b7ffed98c6)` and no model
argument (the init event reported model `grok-4.6`), and ran one full round of
sandbox profile prepare and cleanup.
It observed the real shape of the `streaming-messages-json` stream, that
`--reasoning-effort` was on the command line, and session ID recovery and
`--resume`.

The effort the model actually applied was not observed in any pair, so it stays
`not_measured`. Requested or configured effort is not evidence of the applied
value; neither is the provider accepting a model ID, nor the requested effort
being on the command line. Whether the CLI enforces the worker boundary is also
`not_measured`. The Grok init event listed `spawn_subagent` in its tools even
after `--no-subagents` was passed; both attempts kept the rule because the model
followed instructions. Worker runs under the Codex host were not run, so they
stay `not_measured`. Windows is unsupported and is not a `not_measured` OS in the
queue. The results of the two observed pairs are not stretched to the others.
[Compatibility](compatibility.md) owns the per-pair table and the per-item
measurement status.

#### Actual observations

The discovery check in `tests/products/sddx/` (`sddx-contract`) passed with 281
tests. There is no `skipUnless(os.name == "nt")` check.
By file: `test_contract` 26, `test_extract_task` 29,
`test_prepare_grok_sandbox` 23, `test_resolve_backend` 58,
`test_run_worker` 101, `test_worker_status` 44. The earlier count of 45 SDDx
tests was from before the new Task 1–4 files entered discovery; 212 was from
before this version's session ID recovery and attempt timeout work; and 269 was
from before the running `session_id`, `pid_alive`, and tools index.

The `python-compile` stage arguments that `verify.py` printed include
`skills/sddx/scripts`, so `extract_task.py`, `run_worker.py`,
`resolve_backend.py`, and `prepare_grok_sandbox.py` are all compiled in that
stage.

The `product-contract` stage passes. During the work, the `EXPECTED` table in
`tests/repository/test_release_contract.py` pinned sddx to the previous version
string, so `test_each_product_owns_an_independent_release_manifest` disagreed
with the new version in `release.toml`. This change updated only the sddx row of
that table to the new version and left the other product rows alone. After the
update, `product-contract` passes with 24 tests. When bumping the product
version, include that row in the same change.

All four Step 3 commands exit 0 in the final state.

| Command | exit |
| --- | --- |
| `python3 scripts/verify.py --skill sddx` | 0 |
| `python3 scripts/verify.py` | 0 |
| `python3 scripts/release.py check --product sddx` | 0 |
| `git diff --check` | 0 |

`release.py check` passes with no output. It passes only when the product's owned
paths and the shared release code are clean in the working tree, so run it after
committing.

The product check ran all three stages: `product-contract`, `sddx-contract`, and
`python-compile`. The full check ran and passed all 12 stages:
`repository-contract` 361, `korean-package` 9, `korean-offline`,
`korean-live-unit` 244, `korean-live-dry-run`, `image-contract`,
`image-inspector` 48, `how-it-works-contract` 56, `pre-sdd-review-contract` 54,
`pre-sdd-review-evidence` 61, `sddx-contract` 281, `python-compile`.
All other product stages pass on the new version, which confirms this version
change did not touch other products. Passing every offline stage is still not
evidence of a real provider run.

### 2026-09-14 MCP follow-up regression check

The "2.0.0 verification" section covers Claude Code observations up to `bfd1cda`.
This section records the checks added with the MCP tool filter, and the live
check re-run in this repository afterward.

The new provider-free checks confirm, in a real synthetic child process:

- Only Grok gets the two Cursor/Claude MCP discovery environment variables set to
  `0`; parent and unrelated environment variables are preserved. The Cursor
  environment and argv policy are also preserved.
- Grok argv passes the `search_tool,use_tool` exclusion and the `MCPTool(*)`
  denial. If a needed option is missing or takes no value, the resolver returns
  `missing_flags`.

In the cause-isolating live probe, a call with only the MCP compatibility
environment variables turned off had 0 handshake warnings, and a call with only
the tool exclusion option had 4 `handshake failed`. The early candidate call that
combined both ran read_file and ended with exit 0, and that candidate's tool list
dropped spawn_subagent/search_tool/use_tool together. That list belongs to the
discarded candidate, not to the filter that shipped. Excluding `Agent` and the
internal `task` also removed the command result lookup and kill tools. Excluding
only the `spawn_subagent` label left the tool in place. So the final change adopts
only the `search_tool,use_tool` exclusion and keeps the command lookup and kill
tools. The subagent boundary keeps the existing `--no-subagents` and worker
instructions and does not claim tool removal. The MCP server lists in `inspect`
and init kept showing the import targets, so those lists are not used as evidence
of a real connection.

Raw provider records are kept locally only and are not committed.

#### Live re-check before merge

Four more real calls in the same working tree. Grok did one round in a linked
worktree: `prepare` → new → `--resume` → `cleanup`. Cursor did new and resume in
another worktree from the same seed. All four attempts had wrapper exit 0,
`state: exited`, and `exit_code: 0`, and each committed the implementation and
then wrote `report.md` itself. The two attempts in each round reported the same
`session_id`.

The `read_write` that Grok `prepare` built held the real Git directory and the
shared Git directory, and the worker committed directly inside that linked
worktree. `cleanup` returned `{"cleaned": true}` and removed the `.grok` it made.

After the follow-up, the 23 tools in the Grok init event had no `search_tool` or
`use_tool`, while `spawn_subagent`, `get_command_or_subagent_output`, and
`kill_command_or_subagent` remained. New and resume were the same. The three MCP
servers still showed as connected.

All four attempts had 0 bytes of stderr. Grok attempts in this repository before
the follow-up were also 0 bytes, so the effect of the MCP discovery environment
variables cannot be separated here. The observation that handshake failures
dropped comes from Codex's cause-isolating probe record and was not reproduced in
this repository.

In one attempt, the brief named a wrong discovery command with `-t .` added. The
worker actually ran it and saw exit 1, wrote the cause (`tests/` has no
`__init__.py`) and the named command's real exit code in the report, and then
produced RED exit 1 → GREEN exit 0 again with a valid method. The status was
`DONE_WITH_CONCERNS`. This is a small-sample observation of role compliance, not
evidence of enforcement.

`python3 scripts/verify.py` exited 0, and the full provider-free check including
266 SDDx tests passed. The 361 repository checks also passed. Each new test was
confirmed to fail on its matching source mutation: narrowing the tool filter
value, removing the option check, reverting the percent-variable check, removing
the environment pass-through in `Popen`, and applying the environment variables to
Cursor too. All five mutations were caught, and the source was restored to the
SHA-256 values recorded in [Compatibility](compatibility.md).

### 1.0.3 file name and config lookup clarification

Listing file names in the current worktree, and directly reading the ignore,
build, and test config a task needs, are now stated as allowed checks. That
behavior alone does not require a scope concern or a ruling. The path limit on
content search, the ban on the plan body, and UNVERIFIED for missing records stay.

In independent native contexts, 5 samples each before and after the
clarification were classified for file name lookup, direct config reads, real
plan content exposure, and missing tool records. On real Grok, one task asked
together for file name and config lookups plus native grep or shell rg on a path
with spaces, and the report's classification was compared with the real result.
This check observes an instructed situation; it does not prove a natural
compliance rate or OS-level access blocking.


#### Actual results

The 5 native samples before the clarification classified file name and config
lookups as AMBIGUOUS in every case; the 5 after classified them all as explicit
ALLOWED / none. Plan content exposure FAIL and missing-tool-record UNVERIFIED
stayed. These samples were separate contexts with no prior response, not a model
compliance statistic.

Two new Grok sessions got the final worker rules and dispatch boundary. Both tasks
listed root file names, directly read .gitignore and the usual test config, ran a
real content search, recorded these in the report, and finished DONE / Scope
deviations: none. Native grep named the source and test paths separately, and
shell rg quoted two paths containing spaces. The search term was also placed in
the plan and in an out-of-scope note, but no body text came back.

The native task went RED 10 tests/4 failures/exit 1 → GREEN 10/exit 0, and the
shell task RED 8 tests/4 failures/exit 1 → GREEN 8/exit 0. The independent final
tests were also 10 and 8 with exit 0, using the python3 confirmed from the config.
Each worker committed only the named source and the two new test files directly,
and Git status was clean.

Tool calls and results for the two tasks were 22/22 each, and restoring the
original sandbox text, 0640 permissions, and journal removal were confirmed. The
native task looked up .git as a directory, got an IsAFile error, then read the
one-line worktree pointer and followed the normal Git commit steps. The pointer
lookup was in the original report, and the ListDir error was confirmed in the
original tool record. It did not go on to read the contents of the pointer's
target.

The hashes of the 6 runtime files were the same before and after the calls. The
full provider-free check was 868 unittests plus extra checks, exit 0; the product
check was 24 contract tests, 45 SDDx tests, and compile, exit 0. The final
observation doc is checked for content, links, and diff. Earlier versions'
failure and ambiguity records are not overwritten by this new result.

### 1.0.2 extra search check and remaining ambiguity

With the wording of main `2e9036a`, two new Grok sessions were asked to run a real
content search. Native grep searched the named source and test paths separately
and returned 5 and 4 lines of body text; shell rg quoted two paths containing
spaces and returned 9 lines from 4 files. The same search term was placed in the
plan and an out-of-scope note, but that content did not come back. Independent
tests were 12 and 9 with exit 0, and tool results matched 20/20 and 18/18.

The classification of file name lookups was ambiguous. The earlier worker reported
the root listing and ignore-rule lookup as a concern, and an extra shell run
reported none after a root listing. The independent review found no plan body
exposure, but judged that wording mixing `any search` and `content search` left
the reporting standard for file name lookups and needed direct config reads
unclear. The verdict and original reports from that time are kept after the fix.

### 1.0.2 verification procedure

Run the [behavior probes](../../../../tests/products/sddx/behavior-probes.md) for
model inheritance, High/XHigh, violation reporting, missing tool records, and plan
link scenarios in independent native contexts. Wording checks, real behavior
checks, and real Grok runs are different kinds of evidence.

Live runs use the same function → a controlled same-session fix → a new CLI task.
The full plan stays in the fixture to measure the behavior of not reading it. The
brief is complete with the needed conditions, and both the worker rules and the
dispatch boundary are passed. Each call checks real read and shell output, scope
deviations, the real test exit, worker commits, session ID, and restoration of the
original sandbox text and permissions. Reviews inherit the same orchestrator
model, set effort separately, and record why it was chosen. The role read limit is
still a prompt instruction, not an OS file access block.

#### Search exposure found while writing 1.0.2

When the first candidate ran the three steps, the function and resume steps showed
role compliance, but the CLI task pulled two lines of the plan through a workspace
`grep` with no target path. If search results return plan content, that is a role
FAIL even without opening it with ReadFile. This worker disclosed it under scope
deviations and returned DONE_WITH_CONCERNS, so the reporting improvement was
confirmed. The first candidate's final app had 14 tests, a commit, and a
successful restore; that run's own verdict stays partial pass.

Based on this, the brief gained concrete Search paths and an order for direct
reads of named files. It now states that a file glob alone does not set a
directory boundary. The controller's evidence extraction also uses a separate
local verification tool, extended to keep every tool result including search
results. This did not add a new execution engine to the product. The previous
candidate's source hashes, original text, and failure logs were kept, and the
three steps were verified again with the final wording in a new worktree.

#### Real verification of the final wording

A new linked worktree from the same seed called Grok three times. The SHA-256 of
the 6 final runtime files (skill, worker rules, dispatch, helpers, and so on) was
pinned before the calls and confirmed to match afterward. The function went RED
exit 1 → GREEN 8 tests/exit 0; the controlled same-session fix RED 9 tests/6
failures/exit 1 → GREEN 9/exit 0; the new CLI RED 6 tests/4 failures/exit 1 → full
GREEN 15/exit 0. No wrapper was used. The final independent check was also 15
tests/exit 0, full diff check exit 0, and a clean fixture.

The three workers' direct commits were limited to the 5 task files. Restoring the
original sandbox text and 0640 permissions, journal removal, and real session
reuse and switching were confirmed. All tool calls and results matched 14/14,
12/12, and 16/16, and the final three calls had no plan content reads or
workspace content searches. They used the needed direct file reads, so this does
not prove the search tool's own path limiting or forced file access blocking.

The last worker disclosed a root file name listing and a .gitignore read as
DONE_WITH_CONCERNS. The independent review and the existing controller ruling
accepted these as non-blocking observations incidental to committing and checking
the repository. The real listing did include the plan file name, but no content
came back. The original report and the Minor procedure interpretation notes are
kept. The earlier candidate's real plan content search exposure stays FAIL. The
Grok calls in this improvement work were 6 in total, the first 3 plus the 3 with
the final wording, and they are not merged into one failure-free run.

The real orchestrator, confirmed from the run record, was gpt-6-astra/XHigh, and
every native review omitted the model argument to inherit it. Local Task reviews
and re-reviews were High; the full policy and evidence review was XHigh. This is
not a policy of pinning a specific model. After the final wording landed, the full
provider-free check was 868 unittests plus extra checks, exit 0, and the later
observation doc is checked for content, links, and diff.

### 1.0.1 follow-up failure reproduction

Against the same product HEAD `6cc1e39`, Grok was called three times in each of
two new local linked-worktree fixtures. In the first follow-up fixture, both new
sessions read the full plan; the next main-based fixture reproduced this in the
CLI's new session. The exact worker rules were passed, and a real successful read
result returned the plan body, so this cannot be explained as missing rule
delivery. The worker's clean DONE report also left out the violation.

The final app tests in the two fixtures were 15 and 14 with exit 0, and each had 3
direct worker commits. The original text and 0640 permissions of the existing
sandbox TOML with CRLF and comments matched after every call, and the journal was
removed. Separate from the app's success, role compliance was FAIL, and the
independent final review also judged it a partial pass. The earlier first success
sample does not offset this follow-up failure. MCP initialization warnings are
kept separate from real MCP tool calls by the model.

The initial empty fixture records Python 3.14 unittest's NO TESTS RAN/exit 5 as
unmeasured. A real non-zero test inside a shell wrapper exit 0 is not counted as
a pass either. Local raw provider traces and receipts are not committed to the
repository.

### 2026-09-11 1.0.1 first Grok check

The environment was macOS 26.5.2, Python 3.14.7, a Codex controller, Grok 1.0.25,
and `grok-4.6` High. In a linked worktree of a new local repository with no
remote, the steps were:

1. Check the resolver and sandbox helper from the changed product, running
   `prepare` before each call and `cleanup` after the worker ends.
2. In the first task, have the worker directly commit a Unicode whitespace
   normalization implementation and tests.
3. Send the same worker session a controlled request to add a TypeError message
   and equality tests, and repeat the native scoped review after the fix commit.
4. Run a CLI task in a new session and confirm the worker's third direct commit.
5. In the fixture, check `python3 -m unittest discover -s tests -v`,
   `git diff --check` with the base and result commits as arguments,
   `git status --short`, the changed file list, and recent commits.

There were three real provider calls, all ending with worker exit 0, cleanup exit
0, report `DONE`, and a direct worker commit. The first task ran RED exit 1 with
one loader-error test (because `textnorm` did not exist before implementation),
then GREEN 7 tests exit 0; the controlled same-session fix went RED 8 tests exit
1, then GREEN 8 tests exit 0; the second task went RED 14 tests exit 1, then
GREEN 14 tests exit 0. For the second task's RED/GREEN, the real test exit inside
the shell wrapper's exit 0 was checked separately. No defect in the original
implementation was found; the same-session change verified resume behavior for a
pre-approved extra request.

The final independent unittest was 14 tests, exit 0, and `git diff --check` over
the full commit range also exited 0. The worktree was clean, and the three worker
commits held only the five required application, test, and README files. The
controller did not modify the implementation or help with commits. The generated
sandbox config and restore record were cleaned up; byte preservation of the
existing config was proven by the provider-free check, not the live fixture.

A manual review of the real tool trace confirmed the brief-first order, and
observed no external skill or full plan reads, nested agents, MCP tool calls, or
role violations. The existing host integration's MCP initialization, handshake,
and auto-restart warnings kept appearing. These warnings differ from the model's
MCP tool calls, and there is no guarantee they go away.

The independent whole-fixture native review re-checked the clean checkout, the
absence of the generated config and journal, the worker-owned commit range, the
same-session fix and new task session, and the independent 14-test log, and
accepted with 0 Critical/Important/Minor findings.

At the product implementation HEAD, `python3 scripts/verify.py` finished the full
provider-free check including 868 unittests, exit 0. Later changes were docs
only, so the full suite was not repeated; content, links, and diff were checked.
Cursor worker and Claude Code host runs are `not_measured`.

### Behavior probes

For the [behavior probes](../../../../tests/products/sddx/behavior-probes.md), the
controller manually judges the behavior a native model proposes in independent
contexts with no prior response. On 2026-09-11, all 5 controller scenarios passed
the completion verdict, sandbox failure, and session reuse and switching criteria.
In a separate synthetic worker-role sample, proposals to read an external skill
dropped from 2/5 at baseline to 0/5 after applying the candidate worker guidance.
All five guided responses read `candidate-worker.md`; the final role sentence and
content were the same, but the order and formatting of the existing paragraphs
differed. This result is not a string check, and a small native simulation is not
treated as a real Grok call or a runtime reliability statistic.
