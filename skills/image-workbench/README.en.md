# Image Workbench

[한국어](README.md)

## The problem this skill solves

Plans, generates, edits, compares, or audits a raster asset for a local project. It keeps project fit, input constraints, and a saved result.

## When to use it and when not to

Use it for a project-bound raster deliverable.

Do not use `image-workbench` for casual one-off images, SVG or native UI, actual frontend implementation, or copying an external prompt gallery.

## One-minute install and first invocation

The primary Codex path is `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists; it does not replace an existing install.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

After install, invoke explicitly on the next turn:

```text
$image-workbench Plan or generate a project-bound raster asset for this repository.
```

Shared install, update, and uninstall steps are in [Installation](../../docs/users/en/installation.md).

## Main workflow

Choose one mode before acting: `brief`, `generate`, `edit`, or `audit`. `brief` and `audit` are read-only and never authorize generation. Only a clear generate or edit request authorizes an image call. For a project-bound final file, run `python3 scripts/inspect_asset.py` from this skill root.

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
- [Maintainer document](../../docs/maintainers/image-workbench.md)
