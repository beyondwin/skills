# Safety and privacy

[한국어](../ko/safety-and-privacy.md) · [Installation](installation.md) · [Verification](verification.md)

This project itself has no telemetry. Required CI and `python3 scripts/verify.py` do not use credentials, model calls, or remote uploads. The optional third-party installer `npx skills add beyondwin/skills --skill korean-writing-editor` is third-party and follows its own policy.

Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.en.md), [`image-workbench`](../../../skills/image-workbench/README.en.md), [`how-it-works`](../../../skills/how-it-works/README.en.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.en.md).

## Korean source text

`korean-writing-editor` does not persist user text as fixtures, logs, or a voice profile. It does not send text to unofficial spelling services or browse for facts unless the user separately asks. Public fixtures are synthetic examples that may be redistributed. Do not commit personal conversations or private manuscripts.

## Explanation topics

`how-it-works` does not persist user topics as fixtures or logs, including when it is installed locally for Codex or Claude Code. Citations are user-visible URLs from the current turn, not a private corpus. Medical, legal, or financial slices explain mechanism only; they are not advice.

## Image references and consent

In `image-workbench`, every input image has exactly one role: `edit_target`, `subject_reference`, `style_reference`, or `compositing_input`. A reference does not confer rights to reproduce a person, mark, or protected work. Unknown consent for a person, mark, or example image is a hold. Do not store private references, prompts, or generated outputs as Git fixtures.

## Pre-SDD document review

`pre-sdd-review` reads local design, implementation plan, referenced ADR, and repository files. In default mode it edits only the resolved design and plan. Repository-owned tests do not transmit, persist, or capture user documents as fixtures. This product adds no telemetry or upload path. Live processing and retention follow the Codex host's data controls. It never starts implementation or SDD without an explicit outer request.

The optional `pre-sdd-review-evidence` command uses only the Python standard
library and keeps receipts under `~/.pre-sdd-review/` or an explicit absolute
`PRE_SDD_REVIEW_HOME`. Reviews and outcomes are bounded, create-only local
records. Do not store source text, absolute paths, prompts, provider
transcripts, command output, credentials, or environment-variable values.
Even bounded reasons and findings must use paraphrases rather than raw text,
paths, prompts, transcripts, or credentials. The CLI does not promise
automatic secret detection.

Atomic local storage gives cooperating clients consistency; it is not a signed audit log resistant to malicious local tampering.
Structured downstream observations, assessment basis, and confidence are
observer-supplied. The CLI derives `good`, `false-ready`, `noisy`, and
`prevented-rework` deterministically from those observations. Inputs and derived
labels are self-improvement evidence, not objective quality judgments or
audit-grade proof. Before `record-outcome`, represent every known dispute and
uncertainty honestly in the single structured outcome input. Put finding
disputes in `disputed_findings` and other uncertainty in the applicable
structured observation fields. Confidence and assessment basis do not alter
the deterministic label. `inconclusive` occurs only when the structured
downstream observations reach the approved derivation fallback. A completed
outcome without escaped, disputed, or prevented-rework observations derives
`good` even when confidence is low. After the create-only outcome is recorded,
schema 1 cannot correct or amend it. An erroneous recorded outcome is an
uncorrectable residual risk, not a correction path. Treat candidate thresholds
as human-inspection heuristics, never automatic skill mutation or client/model
ranking.

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
