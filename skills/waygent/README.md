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
  └─ end ──── one full review (one model tier up) → fixes → app check → tests → 15-line report
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

waygent: Claude Code, Codex, Cursor Agent, and Grok Build supported for local or repository-based use.

| Host | Call | Install path | Subagents |
| --- | --- | --- | --- |
| Claude Code (`claude-code`) | `/waygent` | `~/.claude/skills/waygent` | Agent tool |
| Codex (`codex`) | `$waygent` | `~/.agents/skills/waygent` | `spawn_agent`; needs `multi_agent = true` under `[features]` in `~/.codex/config.toml` |
| Cursor Agent (`cursor`) | `/waygent` | `~/.cursor/skills/waygent` | Task tool |
| Grok Build (`grok`) | `/waygent` | any of the three links above; no extra link | `spawn_subagent` |

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

Claude Code, optional: link the final reviewer's agent definition too. With it, the
final review runs on opus at xhigh instead of fable; without it, fable as before.
Run this block the same way, with the first line given under it.
It never replaces an existing file or link.

<!-- waygent-agent-link -->
```python
import os
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: python3 - SOURCE TARGET")
source = Path(sys.argv[1]).expanduser().resolve(strict=True)
target = Path(os.path.abspath(os.path.expanduser(sys.argv[2])))
if not source.is_file() or source.suffix != ".md" or source.parent.name != "agents":
    raise SystemExit("source must be an agent definition file")
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
    target.symlink_to(source)
except FileExistsError:
    raise SystemExit("target appeared during installation; inspect it before retrying")
print("linked")
```

- Agent link: `python3 - "$PWD/skills/waygent/agents/waygent-final-reviewer.md" "$HOME/.claude/agents/waygent-final-reviewer.md" <<'PY'`

Because it is a link, `git pull` in the repo updates it. To remove, check first and
remove only the link.

```bash
ls -ld ~/.claude/skills/waygent ~/.agents/skills/waygent ~/.cursor/skills/waygent ~/.claude/agents/waygent-final-reviewer.md
unlink ~/.claude/skills/waygent
unlink ~/.claude/agents/waygent-final-reviewer.md
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
  `/waygent` alone picks up the one unfinished run, and asks once if there are several.
- A finished run is only reported; new work needs a new `/waygent <request>`.
- A plan that names its test command and its rules gets better results.

## Expected result

**git**
- On `main` or `master` it first creates a `waygent/<plan-slug>` branch.
- One or more commits per task in the repository's message format; the last one
  ends with a `Waygent-Task: N` trailer.
- No push, merge, or PR.

**Records** (not tracked by git)

```text
.waygent/
  .gitignore              # the line "*": keeps the folder out of git
  <plan-slug>/
    progress.md           # per-task state, rulings, failure causes
    guide.md              # commands, app start, shared rules; implementers read it first
    reviews/task-N.md     # the reviewer's full findings
    reviews/final.md
```

**What `progress.md` looks like**: one line per step, including who did the work
(`model/effort`). `inherit` means the main session set no value; a subagent one tier
up may then run at its own configured effort, not the session's. The `model:` header
is the session's own model, with its effort only when one was set.

```text
model: opus/high
task 1: start base=3f2a1c0
task 1: low: usage/store.py:41 loop reads each row twice
task 1: done 8c1d2e4 impl=opus/inherit review=fixed 2 reviewer=opus/inherit tests=43 passed
task 2: start base=8c1d2e4
task 2: failure: suite red after commit — cause: stale import — next: fix the import
task 2: retry impl=fable/inherit
task 2: done 5b7a9d2 impl=fable/inherit review=clean reviewer=opus/inherit tests=45 passed
final: start
final: done 9e0f3a1 impl=opus/inherit reviewer=opus/xhigh fixed=1 walk=ok tests=47 passed
```

The review field is one of `clean`, `fixed K`, `overruled K`, `skipped (<why>)`, or
`unknown` (rebuilt after the records were lost). `walk=none (<why>)` says why the app
was not walked.

**When done**: a report of at most 15 lines: tasks and commits, findings fixed or
overruled, the final test result, and anything not verified.

**When something goes wrong**
- A failed task gets one written cause and one retry. A second failure stops the run
  with the reason. A red test run after the final fixes is handled the same way.
- A subagent's brief rate-limit error (429) gets one redispatch. When the session
  itself hits its usage limit, it writes `paused: limit` and stops. Call it again to
  continue.
- If a run is cut off, call it again. Tasks committed in this run are not redone; a
  task cut off before its review picks up at the review, and a cut-off final phase
  picks up at its review or its fixes. Uncommitted work is never thrown away. If
  `.waygent/` is deleted, call `/waygent` alone: progress is rebuilt from this run's
  `Waygent-Task` commits. If the branch history was rewritten under the run (say, a
  squash), it stops and says so.

**Reviews**
- A reviewer's High or Medium is fixed once. The main session may reject one only
  after running the reviewer's reproduction and seeing the code work.
- Low findings are only written down; the final review sees them, but they are not
  fixed automatically.
- Findings the repository cannot settle, such as deploy order or a billing policy,
  come back as notes in the report for you to decide.

**Models**
- Implementers and per-task reviewers use this session's model, never a cheaper one.
- Only the final review and the retry after a failure go one tier up: Claude Code
  goes sonnet → opus → fable; Codex keeps the model and sets `reasoning_effort` to
  `xhigh`. Cursor and Grok Build cannot pick, so they use the same model.
- In Claude Code, with the optional agent link above, the final review runs on opus at
  xhigh instead of fable. In 2026-10 measurements it cost about a third less for that
  review with the same results.
- One subagent runs at a time, reviewers included. In Claude Code a subagent may run
  in the background; the main session waits for it, so keep the session open until
  the run ends. If it closes, call the command again.

**App check**: implementers stick to tests and start the app only when their task
changes how it starts. `guide.md` says how to start the app, or why there is none. At
the end the final fixer starts it once, walks the changed flows on real data, fixes
what it finds, and stops it.

**Not done**: brainstorming or spec phases, re-review loops, parallel subagents,
a human checkpoint per task, edits to `CLAUDE.md` or `AGENTS.md`.

**Limits**: fixed code is seen again only by the final review. Results depend on the
model and the plan.

## See also

- [Design and evaluation](https://github.com/beyondwin/skills/blob/main/docs/research/2026-09-waygent-eval/README.md): why it works this way, with numbers
- [CHANGELOG](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/contract.md) · [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/testing.md) · [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md) · [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/release.md)
- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
