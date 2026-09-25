# Local links

[한국어](../ko/install-local.md) · [Installation](installation.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md) · [Verification](verification.md)

How It Works, SDDx, and Image Workbench on Grok use a shortcut (symbolic link)
from the host's skill folder to a clone of this repo. The skill folder is not
copied.

The steps are the same for all three skills.

1. Clone the repo and create the folders that hold the shortcuts.
2. Run the Python block below to create a shortcut. Run it once per shortcut (target).
3. Start a new turn and use the first-call example in the product README.

## What the Python block does

The Python below is the same for how-it-works, sddx, and image-workbench. It
creates a shortcut and will not overwrite.

This one-shot Python block takes source (the skill folder) and target (where the
shortcut goes) as arguments. It first validates that source is a skill directory
and treats the same link as success. It does not replace a different link,
dangling link, file, or directory. It also stops if the target appears after
inspection, so inspect it before retrying.

How to run it: in a terminal, type the first line given in each section
(`python3 - ... <<'PY'`). On the following lines, paste the Python block
unchanged. End with `PY` on its own line. This passes the block on standard
input through a quoted here-document. Keep the source and target arguments
quoted.

## how-it-works

Use this on Codex and Claude Code. The public GitHub path is https://github.com/beyondwin/skills/tree/main/skills/how-it-works. You make two shortcuts. The first link serves Codex. The second serves Claude Code. Codex looks in `~/.agents/skills/how-it-works`. Do not create a `~/.codex` or `~/.grok` duplicate.

1. Clone the repo and create the folders.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

2. Run the block below once per target.

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

The Codex invocation starts with
`python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`;
the Claude Code invocation starts with
`python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`.

3. First-call examples are in the [`how-it-works` README](../../../skills/how-it-works/README.en.md). Do not create host-specific copies.

## sddx

Use this on Codex and Claude Code. The public GitHub path is https://github.com/beyondwin/skills/tree/main/skills/sddx. You make two shortcuts. The first link serves Codex. The second serves Claude Code. Codex looks in `~/.agents/skills/sddx`. Do not create a `~/.codex` or `~/.grok` duplicate.

1. Clone the repo and create the folders.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

2. Run the block below once per target.

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

The Codex invocation starts with
`python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<'PY'`;
the Claude Code invocation starts with
`python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<'PY'`.

3. First-call examples are in the [`sddx` README](../../../skills/sddx/README.en.md). Do not create host-specific copies.

## image-workbench

Use this only on Grok. For Codex, follow [Codex install](install-codex.md). The public GitHub path is https://github.com/beyondwin/skills/tree/main/skills/image-workbench. You make one shortcut. Grok looks in `~/.agents/skills/image-workbench`. Do not copy the skill into `~/.grok` or `~/.codex`.

1. Clone the repo and create the folder.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

2. Run the block below once. It checks that the source is a skill folder. If the
same shortcut already exists, it leaves it. It will not replace a different
shortcut, file, or folder.

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

The first line is
`python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`.

3. First-call examples are in the [`image-workbench` README](../../../skills/image-workbench/README.en.md). Do not make extra copies per host.

## Update and uninstall

To remove one, inspect it with `ls -ld` first. Then remove only that exact link.

`how-it-works` links:

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

`sddx` links:

```bash
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx
```

`image-workbench` link:

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

Do not delete the parent `skills` directory or a home directory. Install, update, and uninstall touch only an inspected exact target. Do not pipe remote scripts into a shell. Do not copy without inspecting the destination. Do not replace an existing install by default.
