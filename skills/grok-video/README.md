# Grok Video

A request to generate, animate, or extend a video turns this skill on. `$grok-video` does too.

[한국어](README.ko.md)

## Purpose

Grok Video makes one clip. It asks only when the subject, the change, a spoken line, or a person's photo is missing. It fills duration, resolution, ratio, and a locked camera. The clip is pinned to stills so the scene does not drift.

## When to use and not use

Use it when you want a Grok video.

Don't use it for a still image, a sprite sheet, a diagram, or trimming a file by hand. Stills belong to image-workbench.

## Supported hosts

grok-video: Grok supported; a clip needs the host reference_to_video tool and a way to open the result.

The host id is `grok`. Codex, Claude Code, and Cursor are not supported.

Claude.ai, Cowork, Skills API upload, and marketplace publishing are not supported.
Shared limits are in
[Compatibility](https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md).

## Install

Grok reads a local link. Public path: https://github.com/beyondwin/skills/tree/main/skills/grok-video. The steps are in
[Local links](https://github.com/beyondwin/skills/blob/main/docs/users/en/install-local.md).

Codex can install the folder, and the skill still runs only on Grok:

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/grok-video
```

## First call

Ask for the clip in ordinary words.

```text
A yellow mug slides from the left of a wooden table to the right.
```

## Expected result

One video, six seconds at 720p unless you named another length or a draft. The reply names the file and whether the subject still matches the opening scene.

## See also

- [Safety and privacy](https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md)
- [Verification](https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md)
- [Changelog](CHANGELOG.md)
- [Contract](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-video/contract.md)
- [Testing](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-video/testing.md)
- [Compatibility](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-video/compatibility.md)
- [Release](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-video/release.md)
