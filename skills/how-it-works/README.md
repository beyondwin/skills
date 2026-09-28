# How It Works

[한국어](README.ko.md)

## Purpose

How It Works explains one mechanism in one chat reply. Every reply has a Mermaid
diagram and a numbered list of steps. You pick one of four depths. If you don't pick,
it starts at picture.

- picture: the whole shape at a glance
- path: the flow, one step at a time
- skeleton: the inner parts and branch points
- fracture: where the picture stops being true

It keeps the facts true at every depth. It doesn't swap them for a cute analogy or
talk down in a child's voice.

## When to use and not use

Use it when you want to understand how something works.

Don't use it for debugging, implementing, reviewing, translating, one-line fact
lookups, or child-voice explainers. It is not a stand-in for `/eli5`.

## Supported hosts

how-it-works: Codex and Claude Code supported for local or repository-based use.

The host ids are `codex` and `claude-code`. Live runs of the current install files are
`not_measured`. Grok and Cursor are not supported.

Claude.ai, Cowork, Skills API upload, and marketplace publishing are not supported.
Shared limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Clone the repo and make two links to the skill folder: one for Codex, one for Claude
Code.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

The Python block below takes two arguments, source (the skill folder) and target
(where the link goes), and makes the link.

- It first checks that source is a real skill folder.
- If the same link is already there, that counts as success.
- It does not replace a different link, dangling link, file, or directory.
- It also stops if the target shows up after the check. Look at it, then retry.

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

Run it twice, once per target. Feed the block on standard input with a quoted
here-document (`<<'PY'`).

- Codex:
  `python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`
- Claude Code:
  `python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`

After that first line, paste the Python block as is, then end with `PY` on its own
line. Keep the quotes around source and target.

On Codex you can also install from the public GitHub path with `$skill-installer`.
Codex looks in `~/.agents/skills/how-it-works`, so don't make a `~/.codex` copy.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/how-it-works
```

Update and removal steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

Call it by name with `$how-it-works` on Codex or `/how-it-works` on Claude Code. A bare
topic gets the default depth, picture.

```text
$how-it-works DNS
/how-it-works DNS
```

To pick a depth, name it in the request.

```text
$how-it-works Explain DNS as a path.
/how-it-works Explain DNS as a path.
```

## Expected result

The whole explanation is in one chat reply. You don't need a host page, Canvas,
browser, URL, file, or Mermaid renderer (a tool that draws the diagram). A missing
renderer is not a failed task.

Every reply has these six parts:

1. one-sentence claim — what moves, in one sentence
2. Mermaid — the diagram
3. numbered hop list — the steps in order
4. rung-specific body — the body for the depth you picked
5. adjacent slices — nearby topics this reply leaves out
6. one next move — one thing to try next

At picture, the Map shows the numbered steps (hops) before the Mermaid source, and the
Body doesn't walk the steps again.

Reply outline:

````markdown
# {slice} · {picture|path|skeleton|fracture}

## One sentence

## Map

1. **H1** — {what moves or changes}
2. **H2** — {what moves or changes}

```mermaid
{diagram source}
```

## Body

## Adjacent slices

Next: {exactly one move}
````

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/release.md)
