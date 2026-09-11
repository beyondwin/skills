# SDDx

[한국어](README.md)

## Purpose

It runs Superpowers SDD with the current Claude Code or Codex session as
orchestrator, and sends implementation only to Cursor CLI or Grok Build CLI.

## When to use and not use

Use it when an implementation plan exists and you want Superpowers SDD with
an external Grok or Cursor implementer.

Do not use it to write a spec or plan, to run `pre-sdd-review`, or for native
subagent-driven-development without an external implementer.

## Supported hosts

sddx: Claude Code and Codex supported for local or repository-based use.

The supported host ids are `claude-code` and `codex`. Cursor and Grok CLIs
are implementer workers, not hosts. Live evidence for the current install
files is `not_measured`. Claude.ai, Cowork, Skills API upload, and
marketplace publication are not supported. Shared limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Clone the repo, then make two links. The first link serves Codex. The second
serves Claude Code.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

`$skill-installer` names the public GitHub path. Codex still discovers
`~/.agents/skills/sddx`. Do not add this product to the three Codex-only
commands in `install-codex.md`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/sddx
```

Shared install steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

## First call

Explicit calls are `$sddx` on Codex and `/sddx` on Claude Code.

```text
$sddx docs/history/plans/example.md
/sddx docs/history/plans/example.md
```

## Expected result

The skill asks for a backend once unless argv is present, then runs
Superpowers SDD with an external implementer and native reviewers.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
