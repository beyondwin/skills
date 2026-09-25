# How It Works

[한국어](README.md)

## Purpose

It explains how one mechanism works, in a single chat reply. Every reply has
a Mermaid diagram and numbered steps. There are four depths. If you do not
pick one, it starts at picture.

- picture: the whole shape at a glance
- path: the flow, one step at a time
- skeleton: the internal structure and branches
- fracture: where it breaks

It does not swap the content for an analogy or talk down in a child voice.

## When to use and not use

Use it when you want to understand how something works.

Do not use `how-it-works` for debugging, implementing, reviewing,
translating, one-line factual lookups, or child-register explainers. It is not
a stand-in for `/eli5`.

## Supported hosts

how-it-works: Codex and Claude Code supported for local or repository-based use.

The supported host ids are `codex` and `claude-code`. Live evidence for the
current install files is `not_measured`. In the preserved 2026-08-28 measurement,
Grok failed and Cursor was not run. That old record is not a current result.

Claude.ai, Cowork, Skills API upload, and marketplace publication are not
supported. Shared limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Clone the repo, then make two links to the skill folder: one for Codex, one
for Claude Code.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

The Python block below takes two arguments, source (the skill folder) and
target (where the link goes), and makes the link.

- It first checks that source is a real skill directory.
- If the same link already exists, it counts as success.
- It does not replace a different link, dangling link, file, or directory.
- It also stops if the target appears after the check. Inspect it before retrying.

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

Run it twice, once per target. Feed the block on standard input through a
quoted here-document (`<<'PY'`).

- Codex:
  `python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`
- Claude Code:
  `python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`

After that first line, paste the Python block above unchanged, then close with
`PY` on its own line. Keep the source and target arguments quoted.

On Codex you can also install from the public GitHub path with
`$skill-installer`. Codex finds the skill in `~/.agents/skills/how-it-works`,
so do not create a `~/.codex` duplicate.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/how-it-works
```

Other install steps, such as update and removal, are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

To call it by name, use `$how-it-works` on Codex and `/how-it-works` on
Claude Code. A bare topic gets the default depth, picture.

```text
$how-it-works DNS
/how-it-works DNS
```

The explicit path example is unchanged. To pick a depth yourself, name it in
the request.

```text
$how-it-works Explain DNS as a path.
/how-it-works Explain DNS as a path.
```

## Expected result

The explanation is complete in one chat reply. A host page, Canvas, browser,
URL, file, or mermaid renderer (a tool that draws the diagram) is not required.
A missing renderer is not a failed task.

Every reply has these six items:

1. one-sentence claim — what moves, in one sentence
2. Mermaid — the diagram
3. numbered hop list — the steps in order
4. rung-specific body — the body for the depth you picked
5. adjacent slices — nearby explanations you are not covering now
6. one next move — exactly one thing to do next

At picture, Map prints the numbered steps (hops) before the Mermaid source.
Body does not walk the hops again.

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
