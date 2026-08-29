# How It Works

[한국어](README.md)

## Purpose

It explains how one machine works. You pick one depth:

- picture: the whole shape at a glance
- path: the flow, one step at a time
- skeleton: the internal structure and branches
- fracture: where it breaks

It does not swap the content for a cute analogy, and it does not talk down in a child voice.

## When to use and not use

Use it to explain how one machine works at a depth you pick.

Do not use `how-it-works` for debugging, implementing, reviewing, translating, one-line factual lookups, child-register explainers, or as a stand-in for `/eli5`.

## Supported hosts

how-it-works: Codex and Claude Code supported for local or repository-based use.

The supported host ids are `codex` and `claude-code`. Grok was measured and failed live smoke, so it is not supported. Cursor was not executed, so it is not claimed. Claude.ai, Cowork, Skills API upload, and marketplace publication are not supported. Shared limits are in [Compatibility](../../docs/users/en/compatibility.md).

## Install

Clone the repo, then make two links. The first link serves Codex; the second serves Claude Code. `ln -s` fails instead of overwriting an existing target.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
ln -s "$PWD/skills/how-it-works" ~/.agents/skills/how-it-works
ln -s "$PWD/skills/how-it-works" ~/.claude/skills/how-it-works
```

`$skill-installer` names the public GitHub path. Codex still discovers `~/.agents/skills/how-it-works`; do not create a `~/.codex` duplicate. The installer stops if the destination already exists. It does not replace an existing install.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/how-it-works
```

Shared install, update, and uninstall steps are in [Installation](../../docs/users/en/installation.md).

## First call

Explicit calls are `$how-it-works` on Codex and `/how-it-works` on Claude Code.

```text
$how-it-works Explain DNS as a path.
/how-it-works Explain DNS as a path.
```

## Expected result

The explanation is complete in this chat reply. A host page, Canvas, browser, URL, file, or mermaid renderer is not required. A missing renderer is not a failed task.

The six required items are:

1. one-sentence claim
2. Mermaid
3. numbered hop list
4. rung-specific body
5. adjacent slices
6. one next move

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

This repository has no telemetry. The skill does not persist user topics as fixtures or logs. Citations are user-visible URLs from the current turn, not a private corpus. Medical, legal, or financial slices explain mechanism only; they are not advice.

Details are in [Safety and privacy](../../docs/users/en/safety-and-privacy.md).

## Verification

Provider-free verification is `python3 scripts/verify.py --skill how-it-works`. Offline fixtures prove the deterministic contract only; they do not prove live host quality.

Shared evidence limits are in [Verification](../../docs/users/en/verification.md).

## Update and remove

Inspect the exact install target before update or removal. Confirm the path matches this skill name, whether it is a symlink, and that `SKILL.md` `name` and `metadata.version` are the expected values. Do not replace an existing install without that inspection.

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

Do not delete the parent `skills` directory or a home directory. Check the current version in `SKILL.md` `metadata.version` and [CHANGELOG](CHANGELOG.md).

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/products/how-it-works/contract.md)
- [Testing](../../docs/maintainers/products/how-it-works/testing.md)
- [Compatibility](../../docs/maintainers/products/how-it-works/compatibility.md)
- [Release](../../docs/maintainers/products/how-it-works/release.md)
