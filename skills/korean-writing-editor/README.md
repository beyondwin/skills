# Korean Writing Editor

[한국어](README.ko.md)

## Purpose

It edits Korean text you already have: spelling, spacing, and awkward
sentences. Meaning, voice, names, dates, and numbers stay the same.

## When to use and not use

Use it when you have Korean text and want it corrected or polished.

Do not use `korean-writing-editor` for translation, drafting, summaries,
general writing or Korean-learning advice, code review, casual chat,
AI-authorship detection, detector evasion, or imitating a named author.

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

The default is a light polish.

```text
$korean-writing-editor Polish this naturally: (Korean text)
```

For spelling and spacing only:

```text
$korean-writing-editor Fix typos only: (Korean text)
```

`$korean-writing-editor` and `/korean-writing-editor` both work in Codex.

## Expected result

- `polish` (default): a light edit for readability; meaning and voice stay.
- `diagnose`: lists problems without rewriting.
- `correct`: fixes only spelling, spacing, and clearly broken grammar.

The reply is the edited text itself. `diagnose` returns only the findings.

If you select a paragraph or sentence, the rest stays unchanged, including
errors outside that selection. English technical terms, meaningful contrasts,
and intentional repetition are not errors merely because they match a style pattern.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/release.md)
