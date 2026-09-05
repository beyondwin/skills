# Image Workbench

[한국어](README.md)

## Purpose

It plans, makes, edits, compares, or checks bitmap images (PNG, JPG, and
similar) that will actually go into this project. It does not keep a result
that does not fit the project or that breaks a given constraint.

## When to use and not use

Use it when you need an image that belongs in the project.

Do not use `image-workbench` for a casual one-off picture, SVG or code-drawn
UI, actual screen implementation, or copying an external prompt gallery.

## Supported hosts

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

Codex is the measured host today. Other hosts are in
[Compatibility](../../docs/users/en/compatibility.md).

## Install

In Codex, pass the public GitHub path to `$skill-installer`.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

Shared install steps are in
[Installation](../../docs/users/en/installation.md).

## First call

After install, invoke it on the next turn:

```text
$image-workbench Make a landing-page hero image for this project.
```

## Expected result

Choose one mode first. `brief` only writes down what image is needed and
does not create one. `generate` makes a new image. `edit` changes an
existing image. `audit` only inspects and does not create. `brief` and
`audit` are read-only. An image is created only when the generate or edit
request is clear.

For a final project file, run `python3 scripts/inspect_asset.py` from this
skill folder to check the file format and size.

## Safety and privacy

Every input image has exactly one role. The role is `edit_target`,
`subject_reference`, `style_reference`, or `compositing_input`. A reference
does not confer rights to reproduce a person, mark, or protected work.
Unknown consent for a person, mark, or example image is a hold.

Details are in
[Safety and privacy](../../docs/users/en/safety-and-privacy.md).

## Verification

Offline checks cover the contract only. They do not prove live image
quality. Evidence limits are in
[Verification](../../docs/users/en/verification.md).

## Update and remove

Inspect the install folder before update or remove. Shared steps are in
[Installation](../../docs/users/en/installation.md).

Check the current version in `SKILL.md` `metadata.version` and
[CHANGELOG](CHANGELOG.md).

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/products/image-workbench/contract.md)
- [Testing](../../docs/maintainers/products/image-workbench/testing.md)
- [Compatibility](../../docs/maintainers/products/image-workbench/compatibility.md)
- [Release](../../docs/maintainers/products/image-workbench/release.md)
