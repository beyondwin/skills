# Grok Image

Use this skill when you ask Grok for a still image. A matching request activates it. You can also call `$grok-image` or `/grok-image`.

[한국어](README.ko.md)

## Purpose

Grok Image writes one concrete scene from your request, fills in light, camera, and setting, and asks one question only when the subject, the count, the words, or a real person is missing. It then makes one still and checks the named parts.

## When to use and not use

Use it for a new still or an edit of one.

Do not use it for a project image that must be saved and checked with image-workbench, for video, for an SVG, a chart, or interface code, or for a prompt gallery.

## Supported hosts

grok-image: Grok supported; still generation uses the host's built-in image tool and local image viewing.

The host id is `grok`. Codex, Claude Code, and Cursor are not supported. A live auto-routing check of the current install is `not_measured`. The prompt procedure was checked with Grok stills on 2026-10-25.

Claude.ai, Cowork, Skills API upload, and marketplace publishing are not supported.

## Install

Clone the repo and link the skill folder into `~/.agents/skills`. Do not add a copy under `~/.grok` or `~/.codex`.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

<!-- grok-image-local-links -->
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

Run it once. The first line is:

`python3 - "$PWD/skills/grok-image" "$HOME/.agents/skills/grok-image" <<'PY'`

After that line, paste the Python block, then end with `PY` on its own line.

On Codex you can also install from the public GitHub path with `$skill-installer`. That does not add Grok support.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/grok-image
```

Update and removal steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

To remove the link after you have looked at it:

```bash
ls -ld ~/.agents/skills/grok-image
unlink ~/.agents/skills/grok-image
```

## First call

Ask for the still in ordinary words, or name the skill.

```text
A bright summer photo of a vegetarian Greek salad.
$grok-image A bright summer photo of a vegetarian Greek salad.
/grok-image A bright summer photo of a vegetarian Greek salad.
```

## Expected result

You get one still. The reply names the path and whether the subject, the counts, and the materials in the prompt are in the picture. If one named item is missing, there is one follow-up still, then a stop.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-image/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-image/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-image/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-image/release.md)
