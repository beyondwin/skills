# Image Workbench

[한국어](README.md)

## The problem this skill solves

It plans, makes, edits, compares, or checks bitmap images (PNG, JPG, and similar) that will actually go into this project. It does not keep a result that does not fit the project or that breaks a given constraint.

## When to use it and when not to

Use it when you need an image that belongs in the project.

Do not use `image-workbench` for a casual one-off picture, SVG or code-drawn UI, actual screen implementation, or copying an external prompt gallery.

## One-minute install and first invocation

The primary Codex path is `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists; it does not replace an existing install.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

After install, invoke explicitly on the next turn:

```text
$image-workbench Make a landing-page hero image for this project.
```

Shared install, update, and uninstall steps are in [Installation](../../docs/users/en/installation.md).

## Main workflow

Choose one mode first. `brief` only writes down what image is needed and does not create one. `generate` makes a new image. `edit` changes an existing image. `audit` only inspects and does not create. `brief` and `audit` are read-only. An image is created only when the generate or edit request is clear. For a final project file, run `python3 scripts/inspect_asset.py` from this skill folder to check the file format and size.

## Safety and privacy

This repository has no telemetry. Every input image has exactly one role: `edit_target`, `subject_reference`, `style_reference`, or `compositing_input`. A reference does not confer rights to reproduce a person, mark, or protected work. Unknown consent for a person, mark, or example image is a hold.

Details are in [Safety and privacy](../../docs/users/en/safety-and-privacy.md).

## Compatibility and verification

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

Shared support policy is in [Compatibility](../../docs/users/en/compatibility.md). Evidence limits are in [Verification](../../docs/users/en/verification.md).

## Updates and version checks

Inspect the exact install target before update. Confirm the path matches this skill name, whether it is a real directory, and that `SKILL.md` `name` and `metadata.version` are the expected values. Do not replace an existing install without that inspection.

Check the current version in `SKILL.md` `metadata.version` and [CHANGELOG](CHANGELOG.md).

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Contract](../../docs/maintainers/image-workbench/contract.md)
- [Testing](../../docs/maintainers/image-workbench/testing.md)
- [Release](../../docs/maintainers/image-workbench/release.md)
