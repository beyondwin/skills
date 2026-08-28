# Safety and privacy

[한국어](../ko/safety-and-privacy.md) · [Installation](installation.md) · [Verification](verification.md)

This project itself has no telemetry. Required CI and `python3 scripts/verify.py` do not use credentials, model calls, or remote uploads. The optional third-party installer `npx skills add beyondwin/skills --skill korean-writing-editor` is third-party and follows its own policy.

Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), [`how-it-works`](../../../skills/how-it-works/README.en.md).

## Korean source text

`korean-writing-editor` does not persist user text as fixtures, logs, or a voice profile. It does not send text to unofficial spelling services or browse for facts unless the user separately asks. Public fixtures are synthetic examples that may be redistributed. Do not commit personal conversations or private manuscripts.

## Explanation topics

`how-it-works` does not persist user topics as fixtures or logs, including when it is installed locally for Codex or Claude Code. Citations are user-visible URLs from the current turn, not a private corpus. Medical, legal, or financial slices explain mechanism only; they are not advice.

## Image references and consent

In `image-workbench`, every input image has exactly one role: `edit_target`, `subject_reference`, `style_reference`, or `compositing_input`. A reference does not confer rights to reproduce a person, mark, or protected work. Unknown consent for a person, mark, or example image is a hold. Do not store private references, prompts, or generated outputs as Git fixtures.

## High-stakes requests

For high-stakes legal, medical, or financial Korean text, default to mechanical `correct` or `diagnose`. `how-it-works` slices in those domains explain mechanism only. Image Workbench holds when material rights or privacy are unknown.

## hash, provenance, consent, and rights

These evidence types are distinct. None of them alone proves ownership, consent, truth, or commercial permission.

| Evidence | What it shows | What it does not prove |
| --- | --- | --- |
| Repository code and Apache-2.0 | License for this skill code | Ownership of outputs or rights in a reference image |
| Output hash (SHA-256) | Byte identity | Origin, consent, or commercial permission |
| Source URL | Where a document was read | Reuse rights |
| C2PA or other provenance metadata | A declared origin claim | Truth, consent, or commercial permission |

Authoritative locators and pins live in each skill's `references/sources.md`. An external project's license file can be a condition on that code and still not grant rights in a prompt, gallery, or example image.

Report vulnerabilities privately through [SECURITY.md](../../../SECURITY.md).
