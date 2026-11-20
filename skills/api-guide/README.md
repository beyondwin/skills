# API Guide

Use this skill only by explicitly invoking `/api-guide` in Claude Code.
Matching requests alone do not activate it.

[한국어](README.ko.md)

## Purpose

API Guide writes one page that tells developers on another team how to call APIs that
were added or changed. The readers can be web, app, or server developers. Every fact
about the server on the page is read from the server code at a recorded commit, and the
page is published as a Claude artifact you can share.

The page has a fixed shape:

- common rules that hold for every endpoint: auth, response body, types, dates, headers
- one card per endpoint, always in the same order: request, response, errors, what the
  caller does
- flows for multi-step operations such as uploads or jobs, keyed by the status the caller
  sees
- an optional to-do list for the calling side, when you point it at that code

## When to use and not use

Use it when a change adds or changes APIs and another developer has to build against
them.

Don't use it to write or fix OpenAPI files, to generate a reference site from a spec,
to review code, to implement the client, or to explain how one mechanism works
(`/how-it-works`).

## Supported hosts

api-guide: Claude Code supported for local or repository-based use.

The host id is `claude-code`. The skill needs the Artifact tool and read access to the
server source. Live runs of the current install files are `not_measured`. Codex, Grok,
and Cursor are not supported.

Claude.ai, Cowork, Skills API upload, and marketplace publishing are not supported.
Shared limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Clone the repo and link the skill folder into Claude Code's skill folder.

Public path: https://github.com/beyondwin/skills/tree/main/skills/api-guide

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills
```

The Python block below takes two arguments, source (the skill folder) and target
(where the link goes), and makes the link.

- It first checks that source is a real skill folder.
- If the same link is already there, that counts as success.
- It does not replace a different link, dangling link, file, or directory.
- It also stops if the target shows up after the check. Look at it, then retry.

<!-- api-guide-local-links -->
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

Feed the block on standard input with a quoted here-document (`<<'PY'`):

`python3 - "$PWD/skills/api-guide" "$HOME/.claude/skills/api-guide" <<'PY'`

After that first line, paste the Python block as is, then end with `PY` on its own
line. Keep the quotes around source and target.

Update and removal steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

Call it by name in the server repository. With no scope, it covers the current branch
against the default branch.

```text
/api-guide
/api-guide the export endpoints, for app developers, client code in ../mobile-app
```

## Expected result

One private Claude artifact and a short chat report.

The page has, in order: a header with base paths, the date, and the server commit; a
to-do list when you gave the calling side's code; common rules; one card per endpoint;
flows; and an appendix with the files it was checked against. Examples are labeled
captured when a running server returned them and composed otherwise.

The chat report says what was checked and at which commits, what was not checked (for
example deployed configuration values), and gaps it found in contract files such as
OpenAPI. It reports those gaps and does not fix them.

Share the page from its Share menu. Asking again with the page link updates the same
page.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/api-guide/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/api-guide/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/api-guide/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/api-guide/release.md)
