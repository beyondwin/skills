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
are implementer workers, not hosts. Earlier Codex/Grok linked-worktree
checks verified direct commits, session resume, and configuration restoration.
Later checks reproduced prohibited full-plan reads and omitted deviations in
worker reports. Version-specific observations are recorded in the testing guide below.
Cursor worker and Claude Code host execution remain `not_measured`. This is
scope-limited evidence for the measured fixture and versions. Claude.ai,
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

The skill asks for a backend once unless argv is present, then runs
Superpowers SDD with an external implementer and native reviewers.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
