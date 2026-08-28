# graspic

[한국어](README.md)

## The problem this skill solves

It explains how one machine works. You pick one depth:

- picture: the whole shape at a glance
- path: the flow, one step at a time
- skeleton: the internal structure and branches
- fracture: where it breaks

It does not swap the content for a cute analogy, and it does not talk down in a child voice.

## When to use it and when not to

Use it to explain how one machine works at a depth you pick.

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

Do not explain until the topic, the depth (picture, path, skeleton, or fracture), and the language are set. The result is a page you open in a browser, not a chat log. Diagrams are drawn in mermaid. Do not leave the explanation only in the terminal.

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
- [Contract](../../docs/maintainers/products/graspic/contract.md)
- [Testing](../../docs/maintainers/products/graspic/testing.md)
- [Compatibility](../../docs/maintainers/products/graspic/compatibility.md)
- [Release](../../docs/maintainers/products/graspic/release.md)
