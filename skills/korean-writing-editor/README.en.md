# Korean Writing Editor

[한국어](README.md)

## Purpose

It edits Korean text you already have. It fixes spelling, spacing, and
awkward sentences. Meaning, the writer's voice, names, dates, and numbers
stay the same.

## When to use and not use

Use it when you already have Korean text and want it corrected or polished.

Do not use `korean-writing-editor` for translation, drafting, summarization,
code review, casual conversation, AI-authorship detection, or detector evasion.

## Supported hosts

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

Codex is the only supported host today. For other hosts, see
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

In Codex, pass the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
```

Shared install steps are in
[Installation](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-codex.md).

## First call

Call it like this. The default is a light polish.

```text
$korean-writing-editor Polish this naturally: (Korean source)
```

For spelling and spacing only:

```text
$korean-writing-editor Fix typos only: (Korean source)
```

Both `$korean-writing-editor` and `/korean-writing-editor` work. Both forms
were checked in Codex.

## Expected result

- `polish` (default): makes the text a bit easier to read and keeps meaning
  and voice.
- `diagnose`: names problems and does not rewrite.
- `correct`: fixes spelling, spacing, and clearly broken grammar only.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/release.md)
