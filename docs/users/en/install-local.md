# Local links

[한국어](../ko/install-local.md) · [Installation](installation.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md) · [Verification](verification.md)

The Python below is the same for how-it-works, sddx, and image-workbench. It
creates a shortcut and will not overwrite.

For `how-it-works`, clone the repo and make two shortcuts. The public GitHub path is https://github.com/beyondwin/skills/tree/main/skills/how-it-works. The first link serves Codex. The second serves Claude Code. Codex looks in `~/.agents/skills/how-it-works`. Do not create a `~/.codex` or `~/.grok` duplicate.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

The one-shot Python block below takes source and target as arguments. It first
validates that source is a skill directory and treats the same link as success.
It does not replace a different link, dangling link, file, or directory. It also
stops if the target appears after inspection, so inspect it before retrying.

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

Put this block on standard input through a quoted here-document and run it once
per target. The Codex invocation starts with
`python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`;
the Claude Code invocation starts with
`python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`.
Place the Python block above unchanged on the following lines and close each
invocation with `PY` on its own line. Keep the source and target arguments
quoted.

Do not create host-specific copies. First-call examples are in the [`how-it-works` README](../../../skills/how-it-works/README.en.md).

## sddx

For `sddx`, clone the repo and make two shortcuts. The public GitHub path is https://github.com/beyondwin/skills/tree/main/skills/sddx. The first link serves Codex. The second serves Claude Code. Codex looks in `~/.agents/skills/sddx`. Do not create a `~/.codex` or `~/.grok` duplicate.

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

Do not create host-specific copies. First-call examples are in the [`sddx` README](../../../skills/sddx/README.en.md).

## image-workbench

For `image-workbench` on Grok, clone the repo and make one shortcut. The public GitHub path is https://github.com/beyondwin/skills/tree/main/skills/image-workbench. Grok looks in `~/.agents/skills/image-workbench`. Do not copy the skill into `~/.grok` or `~/.codex`.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

The Python below creates that shortcut. It checks that the source is a skill
folder. If the same shortcut already exists, it leaves it. It will not replace a
different shortcut, file, or folder.

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

Run it once in a terminal. The first line is
`python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`.
Paste the Python above on the next lines and end with `PY`. Keep the path quotes.

Do not make extra copies per host. First-call examples are in the [`image-workbench` README](../../../skills/image-workbench/README.en.md).

## Update and uninstall

For `how-it-works` links, inspect first. Then remove only those exact links.

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

For `sddx` links, inspect first. Then remove only those exact links.

```bash
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx
```

For `image-workbench` links, inspect first. Then remove only that exact link.

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

Do not delete the parent `skills` directory or a home directory. Install, update, and uninstall touch only an inspected exact target. Do not pipe remote scripts into a shell. Do not copy without inspecting the destination. Do not replace an existing install by default.
