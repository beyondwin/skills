# Safety and privacy

[한국어](../ko/safety-and-privacy.md) · [Installation](installation.md) · [Verification](verification.md)

This project has no telemetry: it sends no usage data anywhere. Required CI and `python3 scripts/verify.py` use no credentials, call no model, and upload nothing. The optional installer `npx skills add beyondwin/skills --skill korean-writing-editor` is third-party and follows its own policy.

Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`how-it-works`](../../../skills/how-it-works/README.md).

## Korean source text

`korean-writing-editor` does not save your text as fixtures, logs, or a voice profile, and does not send it to unofficial spelling services. It looks up facts only when you ask. Public fixtures are synthetic and free to share. Do not commit personal conversations or private manuscripts.

## Explanation topics

`how-it-works` does not save your topics as fixtures or logs, on Codex or Claude Code. Citations are URLs you can see from the current turn, not a private corpus. Medical, legal, or financial slices explain how something works; they are not advice.

## Image references and consent

In `image-workbench`, every input image has exactly one role: `edit_target`, `subject_reference`, `style_reference`, or `compositing_input`. A reference image gives no right to copy a person, a mark, or a protected work. If consent for a person, mark, or example image is unknown, the work is held. Do not store private references, prompts, or generated outputs as Git fixtures.

## High-stakes requests

For high-stakes legal, medical, or financial Korean text, the default is a mechanical `correct` or `diagnose`. `how-it-works` slices in those domains explain mechanism only. `image-workbench` holds when rights or privacy are unknown.

## hash, provenance, consent, and rights

A hash shows whether bytes match. Provenance is a claimed origin. Consent is permission from a person. Rights say whether you may reuse the work. These are different things, and none of them alone proves ownership, consent, truth, or commercial permission.

| Evidence | What it shows | What it does not prove |
| --- | --- | --- |
| Repository code and Apache-2.0 | License for this skill code | Ownership of outputs or rights in a reference image |
| Output hash (SHA-256) | Byte identity | Origin, consent, or commercial permission |
| Source URL | Where a document was read | Reuse rights |
| C2PA or other provenance metadata | A declared origin claim | Truth, consent, or commercial permission |

Source locations and pins are in each skill's `references/sources.md`. An outside project's license covers that code; it grants no rights in a prompt, gallery, or example image.

Report vulnerabilities privately through [SECURITY.md](../../../SECURITY.md).
