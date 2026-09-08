# Korean Writing Editor

[한국어](README.md)

## Purpose

It edits Korean text you already have. It fixes spelling, spacing, and
awkward sentences. Meaning and the writer's voice stay the same. Names,
dates, and numbers stay the same.

## When to use and not use

Use it when you already have Korean text and want that text edited.

Do not use `korean-writing-editor` for translation, drafting, summarization,
code review, casual conversation, authorship detection, or detector evasion.

## Supported hosts

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

Codex is the measured host today. Other hosts are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

In Codex, pass the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
```

Shared install steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/installation.md).

## First call

After install, invoke it on the next turn:

```text
$korean-writing-editor Fix typos only: (Korean source)
```

## Expected result

The default is `polish`: small readability edits that keep meaning and
voice. `diagnose` names problems and does not rewrite. `correct` fixes
spelling, spacing, and clearly required local grammar only. `polish` applies
those required corrections first, then optionally improves readability and
local flow.

## Safety and privacy

The skill does not persist user text as test examples, logs, or a voice profile.
It does not send text to unofficial spelling services. It does not browse
for facts unless the user separately asks.

For high-stakes legal, medical, or financial material, default to mechanical
`correct` or `diagnose`.

Details are in
[Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md).

## Verification

Offline checks cover the documented rules only. They do not prove live editing
quality. Evidence limits are in
[Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md).

## Update and remove

Inspect the install folder before update or remove. Shared steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/installation.md).

Check the current version in `SKILL.md` `metadata.version` and
[CHANGELOG](CHANGELOG.md).

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/release.md)
