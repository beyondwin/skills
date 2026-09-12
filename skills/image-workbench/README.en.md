# Image Workbench

[한국어](README.md)

## Purpose

It plans, makes, edits, compares, or checks bitmap images (PNG, JPG, and
similar) that will actually go into this project. It does not keep a result
that does not fit the project or that breaks a given constraint.

## When to use and not use

Use it when you need an image that belongs in the project.

Do not use `image-workbench` for a casual one-off picture, SVG or code-drawn
UI, actual screen implementation, or copying an external prompt gallery.

## Supported hosts

image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.

It runs on `codex` and `grok` today. To make or edit an image, that host needs
its own image tool and a way to open the result. Limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

In Codex, pass the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

Full Codex steps are in
[Codex install](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-codex.md).

In Grok, clone this repo and make one shortcut where Grok looks for skills.

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

Inspect the shortcut before deleting it.

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

Do not copy the skill into `~/.grok` or `~/.codex`. The same steps are in
[Local links](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

After install, invoke it on the next turn. Codex uses `$image-workbench`. Grok
uses `/image-workbench`.

```text
$image-workbench Make a landing-page hero image for this project.
/image-workbench Make a landing-page hero image for this project.
```

## Expected result

Choose one mode first. `brief` only writes down what image is needed and
does not create one. `generate` makes a new image. `edit` changes an
existing image. `audit` only inspects and does not create. `brief` and
`audit` are read-only. An image is created only when the generate or edit
request is clear.

For a file that will live in the project, run
`python3 scripts/inspect_asset.py` from this skill folder to check format and
size. A preview path that exists only in the chat is not the final file.

That check looks at basic PNG, JPEG, or WebP structure only. A pass does not
mean the picture looks good, the whole file was decoded, or you have the
rights to use it. Open every final candidate. `--output facts.json` can update
a separate JSON report; it refuses to overwrite the input image.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/release.md)
