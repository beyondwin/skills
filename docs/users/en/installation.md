# Installation

[한국어](../ko/installation.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md) · [Verification](verification.md)

The installable payloads are [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), and [`how-it-works`](../../../skills/how-it-works/README.en.md). The license is Apache-2.0.

## Primary install (Codex)

Use `$skill-installer` with the public GitHub skill path. The installer stops if the destination already exists.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/how-it-works
```

The default destination is `$CODEX_HOME/skills/<skill-name>`, or `~/.codex/skills` when `CODEX_HOME` is unset. Invoke on a new turn after install using the product README.

## How It Works four-host links

`how-it-works` supports Codex, Claude Code, Grok, and Cursor for local or repository-based use. The shortest repository-based install is a clone plus two links. The first link serves Codex, Grok, and Cursor; the second serves Claude Code. `ln -s` fails instead of overwriting an existing target.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
ln -s "$PWD/skills/how-it-works" ~/.agents/skills/how-it-works
ln -s "$PWD/skills/how-it-works" ~/.claude/skills/how-it-works
```

Do not create host-specific payload copies. First-call examples are in the [`how-it-works` README](../../../skills/how-it-works/README.en.md).

## Optional third-party installer

This path applies to the Korean editor only.

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

That `npx` command is a third-party installer with its own release and telemetry policy. `image-workbench` is Codex-only and is not supported on this path. `how-it-works` uses the four-host links above.

## Codex-only git clone

`korean-writing-editor` and `image-workbench` are Codex-only. The non-`npx` alternative is a verified clone plus a Codex folder copy.

```bash
git clone https://github.com/beyondwin/skills.git
SKILL_SOURCE="$PWD/skills/korean-writing-editor"
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_SOURCE"
ls -ld "$SKILL_TARGET"
```

Copy only when `$SKILL_TARGET` is absent or is a confirmed safe link to this skill. If a real directory already exists, stop; do not copy over it. Use the same exact-folder rule for `image-workbench`.

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

Apply the same inspection sequence to `.../skills/image-workbench`.

For `how-it-works` links, inspect first, then remove only those exact links.

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

Install, update, and uninstall touch only an inspected exact target. Do not pipe remote scripts into a shell, copy without inspecting the destination, delete parent skill directories, or replace an existing install by default.

## Verify

Provider-free repository verification:

```bash
python3 scripts/verify.py
```

That command covers contracts and offline fixtures only. It does not authorize live execution or prove editing or image quality. Profiles and evidence limits are in [Verification](verification.md).
