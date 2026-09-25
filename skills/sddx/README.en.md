# SDDx

[한국어](README.md)

## Purpose

Your current Claude Code or Codex session runs Superpowers SDD (split into
tasks, review, fix rounds), and only the coding goes to Cursor Agent or Grok
Build. Both use only Grok 4.7, never a `-fast` variant.

| Term | Meaning |
| --- | --- |
| Host | Claude Code or Codex, the program that runs the skill. The session that got `/sddx` or `$sddx` (the contract's orchestrator) hands out tasks, checks results, and runs reviews. |
| Worker | The outside CLI that codes and commits one task. |
| Brief | The one-task sheet a worker gets, with the plan's run-wide constraints. |
| Runner | `run_worker.py`, which starts the worker and records the attempt. |
| High / XHigh | Reasoning effort; XHigh thinks harder. |

## When to use and not use

- Use it only when an implementation plan file exists and your message
  contains `/sddx` (Claude Code) or `$sddx` (Codex).
- Not for writing a spec or plan, `writing-plans`, `executing-plans`
  (including Native), `pre-sdd-review`, plain SDD, coding in this session, or
  "implement this with Grok" without `/sddx` or `$sddx`.

## Supported hosts

sddx: Claude Code and Codex supported for local or repository-based use.

- Hosts are `claude-code` and `codex`. Cursor Agent and Grok Build are
  workers, not hosts.
- The OS is macOS only. Windows and Linux are unsupported, and the product
  CLIs refuse Windows.
- A Grok worker needs Python 3.11+ in a linked worktree (one added with
  `git worktree`). It turns off MCP call tools, and it will not run on a Grok
  CLI that lacks `--disallowed-tools` and `--deny`.
- Claude.ai, Cowork, Skills API upload, and marketplace publication are not
  supported.
- All four host/worker pairs have been run for real on macOS. What was
  checked is in
  [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md);
  shared limits are in the [compatibility guide](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Clone the repo, then make two shortcuts (symlinks): one for Codex, one for
Claude Code.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

The block below makes one link; the same link already there counts as
success. It does not replace a different link, dangling link, file, or
directory; it stops, so check the target and run it again.

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

Run it once per link. The first line is
`python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<'PY'` for Codex and
`python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<'PY'` for Claude
Code. Paste the block unchanged below it, end with a line that says only `PY`,
and keep the quotes.

To remove, check first, then remove only those links.

```bash
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx
```

The public path in `$skill-installer` form is below, but Codex finds this
skill through the `~/.agents/skills/sddx` link. It is not one of the three
skills in [Codex install](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-codex.md);
do not create a `~/.codex` or `~/.grok` copy.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/sddx
```

More notes are in [Local links](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

Use `/sddx` on Claude Code and `$sddx` on Codex. You can name the worker after
the plan file (`cursor`, `grok`, or `c`, `g` for short).

```text
/sddx docs/history/plans/example.md
$sddx docs/history/plans/example.md grok
```

## Expected result

1. Worker: if you named none, it asks once per plan, and confirms even when
   only one is available. If the chosen one is missing, it stops; it never
   switches on its own.
2. Each task gets a fresh worker and a brief; the worker never reads the whole
   plan.
3. Exit code 0 is not "done". The host checks the report, real test results,
   commits, and tool record (what the worker read and ran), then a reviewer on
   the host's own model reviews: High, or XHigh for concurrency, permission,
   secret, or sandbox changes and round 4-5 re-reviews.
4. Fix rounds 1-3 resume (continue) the same worker session if effort is
   unchanged; rounds 4-5 use a fresh XHigh worker.
5. Work outside the plan is asked about first. A needed push or publish stops
   as `BLOCKED`.

Each attempt leaves `run.json`, `report.md`, and the log in a folder under
`.superpowers/sdd/<plan>/` in the worktree. Watch progress with
`run_worker.py status`: session ID, whether the worker is alive (`pid_alive`),
and a short list of reads, searches, and shells. Do not paste the whole log.

| Situation | Result | What to do next |
| --- | --- | --- |
| Worker prints nothing for `--idle-timeout` (default 900 seconds; `0` = off) | Worker stopped, `timed_out`, exit 124, `the worker wrote no output for 900 seconds` | Check the worktree for leftover changes; do not resume that session; start a fresh worker with a brief naming the last report and commits. |
| Past `--timeout` (default `0` = no limit) | Worker stopped, `timed_out`, exit 124 | Check `status` and the report. |
| Ctrl-C or SIGTERM to the runner | `interrupted`; the worker is stopped too (SIGTERM, SIGKILL after ten seconds), exit 130 | Check for leftover background processes the worker started. |
| Out of balance (402), auth or permission failure | Attempt ends | Change the condition first; nothing retries automatically. |

To stop an attempt, stop the runner; do not signal the recorded worker pid or
use `pkill -f`. Commands and judgment rules are in the
[contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md).

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
