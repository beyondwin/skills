# Korean Writing Editor

[한국어](README.md)

## The problem this skill solves

It takes Korean text you already have and edits it. It fixes spelling, spacing, and awkward sentences, and it leaves meaning, the writer's voice, and values such as names, dates, and numbers unchanged.

## When to use it and when not to

Use it when you already have Korean text and want that text edited.

Do not use `korean-writing-editor` for translation, drafting, summarization, code review, casual conversation, authorship detection, or detector evasion.

## One-minute install and first invocation

The primary Codex path is `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists; it does not replace an existing install.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
```

After install, invoke explicitly on the next turn:

```text
$korean-writing-editor Proofread the supplied Korean source and keep meaning and voice.
```

Shared install, update, and uninstall steps are in [Installation](../../docs/users/en/installation.md).

## Main workflow

For a valid request, the default is `polish`: small readability edits that keep meaning and voice. `diagnose` names problems and does not rewrite. `correct` fixes spelling, spacing, and clear grammar only.

## Safety and privacy

This repository has no telemetry. The skill does not persist user text as fixtures, logs, or a voice profile. It does not send text to unofficial spelling services or browse for facts unless the user separately asks.

For high-stakes legal, medical, or financial material, default to mechanical `correct` or `diagnose`.

Details are in [Safety and privacy](../../docs/users/en/safety-and-privacy.md).

## Compatibility and verification

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

Shared support policy is in [Compatibility](../../docs/users/en/compatibility.md). Evidence limits are in [Verification](../../docs/users/en/verification.md).

## Updates and version checks

Inspect the exact install target before update. Confirm the path matches this skill name, whether it is a real directory, and that `SKILL.md` `name` and `metadata.version` are the expected values. Do not replace an existing install without that inspection.

Check the current version in `SKILL.md` `metadata.version` and [CHANGELOG](CHANGELOG.md).

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/products/korean-writing-editor/contract.md)
- [Testing](../../docs/maintainers/products/korean-writing-editor/testing.md)
- [Compatibility](../../docs/maintainers/products/korean-writing-editor/compatibility.md)
- [Release](../../docs/maintainers/products/korean-writing-editor/release.md)
