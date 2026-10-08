# Codex install

[한국어](../ko/install-codex.md) · [Installation](installation.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md) · [Verification](verification.md)

## Install with `$skill-installer`

In Codex, install [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md) and [`image-workbench`](../../../skills/image-workbench/README.md) with `$skill-installer`:

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

Each skill lands in `$CODEX_HOME/skills/<skill-name>` (`~/.codex/skills` when `CODEX_HOME` is unset). If that folder already exists, the installer stops.

Then start a new turn and try the first call in the product README.

How It Works is not installed this way. Use [Local links](install-local.md).

## Optional: third-party installer

For the Korean editor only, you can also use:

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

This is a third-party tool with its own release and telemetry policy.

## Optional: copy from a git clone

To skip both installers, clone the repo and copy one skill folder yourself:

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
SKILL_SOURCE="$PWD/skills/korean-writing-editor"
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_SOURCE"
ls -ld "$SKILL_TARGET"
```

Copy only if `$SKILL_TARGET` does not exist, or is a link you have confirmed points to this skill. If a real folder is already there, stop and do not copy over it. The same rule applies to `image-workbench`.

## Update and uninstall

First inspect the exact target:

```bash
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_TARGET"
```

Check that:

- the path ends in this skill's name
- it is the kind of entry you expect (a real folder or a link, and where a link points)
- `name` and `metadata.version` in its `SKILL.md` are what you expect

Only then remove that one path, and reinstall with `$skill-installer` if you are updating. Do the same for `.../skills/image-workbench`.

Never delete the parent `skills` folder or a home folder. Never pipe a remote script into a shell, and never replace an install you have not inspected.
