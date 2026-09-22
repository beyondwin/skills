# SDDx

[한국어](README.md)

## Purpose

It runs Superpowers SDD with the current Claude Code or Codex session as
orchestrator, and sends implementation only to Cursor Agent or Grok Build.
Both workers use only Grok 4.7, and neither uses a `-fast` variant.

## When to use and not use

Use it when an implementation plan exists and the user runs `/sddx` or
`$sddx`.

Do not use it to write a spec or plan, to run `writing-plans`,
`executing-plans` (including Native inline), or `pre-sdd-review`, or to
implement in this session, or when the user asks for a Grok/Cursor
implementer without `/sddx` or `$sddx`.

## Supported hosts

sddx: Claude Code and Codex supported for local or repository-based use.

The supported programs are `claude-code` and `codex`. Cursor and Grok CLIs
are implementer programs only. The contract calls them workers. They are not
hosts.

On macOS, all four Claude Code / Codex by Cursor / Grok combinations have
been run for real. What was checked, and what was not, is the table in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md).
Claude.ai, Cowork, Skills API upload, and marketplace publication are not
supported. Shared limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

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

The implementer is chosen with `sddx <plan-file> [cursor|grok|c|g]`. `c` means
cursor and `g` means grok. If the request has no choice, the skill asks once
for this plan. If only one implementer is available, it still shows that fact
and the missing side's reason, then confirms before continuing. If the
requested side is missing, it stops instead of switching.

The worker receives a complete task and listed references, without reopening
the full plan. Completion is judged from the report, real test exits, commits,
the tool record, and native review — not from a process exit. Every attempt
leaves a directory under the plan's `sdd-workspace` folder (inside the
worktree `.superpowers/sdd/<plan>/` tree). While it runs,
`run_worker.py status` is how you read the session ID, whether the pid is still
alive, and a short list of reads, searches, and shells. Do not paste the
whole log. Commands and judgment rules are in the
[contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md).

Grok linked worktrees need Python 3.11+. Grok removes MCP invocation tools
and will not run without value-taking `--disallowed-tools` and `--deny`.
The supported OS is macOS only. Windows and Linux are unsupported. Product
CLIs refuse Windows.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
