# Image Workbench

[한국어](README.ko.md)

## Purpose

Image Workbench plans, makes, edits, compares, and checks bitmap images (PNG,
JPG, and similar) for your project. It drops any result that does not fit the
project or breaks a constraint you gave.

## When to use and not use

Use it when you need an image that will live in the project.

Do not use `image-workbench` for:

- a casual one-off picture
- SVG or UI drawn in code
- a data chart
- building the actual screen
- copying an external prompt gallery

## Supported hosts

image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.

It runs on `codex` and `grok`. To make or edit an image, the host (the agent
app you use) needs its own image tool and a way to open the result. Limits are
in [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

In Codex, give the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

Full steps: [Codex install](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-codex.md).

In Grok, clone this repo and add one shortcut (symlink) in the folder where
Grok looks for skills.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

The Python below makes that shortcut. It checks that the source is a skill
folder. If the same shortcut already exists, it leaves it alone. It never
replaces a different shortcut, file, or folder.

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

Run it once in a terminal:

1. First line: `python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`
2. Then paste the Python above as is.
3. Last line: `PY`

Keep the quotes around the paths.

To remove it, check that it is a shortcut first.

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

Codex reads `~/.agents/skills` too, so this one link serves both Codex and
Grok. If you use both hosts, install only one copy: this link, or
`$skill-installer` for Codex alone. Two copies show up as two Codex entries.

Do not copy the skill into `~/.grok` or `~/.codex`. The same steps are in
[Local links](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

Call it in your next conversation after install: `$image-workbench` in Codex,
`/image-workbench` in Grok.

```text
$image-workbench Make a landing-page hero image for this project.
/image-workbench Make a landing-page hero image for this project.
```

## Getting a usable first image

Describe where the image will appear, the subject, the required empty space and
what must remain fully visible. Then specify materials and light. For a hero,
say which side carries HTML text and which side holds the subject. For several
objects, say whether they only need to be countable or their complete outlines
must be visible. A longer list of style adjectives does not resolve that difference.

The skill preserves a detailed first prompt and checks the result against your
original request. A spatial failure can be corrected through view or placement.
It checks the tool's supported canvas
values before generation. If your ratio needs a deterministic crop or pad, it
reports that conversion and rechecks the final image; a conversion that breaks
your constraints is not accepted.

For refinement, name the visible failure and what must stay unchanged. Set an
image-call budget when you want several attempts; rejected calls count toward
an explicit tool-call budget. A file check or a polished-looking image alone
does not prove all requirements were met.

The skill organizes project delivery; it does not guarantee a better-looking
image than the host's ordinary generation. In local comparisons, more instructions
did not establish a consistent aesthetic advantage. The agent's own
visual review also missed occlusion and miscounted visible parts. For a final asset
whose count or completeness is essential, verify those parts yourself or have an
independent reviewer inspect the actual image. Another confident answer from the
same model is not independent confirmation.

For a correction, the skill now keeps your complete original drawing brief and
appends the specific change. It checks subject, count, visibility, framing,
materials, light, exclusions and canvas before the call, then checks every
original critical condition again. Keep a bounded call budget and preserve failed
candidates. Additional attempts can introduce new defects; choose only among
candidates that meet the original requirements.

A paired Grok correction test preserved the original exclusions and produced a
usable result where the previous workflow dropped the exclusions and added visible
text. This is one measured repair, not a guarantee of better aesthetics. Three
attempts to improve count and occlusion review through detail views and sequencing
failed; those revisions are not installed. Use an independent visual review for
acceptance-critical counts and complete outlines.

The retained correction patch also failed the final selection audit's no-regression
criterion: it wrongly rejected three of twelve new candidates, versus two for the
previous version. Both rejected the two failing candidates correctly. This patch
is retained for condition preservation; the overall review workflow has not earned
an improvement claim.

## Expected result

It first picks exactly one mode:

- `brief`: writes down what image is needed. Creates nothing.
- `generate`: makes a new image.
- `edit`: changes an existing image.
- `audit`: inspects only. Creates nothing.

`brief` and `audit` are read-only. It creates an image only when the generate
or edit request is clear.

For a file that goes into the project, it runs
`python3 <skill-root>/scripts/inspect_asset.py <absolute-asset-path>`, where
`<skill-root>` is the installed skill folder. The report lists format, width,
height, alpha, byte size, SHA-256, `extension_matches` (the file extension
fits the detected format), and `trailing_bytes` (extra bytes after the image
end). A preview path that exists only in the chat is not the final file. Grok
returns JPEG without transparency, so its results keep the `.jpg` extension.

That check reads only basic PNG, JPEG, or WebP structure. A pass does not mean
the picture looks good, that the whole file was decoded, or that you have the
right to use it. Open every final candidate yourself. `--output` takes an
absolute report path outside the skill folder. It updates only an existing
JSON report or an empty file, refuses an image file name, the input image,
another image, or any other file, and names the output path when it fails.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/release.md)
