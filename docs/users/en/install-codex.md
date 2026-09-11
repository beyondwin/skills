# Codex install

[한국어](../ko/install-codex.md) · [Installation](installation.md) · [Compatibility](compatibility.md) · [Safety and privacy](safety-and-privacy.md) · [Verification](verification.md)

## Primary install (Codex)

Use `$skill-installer` for [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), and [`pre-sdd-review`](../../../skills/pre-sdd-review/README.en.md). The installer stops if the destination already exists. The default destination for those three skills is `$CODEX_HOME/skills/<skill-name>`. If `CODEX_HOME` is unset, that is `~/.codex/skills`. How It Works is not this destination.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

After install, start a new turn and use the first-call example in the product README.

## Optional third-party installer

This path applies to the Korean editor only.

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

That `npx` command is a third-party installer. It has its own release and telemetry policy. Use the primary install or [Local links](install-local.md) for the other skills.

## Codex-only git clone

If you skip `npx`, clone the repo. Then copy only a verified directory into the Codex skill folder.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
SKILL_SOURCE="$PWD/skills/korean-writing-editor"
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_SOURCE"
ls -ld "$SKILL_TARGET"
```

Copy only when `$SKILL_TARGET` is absent, or is a confirmed safe link to this skill. If a real directory already exists, stop. Do not copy over it. Use the same exact-folder rule for `image-workbench` and `pre-sdd-review`.

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

Only after that confirmation, remove that exact path. Use the host's ordinary uninstall, or clear that exact destination and reinstall with `$skill-installer`. Do not delete the parent `skills` directory or a home directory. Do not replace an existing install without that inspection.

Apply the same inspection sequence to `.../skills/image-workbench` and `.../skills/pre-sdd-review`.

Install, update, and uninstall touch only an inspected exact target. Do not pipe remote scripts into a shell. Do not copy without inspecting the destination. Do not delete parent skill directories. Do not replace an existing install by default.
