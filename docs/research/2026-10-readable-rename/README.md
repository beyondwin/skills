# Readable — personal skill rename

[한국어](README.ko.md)

The personal Korean technical-writing skill is now **Readable**, invoked as
`$readable`. Version **0.6.0** replaces the former `ko-technical-writing` identity.
It remains a personal Codex pilot, outside the repository's supported product list.

## Use and install

[User guide](readable/README.md) · [Skill](readable/SKILL.md)

For a new installation, copy `readable/` from this directory to
`~/.codex/skills/readable/`. Before replacing an existing installation, back it up
outside the skill discovery directories. Remove the former
`~/.codex/skills/ko-technical-writing/` installation after migration; no alias or
compatibility shim is provided. Start a new conversation and invoke `$readable`.
Automatic selection for Korean technical drafting remains enabled.

## Scope of the change

The user chose Readable over Readably. This is a naming decision, not an English
user study or trademark clearance. The pre-1.0 version increases to 0.6.0 because
the explicit invocation changes. The payload retains six files; it does not add a
runtime, provider call, host, or supported repository product.

Changed fields: folder/name, version, entrypoint heading, UI display name, default
prompt and the English/Korean user guides. The trigger description, all writing
instructions after the heading, both reference files and the invocation policy
are unchanged from 0.5.1. The UI description is unchanged too.

Frozen experiment snapshots, protocols and results keep their historical names
and hashes. They are evidence, not active aliases. Research introductions and the
learning record now point readers to this installation.

## Verification and limits

[Verification record](verification.json) records the payload manifest, source
comparison, local installation and offline checks. No provider was called for this
rename. Native discovery and writing quality under the new name have not been
measured. The [0.5.1 live study](../2026-10-writing-plain-language/README.md) remains
evidence only for that pinned version; it established neither general superiority
nor human reading improvement.

[Decision history](../../learning/cases/2026-10-09-personal-technical-writing.md)
