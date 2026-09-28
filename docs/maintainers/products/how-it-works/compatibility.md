# how-it-works compatibility

This document sets which hosts and OS how-it-works supports and what backs that. The
supported hosts are `codex` and `claude-code` from the product registry, for local or
repository-based use only. Support scope and current measurement are separate. Live
evidence for the current payload is `not_measured`.

- Grok: not supported.
- Cursor: not a support target.
- Claude.ai, Cowork, Skills API upload, marketplace publishing, and cloud sync are not
  supported. Don't make a copy per host.

Terms: `not_measured` means not checked yet, and `current-bounded` means only the
version and hash are bound.

## Supported OS

The supported OS is macOS only. Windows and Linux are unsupported. CI may run full
verification on Ubuntu, but that pass is not Linux support and is not macOS support
evidence.

## Discovery paths

```text
skills/how-it-works/              repository source
├─ ~/.agents/skills/how-it-works ─→ Codex
└─ ~/.claude/skills/how-it-works ─→ Claude Code
```

The one-off Python block in the product README takes source and target as arguments.

- It checks that source exists and has `SKILL.md`, then makes the link.
- Installing the same link again succeeds with `already linked`.
- It never replaces a different link, a dangling link, a file, a directory, or a
  target that appears after the check.

Don't recreate `.codex` or `.grok` duplicate links. The install contract is tested on
temporary paths with spaces, not the real HOME.

## Invocation

| Host | Explicit call | Discovery path |
| --- | --- | --- |
| Codex | `$how-it-works` | `~/.agents/skills/how-it-works` |
| Claude Code | `/how-it-works` | `~/.claude/skills/how-it-works` |

`agents/openai.yaml` is optional Codex display metadata, not a file the skill needs to
run.

## Required host abilities

- Installing a local Agent Skills directory and reading `SKILL.md`
- Returning GitHub-flavored markdown and mermaid source in chat
- A mermaid renderer is not required. The hop list must read fine without one

## Provider-free evidence

The required evidence is `python3 scripts/verify.py --skill how-it-works`.
`tests/products/how-it-works/cases.json` and
`tests/products/how-it-works/test_contract.py` prove shape and the payload contract
only. They don't prove live model quality.

## Live evidence boundary

Live runs are local, explicit, optional, and may cost money. CI never requires them.
Don't describe a payload contract pass as evidence of a live call. Never commit user
topics, provider transcripts, or private logs.

### Records

A schema 2 record separates the observed version, payload hash, model, host,
client, runner, and date, plus per-case invocation and five observed dimensions.

- `lexical` checks of `fence` and `hop_ids` can't promote `skill_loading`,
  `mermaid_syntax`, or `meaning` to a pass.
- With no observation source a dimension is `not_measured/not_run`; an unknown model
  is `null`.
- `current-bounded` only means the metadata matches the current version and hash. It
  does not certify a real run or overall quality.
- `host_event`, `parser`/`renderer`, and `semantic_review` are the operator's declared
  observation methods. The pure binding function does not certify that they ran.
- This work creates no new real record.

For the operating steps, see [testing](testing.md) and
`tests/products/how-it-works/live/README.md`.

## Adding a host

To add support to the registry and public docs, these four smoke checks must pass on
the same build:

1. skill discovery
2. explicit call
3. intended implicit call, and no call on near-miss requests
4. output contract (markdown, mermaid source, numbered hop list)

Don't add a host without real observed evidence and a separate support decision. Don't
drop existing Codex and Claude Code support just because it is currently unmeasured.
Only when support scope is deliberately changed, update `products.toml`, public docs,
and tests together. For the shared user guide, see
[Compatibility](../../../users/en/compatibility.md).
