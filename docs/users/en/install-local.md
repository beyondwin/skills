# Local links

[한국어](../ko/install-local.md) · [Installation](installation.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md) · [Verification](verification.md)

How It Works, SDDx, Waygent, and Image Workbench on Grok are not copied. You clone this repo once and add a link (symlink) from each host's skill folder to the skill folder in your clone. A `git pull` in the clone then updates every host at once.

Every section below has the same three steps:

1. Clone the repo and create the host folders.
2. Run the Python block once per link.
3. Start a new turn and try the first call in the product README.

## How to run the Python block

The block is the same in every section. It takes two arguments: the skill folder (source) and where the link goes (target). It checks that the source is a skill folder, treats an identical link as success, and never replaces a different link, a broken link, a file, or a folder. If something appears at the target while it runs, it stops; look at the target, then run it again.

In a terminal, type the first line given in the section (`python3 - ... <<'PY'`), paste the block unchanged on the next lines, and end with `PY` on its own line. Keep the quotes around both arguments.

## how-it-works

For Codex and Claude Code. Public path: https://github.com/beyondwin/skills/tree/main/skills/how-it-works. You make two links: Codex reads `~/.agents/skills/how-it-works`, Claude Code reads `~/.claude/skills/how-it-works`. Do not add a copy under `~/.codex` or `~/.grok`. SDDx runs on waygent, so link `waygent` the same way (see its section).

1. Clone and create the folders.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

2. Run the block once per link.

<!-- how-it-works-local-links -->
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

- Codex: `python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`
- Claude Code: `python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`

3. First calls are in the [`how-it-works` README](../../../skills/how-it-works/README.md).

## sddx

For Codex and Claude Code. Public path: https://github.com/beyondwin/skills/tree/main/skills/sddx. You make two links: Codex reads `~/.agents/skills/sddx`, Claude Code reads `~/.claude/skills/sddx`. Do not add a copy under `~/.codex` or `~/.grok`. SDDx runs on waygent, so link `waygent` the same way (see its section).

1. Clone and create the folders.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

2. Run the block once per link.

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

- Codex: `python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<'PY'`
- Claude Code: `python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<'PY'`

3. First calls are in the [`sddx` README](../../../skills/sddx/README.md).

## waygent

For Claude Code, Codex, Cursor Agent, and Grok Build. Public path: https://github.com/beyondwin/skills/tree/main/skills/waygent. Make one link per host you use: Claude Code reads `~/.claude/skills/waygent`, Codex reads `~/.agents/skills/waygent`, Cursor Agent reads `~/.cursor/skills/waygent`, and Grok Build reads any of the three, so it needs no link of its own. Do not add a copy under `~/.codex`. Codex also needs `multi_agent = true` under `[features]` in `~/.codex/config.toml`.

1. Clone and create the folders.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills
```

2. Run the block once per link.

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

- Claude Code: `python3 - "$PWD/skills/waygent" "$HOME/.claude/skills/waygent" <<'PY'`
- Codex: `python3 - "$PWD/skills/waygent" "$HOME/.agents/skills/waygent" <<'PY'`
- Cursor Agent: `python3 - "$PWD/skills/waygent" "$HOME/.cursor/skills/waygent" <<'PY'`

Claude Code, optional: also link the final reviewer's agent definition, so the final
review runs on opus at xhigh instead of fable. Run this block the same way, with the first line given under it. It never replaces an existing file or link.

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

3. First calls are in the [`waygent` README](../../../skills/waygent/README.md).

## image-workbench

For Grok. Public path: https://github.com/beyondwin/skills/tree/main/skills/image-workbench. You make one link in `~/.agents/skills`. Codex reads that folder too, so if you use both hosts, this one link serves both; do not also install a Codex copy with `$skill-installer`. On Codex alone, use [Codex install](install-codex.md) instead. Do not add a copy under `~/.grok` or `~/.codex`.

1. Clone and create the folder.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

2. Run the block once.

<!-- image-workbench-local-links -->
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

- Grok: `python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`

3. First calls are in the [`image-workbench` README](../../../skills/image-workbench/README.md).

## Update and uninstall

To update, run `git pull` in your clone; the links pick up the change. To remove a skill, inspect each link with `ls -ld`, then remove only that link.

```bash
# how-it-works
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works

# sddx
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx

# waygent
ls -ld ~/.claude/skills/waygent ~/.agents/skills/waygent ~/.cursor/skills/waygent ~/.claude/agents/waygent-final-reviewer.md
unlink ~/.claude/skills/waygent
unlink ~/.claude/agents/waygent-final-reviewer.md
unlink ~/.agents/skills/waygent
unlink ~/.cursor/skills/waygent

# image-workbench
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

Never delete the parent `skills` folder or a home folder. Never pipe a remote script into a shell, and never replace an install you have not inspected.
