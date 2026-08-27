# graspic

[한국어](README.md)

## The problem this skill solves

Explains how one machine works at a chosen rung (picture, path, skeleton, or fracture). The picture holds. Age does not go down.

## When to use it and when not to

Use it to explain how one machine works at a chosen rung.

Do not use `graspic` for debugging, implementing, reviewing, translating, one-line factual lookups, child-register explainers, or as a stand-in for `/eli5`.

## One-minute install and first invocation

The primary Codex path is `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists; it does not replace an existing install.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/graspic
```

After install, invoke explicitly on the next turn:

```text
$graspic Explain DNS as a path.
```

Shared install, update, and uninstall steps are in [Installation](../../docs/users/en/installation.md).

## Main workflow

Do not explain until slice, type, rung, and language are filled. Rungs are picture, path, skeleton, and fracture. The default deliverable is a published page; mermaid is the visual channel. Do not leave the explanation in terminal scrollback.

## Safety and privacy

This repository has no telemetry. The skill does not persist user topics as fixtures or logs. Citations are user-visible URLs from the current turn, not a private corpus. Medical, legal, or financial slices explain mechanism only; they are not advice.

Details are in [Safety and privacy](../../docs/users/en/safety-and-privacy.md).

## Compatibility and verification

graspic: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

Shared support policy is in [Compatibility](../../docs/users/en/compatibility.md). Evidence limits are in [Verification](../../docs/users/en/verification.md).

## Updates and version checks

Inspect the exact install target before update. Confirm the path matches this skill name, whether it is a real directory, and that `SKILL.md` `name` and `metadata.version` are the expected values. Do not replace an existing install without that inspection.

Check the current version in `SKILL.md` `metadata.version` and [CHANGELOG](CHANGELOG.md).

## Changelog and maintainer docs

- [CHANGELOG](CHANGELOG.md)
- [Maintainer document](../../docs/maintainers/graspic.md)
