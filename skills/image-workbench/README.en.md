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

The supported host ids are `codex` and `grok`. Generate/edit requires the
current host's built-in image generation and local image viewing. Shared
limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

In Codex, pass the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

Shared Codex install steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-codex.md).

For Grok, clone the repo and make one link under `~/.agents/skills`.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

The one-shot Python block below takes source and target as arguments. It first
validates that source is a skill directory and treats the same link as success.
It does not replace a different link, dangling link, file, or directory. It also
stops if the target appears after inspection, so inspect it before retrying.

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

Put this block on standard input through a quoted here-document and run it once.
The invocation starts with
`python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`.
Place the Python block above unchanged on the following lines and close with `PY`
on its own line. Keep the source and target arguments quoted.

Inspect the link before removing it.

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

Do not create a `~/.grok` or `~/.codex` duplicate. Shared local-link steps are in
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

For a final project file, run `python3 scripts/inspect_asset.py` from this
skill folder to check the file format and size.

The inspector checks selected required structures, including PNG CRCs,
scanline filters and indexed palettes, the first JPEG SOS header, and
interpreted WebP header/version fields. Passing does not prove complete
bitstream decoding, visual quality, or rights clearance. Open every final
candidate for visual review. `--output facts.json` can update a separate JSON
report, but rejects any output that refers to the input image before writing.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/release.md)
