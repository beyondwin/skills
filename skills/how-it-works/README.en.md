# How It Works

[한국어](README.md)

## Purpose

It explains how one machine works. You pick one depth:

- picture: the whole shape at a glance
- path: the flow, one step at a time
- skeleton: the internal structure and branches
- fracture: where it breaks

It does not swap the content for a cute analogy. It does not talk down in a
child voice.

## When to use and not use

Use it to explain how one machine works at a depth you pick.

Do not use `how-it-works` for debugging, implementing, reviewing,
translating, one-line factual lookups, child-register explainers, or as a
stand-in for `/eli5`.

## Supported hosts

how-it-works: Codex and Claude Code supported for local or repository-based use.

The supported host ids are `codex` and `claude-code`. Live evidence for the
current install files is `not_measured`. In the preserved 2026-08-28 measurement,
Grok failed and Cursor was not run. That historical record is not current-run
evidence. Claude.ai, Cowork, Skills API upload, and marketplace publication are
not supported. Shared limits are in
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

`$skill-installer` names the public GitHub path. Codex still discovers
`~/.agents/skills/how-it-works`. Do not create a `~/.codex` duplicate.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/how-it-works
```

Shared install steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/installation.md).

## First call

Explicit calls are `$how-it-works` on Codex and `/how-it-works` on Claude
Code.

```text
$how-it-works Explain DNS as a path.
/how-it-works Explain DNS as a path.
```

## Expected result

The explanation is complete in this chat reply. A host page, Canvas,
browser, URL, file, or mermaid renderer is not required. A missing renderer
is not a failed task.

The six required items are:

1. one-sentence claim — what moves, in one sentence
2. Mermaid — the diagram
3. numbered hop list — the steps in order
4. rung-specific body — the body for the depth you picked
5. adjacent slices — nearby explanations you are not covering now
6. one next move — exactly one thing to do next

Skeleton:

````markdown
# {slice} · {picture|path|skeleton|fracture}

## One sentence

## Map

```mermaid
{diagram source}
```

1. **H1** — {what moves or changes}

## Body

## Adjacent slices

Next: {exactly one move}
````

## Safety and privacy

The skill does not persist user topics as test examples or logs. Citations are
user-visible URLs from the current turn. They are not a private corpus.
Medical, legal, or financial slices explain mechanism only. They are not
advice.

Details are in
[Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md).

## Verification

Provider-free verification is
`python3 scripts/verify.py --skill how-it-works`. Offline fixtures prove
the documented rules only. They do not prove live host quality.

Optional live scoring is pass/fail from observable output in a fresh session.
Calls may use subscription/API quota. Do not use private or user prompts.
Do not commit full responses. Keep temporary files outside the repository
and delete them after scoring. A host that fails the same-build criteria is
unsupported.

Shared evidence limits are in
[Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md).

## Update and remove

Inspect the exact install target before update or remove.

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

Do not delete the parent `skills` directory or a home directory. Shared
steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/installation.md).

Check the current version in `SKILL.md` `metadata.version` and
[CHANGELOG](CHANGELOG.md).

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/release.md)
