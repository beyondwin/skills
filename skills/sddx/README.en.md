# SDDx

[한국어](README.md)

## Purpose

It runs Superpowers SDD with the current Claude Code or Codex session as
orchestrator, and sends implementation only to Cursor CLI or Grok Build CLI.

## When to use and not use

Use it when an implementation plan exists and you want Superpowers SDD with
an external Grok or Cursor implementer.

Do not use it to write a spec or plan, to run `pre-sdd-review`, or for native
subagent-driven-development without an external implementer.

## Supported hosts

sddx: Claude Code and Codex supported for local or repository-based use.

The supported host ids are `claude-code` and `codex`. Cursor and Grok CLIs
are implementer workers, not hosts. This version has not been executed against
any of the four Claude Code / Codex by Cursor / Grok combinations with a real
provider. All four are `not_measured`. Observations from earlier versions are
records of those versions, not evidence for this one. The per-combination
measurement state is the table in the compatibility guide below. Claude.ai,
Cowork, Skills API upload, and marketplace publication are not supported.
Shared limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Task scope and review

The worker receives a complete task brief and listed references, without
reopening the full plan. Compare its scope-deviations report with actual tool
records. Role violations are FAIL; insufficient tool evidence is UNVERIFIED.
Neither qualifies for clean DONE.
`Search paths` limits content searches. Filename-only listings in the current
worktree and direct reads of task-needed ignore/build/test configuration are
allowed; these actions alone require no scope concern. Full-plan content and
secrets remain excluded.

Task reviews, scoped re-reviews, and final review all follow the current
orchestrator model. Select reviewer effort separately. On Claude Code, High
means the normal dispatch with no `model` argument; XHigh means dispatching
`subagent_type: sddx-reviewer-xhigh`, also with no `model` argument. Use XHigh
only for changes to locking, ordering, or concurrently shared state; changes to
an auth, permission, secret, or sandbox boundary; a round 4-5 re-review; or a
defect the reviews keep missing. Diff size, implementation difficulty, and
"this is the final review" are not reasons. The escalation definition is Claude
Code only; on a host without it, report that limitation and continue.

## Choosing and keeping a backend

In `sddx <plan-file> [cursor|grok|c|g]`, `c` means `cursor` and `g` means
`grok`. The backend comes from an explicit choice in this request, then the
current state of this same run, then one question. An explicit choice needs no
re-approval on later tasks. If only one backend is available, the skill shows
that fact and the missing backend's `reason`, and still confirms before
proceeding. If the requested backend is missing, it stops instead of switching.

From this major version, a Cursor CLI must declare headless print (`--print`
or `-p`), `--trust`, `--auto-review`, `--sandbox`, a confirmed `stream-json`
output format, and at least one Grok model id that a model-list command
actually returned. An existing Cursor install that does not meet this
resolves as `available: false` with `reason: missing_flags`. It no longer
falls back to `--force`/`--yolo` blanket approval, and no option brings that
back. An unavailable backend's `reason` is one of `not_found`,
`identity_mismatch`, `missing_flags`, or `no_grok_model`.

Changing backends never passes the previous provider's session ID along and
never resets the fix-round count. Reviews still inherit the current
orchestrator model, with effort selected separately and no `model` override.

## Execution helpers and evidence

To cut one task's section out of the plan, the controller runs
`scripts/extract_task.py <plan-file> --heading "<full heading without #>" --output <file>`.
Exit 0 is success, 2 is a file or argument error, and 3 means the heading is
absent, duplicated, or has an empty body. It never overwrites an existing
output file.

`scripts/run_worker.py run` is the only launch path. Do not hand-compose a
provider command or write a new execution script for a run. One attempt leaves
six files in a new directory under the worktree's `.superpowers/`: `brief.md`,
`dispatch.md`, `worker.jsonl`, `stderr.log`, `run.json`, and `report.md`. The
worker writes `report.md` itself; the runner never does. The runner never
prepares or cleans up the Grok profile. The controller keeps the order:
prepare, run, confirm the exit, clean up. There is no automatic retry anywhere.

Read a running or finished attempt only through `scripts/run_worker.py status`.
It is read-only and interprets nothing. The default answer is metadata, log
sizes, and whether `report.md` exists, never a log body. A body window needs
`--stream`; it defaults to 2048 bytes with a maximum of 8192, and the whole
JSON answer is capped at 64 KiB. Never dump a whole log into the session.

`run.json` holds process facts only. `state` is one of `starting`, `running`,
`exited`, `launch_failed`, or `interrupted`, which is process state and not
task state. Process exit 0 is not a clean DONE. The wrapper exit follows the
worker's; a POSIX signal returns `128 + signal` while `run.json.exit_code`
keeps the real negative return code; a launch failure is 2 and a handled
interrupt is 130. Exit 2 is ambiguous between a launch failure and a worker
that legitimately exited 2, so read `run.json.state` to tell them apart; if the
attempt directory is absent, or present without `run.json`, the launch was
refused before the attempt was created and the `BLOCKED:` line on stderr is the
reason.

The run's current state lives in one block at the top of the Superpowers SDD
ledger and nowhere else. Do not add a separate state file. Cursor has no
confirmed effort control, so `configured_effort` is `null` and the applied
effort is `unknown`; requested and configured effort are recorded separately
and neither proves what the model actually applied. A change to the shared
product source applies to new runs only — no run in progress is converted or
restarted automatically.

## Real measurement limits

On Windows, launching through an npm-style `.cmd` shim is recorded as a launch
failure. The worker rules and the Cursor dispatch text are multi-line and a
`cmd.exe` command line cannot carry a newline, so a recorded failure is
preferred over silent corruption. Windows argv transport itself was not
measured on this branch. Grok's `--rules` travels on the command line only and
is not stored among the attempt directory's six files, so editing
`references/worker-prompt.md` makes past Grok attempts non-reproducible from
the stored evidence alone. The full list of unmeasured items is in the
compatibility guide below.

## Grok worktree execution

Running the Grok backend in a linked worktree requires Python 3.11+.
SDDx prepares a working Git write profile so the worker can commit. Generated
configuration and recovery state are excluded from installation files and
commits; after the worker exits, SDDx restores the prior configuration or
removes the generated one.

## Install

Clone the repo, then make two links. The first link serves Codex. The second
serves Claude Code.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

The one-shot Python block below takes source and target as arguments. It first
validates that source is a skill directory and treats the same link as success.
It does not replace a different link, dangling link, file, or directory. It also
stops if the target appears after inspection, so inspect it before retrying.

<!-- sddx-local-links -->
```python
import os
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: python3 - SOURCE TARGET")
source = Path(sys.argv[1]).expanduser().resolve(strict=True)
target = Path(os.path.abspath(os.path.expanduser(sys.argv[2])))
if not source.is_dir() or not (source / "SKILL.md").is_file():
    raise SystemExit("source must be a skill directory")
if target.is_symlink():
    try:
        same = target.resolve(strict=True) == source
    except (OSError, RuntimeError):
        same = False
    if same:
        print("already linked")
        raise SystemExit(0)
    raise SystemExit("refusing different or dangling link")
if target.exists():
    raise SystemExit("refusing existing file or directory")
target.parent.mkdir(parents=True, exist_ok=True)
try:
    target.symlink_to(source, target_is_directory=True)
except FileExistsError:
    raise SystemExit("target appeared during installation; inspect it before retrying")
print("linked")
```

Put this block on standard input through a quoted here-document and run it once
per target. The Codex invocation starts with
`python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<'PY'`;
the Claude Code invocation starts with
`python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<'PY'`.
Place the Python block above unchanged on the following lines and close each
invocation with `PY` on its own line. Keep the source and target arguments
quoted.

Inspect the links first. Then remove only those exact links.

```bash
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx
```

`$skill-installer` names the public GitHub path. Codex still discovers
`~/.agents/skills/sddx`. Do not add this product to the three Codex-only
commands in `install-codex.md`. Do not create a `~/.codex` or `~/.grok`
duplicate.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/sddx
```

Shared install steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

Explicit calls are `$sddx` on Codex and `/sddx` on Claude Code.

```text
$sddx docs/history/plans/example.md
/sddx docs/history/plans/example.md
```

## Expected result

With an explicit backend choice the skill proceeds on it; otherwise it picks
one once for this plan. It then runs Superpowers SDD with an external
implementer and native reviewers. Every attempt leaves one evidence directory
and the ledger's current-state block, and completion is judged from the
report, real test exits, commits, the tool record, and native review — not
from a process exit.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
