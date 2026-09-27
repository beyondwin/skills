# Waygent

[한국어](README.md)

## Purpose

A light workflow that runs an implementation plan one task at a time. The
session that receives `/waygent` or `$waygent` (the controller) does not write code. For each
task it starts one fresh implementer subagent and hands it a short brief plus a
shared guide file.

| Term | Meaning |
| --- | --- |
| controller | The session that got `/waygent` or `$waygent`. It hands out tasks, checks results, and keeps the progress file. |
| implementer subagent | A fresh subagent that writes the tests first, implements one task, and commits it. |
| guide file | `guide.md`, written once: test and lint commands and the plan's global rules. Every implementer reads it. |
| progress file | `progress.md`, the per-task state. It is never committed. |
| review records | `reviews/task-N.md` and `reviews/final.md`, the full findings each reviewer writes. The controller gets only the short list. |

## When to use and not use

- Use it for a multi-task implementation, only when your message contains
  `/waygent`. With no plan file, it writes a task list from your request and
  asks once before starting.
- Do not use it for brainstorming, writing a design, spec, or plan, a single
  small fix, `/sddx`, or Superpowers `subagent-driven-development`.

## Supported hosts

waygent: Claude Code, Codex, and Cursor Agent supported for local or repository-based use.

- The host ids are `claude-code`, `codex`, and `cursor`. The host must be able to start
  subagents. Codex needs `multi_agent = true` under `[features]` in
  `~/.codex/config.toml` for its subagent tool (`spawn_agent`).
- Measured on 2026-09-27 (Claude Code opus/fable, Cursor Agent grok-4.7-high). Records:
  [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md).
  Codex records are in the same doc.
- The OS is macOS only. Windows and Linux are unsupported.
- Use it inside a Git repository.
- Claude.ai, Cowork, Skills API upload, and marketplace publication are not
  supported. Shared limits are in
  [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Clone the repo, then make a shortcut (symbolic link). Claude Code looks in
`~/.claude/skills`, Codex in `~/.agents/skills`, and Cursor Agent in `~/.cursor/skills`.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills
```

The block below creates one link and treats the same link as success. It does
not replace a different link, dangling link, file, or directory; it stops, so
inspect the target before retrying.

<!-- waygent-local-links -->
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

Run it once per link. For Claude Code the first line is
`python3 - "$PWD/skills/waygent" "$HOME/.claude/skills/waygent" <<'PY'`; for
Codex it is
`python3 - "$PWD/skills/waygent" "$HOME/.agents/skills/waygent" <<'PY'`; for
Cursor Agent it is
`python3 - "$PWD/skills/waygent" "$HOME/.cursor/skills/waygent" <<'PY'`. Paste
the block unchanged on the following lines and end with `PY` on its own line.

To remove, inspect first and remove only that link.

```bash
ls -ld ~/.claude/skills/waygent ~/.agents/skills/waygent ~/.cursor/skills/waygent
unlink ~/.claude/skills/waygent
unlink ~/.agents/skills/waygent
unlink ~/.cursor/skills/waygent
```

The public path in `$skill-installer` form is below, but Codex finds this
skill through the `~/.agents/skills/waygent` link. It is not one of the three
skills in [Codex install](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-codex.md);
do not create a `~/.codex` copy.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/waygent
```

More is in [Local links](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

Claude Code and Cursor Agent use `/waygent`; Codex uses `$waygent`. Give a plan
file, or write a request with no plan.

```text
/waygent docs/plan.md
$waygent docs/plan.md
/waygent Add a show-password button to the login form
```

## Expected result

1. On `main` or `master` it creates a `waygent/<plan-slug>` branch. It never
   commits to `main` or `master`, and never pushes, merges, or opens a PR.
2. For each task a fresh implementer writes a test, sees it fail, then
   implements. The commit carries a `Waygent-Task: N` trailer.
3. Each task gets one review, and findings get one fix. There is no re-review.
4. After the last task there is one full review, its fixes, and one more run of
   the suite.
5. On a failure it writes down one cause first and retries once. A second
   failure stops the run with a report.
6. Implementers and per-task reviewers use the same model as this session, never
   a cheaper model or lower effort. When the host can pick the model, only the
   final review and the retry after a failure go one tier up (Claude Code:
   sonnet → opus → fable). On Codex the dispatch names no model, so the child
   inherits the session's; one tier up sets only
   `reasoning_effort` to `xhigh`. No subagent starts subagents of its own.

Records live at the repository top level in `.waygent/<plan-slug>/`
(`progress.md`, `guide.md`, `reviews/`). `.waygent/.gitignore` (the line `*`)
keeps the folder out of git, so nothing is committed and your `.gitignore` is
not touched. Call `/waygent` (Codex: `$waygent`) again to resume. A task with a trailer commit
is done and is not redone. Uncommitted changes are not discarded; they go to a
fresh implementer. On a usage limit it writes `paused: limit` and stops. If `git clean -fdx`
removes the records, progress is rebuilt from the trailer commits.

Deliberately left out: brainstorming and spec phases, per-task brief files,
re-review loops, parallel implementers, and a human checkpoint per task.

Limits: with one review per task, fixed code is seen again only by the final
review. Result quality depends on the model and the plan. The rules are in the
[contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/contract.md).

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/release.md)
