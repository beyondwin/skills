# Korean Writing Editor

[한국어](README.md)

## The problem this skill solves

Conservatively proofreads, corrects, or polishes Korean text the user already supplied. It preserves meaning, factual literals, and the writer's voice.

## When to use it and when not to

Use it when the user already supplied Korean source text to proofread, correct, or polish.

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

After a valid trigger, the default is conservative `polish`. `diagnose` names issues and does not rewrite. `correct` applies local normative and grammatical fixes only. `polish` still preserves meaning and voice.

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
- [Maintainer document](../../docs/maintainers/korean-writing-editor.md)
