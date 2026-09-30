# Safety and privacy

[한국어](../ko/safety-and-privacy.md) · [Installation](installation.md) · [Verification](verification.md)

This project has no telemetry: it sends no usage data anywhere. Required CI and `python3 scripts/verify.py` use no credentials, call no model, and upload nothing. The optional installer `npx skills add beyondwin/skills --skill korean-writing-editor` is third-party and follows its own policy.

Product guides: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.md), [`image-workbench`](../../../skills/image-workbench/README.md), [`how-it-works`](../../../skills/how-it-works/README.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.md), [`sddx`](../../../skills/sddx/README.md), [`waygent`](../../../skills/waygent/README.md).

## Korean source text

`korean-writing-editor` does not save your text as fixtures, logs, or a voice profile, and does not send it to unofficial spelling services. It looks up facts only when you ask. Public fixtures are synthetic and free to share. Do not commit personal conversations or private manuscripts.

## Explanation topics

`how-it-works` does not save your topics as fixtures or logs, on Codex or Claude Code. Citations are URLs you can see from the current turn, not a private corpus. Medical, legal, or financial slices explain how something works; they are not advice.

## Image references and consent

In `image-workbench`, every input image has exactly one role: `edit_target`, `subject_reference`, `style_reference`, or `compositing_input`. A reference image gives no right to copy a person, a mark, or a protected work. If consent for a person, mark, or example image is unknown, the work is held. Do not store private references, prompts, or generated outputs as Git fixtures.

## Pre-SDD document review

`pre-sdd-review` reads local design, implementation plan, referenced ADR, and repository files. In default mode it edits only the resolved design, plan, and shared-file ledger. Repository-owned tests do not transmit, persist, or capture user documents as fixtures. This product adds no telemetry or upload path. Live processing and retention follow the Codex host's data controls. It never starts implementation or SDD without an explicit outer request.

The optional recorder `evidence/evidence.py` is not installed separately and uses only the Python standard library. Each run writes one record under `~/.pre-sdd-review/runs/`; set an absolute `PRE_SDD_REVIEW_HOME` to change that folder. Commands are in the [recorder README](../../../skills/pre-sdd-review/evidence/README.md).

Records hold repository-relative paths, a directory name, hashes, enum values, integers, timestamps, and short paraphrases. Do not store source text, absolute paths, prompts, provider transcripts, command output, credentials, or environment-variable values, even inside a bounded note, consequence, or fix.
The recorder does not promise automatic secret detection.

Recording is optional; a receipt error does not change the semantic verdict. Schema 5 records derive `repo_key` with HMAC-SHA-256 from the normalized Git directory and checkout root using a private local 32-byte `.identity-salt`. Neither the raw absolute identity path nor the salt is printed or recorded. The binding belongs to the checkout, evidence home, and salt: a separate clone/worktree, moved checkout, different evidence home, or lost salt needs a new run. A display name cannot establish identity. Schema 2, 3, and 4 records from recorders before 6.0.0 are not read: every command refuses them with `schema-unsupported`, and they have no checkout binding to infer.

Atomic local storage gives cooperating clients consistency; it is not a signed audit log resistant to malicious local tampering.
An `outcome` label (`good`, `false-ready`, `noisy`, `abandoned`) is an observation recorded by a person or the SDD worker after SDD or implementation ends and may be re-recorded to correct it. Labels are self-improvement evidence, not objective quality judgments or audit-grade proof. Reading the log is an agent's task: `summary` returns JSON whose anomalies and chains carry run_id values.

## External SDD implementation

When `sddx` runs for real, its worker (Cursor Agent or Grok Build) sends the
task and worktree contents to Cursor or xAI, under that CLI's data policy. The
host never puts its own secrets in the worker prompt. Default `verify.py` and
CI never call the Cursor or Grok CLI. Do not commit worker transcripts,
credentials, or provider receipts (the run records a provider returns).

## Per-task subagent implementation

`waygent` starts subagents inside the host (Claude Code, Codex, Cursor
Agent, or Grok Build). Task content and repository files go to that host's model provider
under that host's data policy. Progress and review records stay in `.waygent/`
at the repository root, and its `.gitignore` keeps them out of commits. Default
`verify.py` and CI never call a model.

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
