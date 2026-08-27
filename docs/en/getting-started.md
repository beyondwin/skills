# Getting started

[한국어](../ko/getting-started.md) · [Compatibility](compatibility.md) · [Privacy and rights](privacy-and-rights.md) · [Evaluation](evaluation.md)

Version `2.0.0` installs `skills/korean-writing-editor`, `skills/image-workbench`, and `skills/graspic`. The license is Apache-2.0.

## Primary install (Codex)

Use `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/graspic
```

The default destination is `$CODEX_HOME/skills/<skill-name>`, or `~/.codex/skills` when `CODEX_HOME` is unset. Invoke on a new turn after install:

```text
$korean-writing-editor Proofread the supplied Korean source and keep meaning and voice.
$image-workbench Prepare a brief only; do not generate an image.
$graspic Explain DNS as a path.
```

## Optional third-party installer

This path applies to the Korean editor only.

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

That `npx` command is a third-party installer with its own release and telemetry policy. `image-workbench` is Codex-only and is not supported on this path.

## Git clone and host-native folder install

The non-`npx` alternative is a verified clone plus a host-native folder copy.

```bash
git clone https://github.com/beyondwin/skills.git
SKILL_SOURCE="$PWD/skills/korean-writing-editor"
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_SOURCE"
ls -ld "$SKILL_TARGET"
```

Copy only when `$SKILL_TARGET` is absent or is a confirmed safe link to this skill. If a real directory already exists, stop; do not copy over it. Use the same exact-folder rule for `image-workbench` and `graspic`.

Other host folders are an Agent Skills portability target for `korean-writing-editor` only. Do not call those hosts supported until a recorded smoke exists.

## Update and uninstall

Inspect the exact target before update or uninstall.

```bash
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_TARGET"
```

Confirm all of the following:

- the path matches this skill name
- whether it is a real directory, a symlink, or a different destination
- `SKILL.md` `name` and `metadata.version` are the expected values

Only after that confirmation, remove that exact path with the host's ordinary uninstall, or clear that exact destination and reinstall with `$skill-installer`. Do not delete the parent `skills` directory or a home directory. Do not replace an existing install without that inspection.

Apply the same inspection sequence to `.../skills/image-workbench` and `.../skills/graspic`.

## Verify

Provider-free repository verification:

```bash
python3 scripts/verify.py
```

That command covers contracts and offline fixtures only. It does not authorize live execution or prove editing or image quality.
