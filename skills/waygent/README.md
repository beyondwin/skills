# Waygent

[한국어](README.ko.md)

## Purpose

A light skill that runs an implementation plan to the end. Each task gets a fresh
subagent that writes the tests first, then the code. Each task gets one review, and
the whole branch gets one final review. The main session writes no code; it hands
out work and checks results, so its context stays small.

```text
/waygent docs/plan.md
  │
  ├─ Task 1 ─ implementer (fresh subagent): failing test → code → commit
  │           reviewer: one look; High and Medium fixed once (no re-review)
  ├─ Task 2 ─ …
  │
  └─ end ──── one full review (one model tier up) → fixes → tests → 15-line report
```

The design comes from measurement: a 10-task plan run in isolation with no skill,
with superpowers, and with waygent
([design and evaluation](https://github.com/beyondwin/skills/blob/main/docs/research/2026-09-waygent-eval/README.md)).

- Current models get most of it right alone, so rules sit only where a model alone
  goes wrong.
- A single session left a hidden state defect in all 5 runs. A fresh implementer
  and a review per task fixed it in 11 of 14.
- Same quality as superpowers at less than half the cost and time.

| Term | Meaning |
| --- | --- |
| main session | The session that got `/waygent`. It hands out tasks, checks results, and keeps the records. |
| implementer | A fresh subagent for one task. It writes the tests first and commits. |
| reviewer | A fresh subagent that reads one task's diff once and reports High, Medium, and Low findings. |

## When to use and not use

- Use it for a multi-task implementation. It turns on only when your message
  contains `/waygent` (Codex: `$waygent`). With no plan file, it writes a task list
  from your request and asks once.
- Do not use it for brainstorming, writing a design, spec, or plan, or a single
  small fix. Not with `/sddx` or Superpowers `subagent-driven-development` either.

## Supported hosts

waygent: Claude Code, Codex, and Cursor Agent supported for local or repository-based use.

| Host | Call | Install path | Subagents |
| --- | --- | --- | --- |
| Claude Code (`claude-code`) | `/waygent` | `~/.claude/skills/waygent` | Agent tool |
| Codex (`codex`) | `$waygent` | `~/.agents/skills/waygent` | `spawn_agent`; needs `multi_agent = true` under `[features]` in `~/.codex/config.toml` |
| Cursor Agent (`cursor`) | `/waygent` | `~/.cursor/skills/waygent` | Task tool |

- macOS only, inside a Git repository.
- Per-host measurements are in
  [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md).
  Shared limits are in
  [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Clone the repo, then make one shortcut (symbolic link) per host you use.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills
```

The block below makes one link. An identical link is left alone; any other file or
link stops it untouched.

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

Change only the first line per host, paste the block on the following lines, and end
with `PY` on its own line.

- Claude Code: `python3 - "$PWD/skills/waygent" "$HOME/.claude/skills/waygent" <<'PY'`
- Codex: `python3 - "$PWD/skills/waygent" "$HOME/.agents/skills/waygent" <<'PY'`
- Cursor Agent: `python3 - "$PWD/skills/waygent" "$HOME/.cursor/skills/waygent" <<'PY'`

Because it is a link, `git pull` in the repo updates it. To remove, check first and
remove only the link.

```bash
ls -ld ~/.claude/skills/waygent ~/.agents/skills/waygent ~/.cursor/skills/waygent
unlink ~/.claude/skills/waygent
unlink ~/.agents/skills/waygent
unlink ~/.cursor/skills/waygent
```

The public path is below. On Codex, too, use the `~/.agents/skills` link above
rather than a copy under `~/.codex`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/waygent
```

More on links is in [Local links](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

```text
/waygent docs/plan.md
$waygent docs/plan.md
/waygent Add a show-password button to the login form
```

- With a plan file it follows the plan's task order; without one it shows a task
  list first.
- If a run was cut off, send the same command again. Finished tasks are skipped.
- A plan that names its test command and its rules gets better results.

## Expected result

**git**
- On `main` or `master` it first creates a `waygent/<plan-slug>` branch.
- One commit per task, each ending with a `Waygent-Task: N` trailer.
- No push, merge, or PR.

**Records** (not tracked by git)

```text
.waygent/
  .gitignore              # the line "*": keeps the folder out of git
  <plan-slug>/
    progress.md           # per-task state, rulings, failure causes
    guide.md              # test command and the plan's shared rules; implementers read it first
    reviews/task-N.md     # the reviewer's full findings
    reviews/final.md
```

**When done**: a report of at most 15 lines: tasks and commits, findings fixed or
overruled, the final test result, and anything not verified.

**When something goes wrong**
- A failed task gets one written cause and one retry. A second failure stops the run
  with the reason.
- On a usage limit it writes `paused: limit` and stops. Call it again to continue.
- Uncommitted work is never discarded; a fresh implementer continues it. If
  `.waygent/` is deleted, progress is rebuilt from the `Waygent-Task` commits.

**Models**
- Implementers and per-task reviewers use this session's model, never a cheaper one.
- Only the final review and the retry after a failure go one tier up: Claude Code
  goes sonnet → opus → fable; Codex keeps the model and sets `reasoning_effort` to
  `xhigh`. Cursor cannot pick, so it uses the same model.

**Not done**: brainstorming or spec phases, re-review loops, parallel implementers,
a human checkpoint per task, generated docs, edits to `CLAUDE.md` or `AGENTS.md`.

**Limits**: fixed code is seen again only by the final review. Results depend on the
model and the plan.

## See also

- [Design and evaluation](https://github.com/beyondwin/skills/blob/main/docs/research/2026-09-waygent-eval/README.md): why it works this way, with numbers
- [CHANGELOG](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/contract.md) · [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/testing.md) · [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md) · [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/release.md)
- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
