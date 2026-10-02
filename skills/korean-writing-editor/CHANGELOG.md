# Changelog

All notable changes to this product are documented in this file.

## Unreleased

### Changed

- `SKILL.md` states the no-rewording list (negation, modality, obligation, possibility, quantity, and attribution, with the `말했다`/`밝혔다` example) once, in the Preservation Gate. Editing Pass steps 2 and 6 point to the gate instead of repeating the list. Behavior is unchanged.

## 2.0.6 - 2026-10-01

### Fixed

- `polish` can make ordinary readability swaps again. The no-rewording rule now covers only already-correct negation, modality, obligation, possibility, quantity, and attribution wording. Attribution includes the speaker, the quoted words, and the reporting verb, so `말했다` stays `말했다`, not `밝혔다`.
- An explicit call with no Korean text asks once for the text in one short Korean line instead of replying that the editor does not apply.
- `diagnose` returns findings only, never the unchanged source. Clean text gets one line such as `고칠 부분 없음`.
- Legal, medical, or financial text with no stated mode gets `correct` plus a `확인 필요` line on the claim. An explicit `polish` may change wording but keeps each claim verbatim. The impossible "separate source verification" requirement is gone.
- A `확인 필요` line comes after the edited text, on its own line. The output contract says the high-stakes line is one of the material holds, so it is not dropped as "not material".
- The no-rewording list is the same on every face; the Preservation Gate no longer adds "permission", which modality already covers.

### Changed

- The description and both READMEs list the same excluded tasks as `SKILL.md`, including general writing or Korean-learning advice and named-author imitation.
- `SKILL.md` says when to read each reference: the editorial guide for `diagnose` decision classes or an unclear normative case, and the evidence register only when the user asks for sources.
- The Codex picker prompt says "polish", which matches the default mode.
- `SKILL.md` states the near-miss refusal and the output contract once each.
- Model Tier is now a short Model section. The skill uses the active model, never chains rewrites, runs a panel, or launches another CLI, and still answers `routing unavailable` when asked about routing. The tier table, the single delegated call, and the on-request tier report are gone.

### Removed

- The evidence register no longer ships a `chatgpt.com/share` link.

## 2.0.5 - 2026-09-28

### Changed

- README wording is shorter and uses plain terms. Behavior is unchanged.
- Docs are English-first: `README.md` is English and `README.ko.md` is the
  Korean user guide. `README.en.md` is gone. Maintainer docs are in English.
  Skill behavior is unchanged.
- `SKILL.md` no longer lists the former `kws-` prefixed name as a separate
  exclusion; that old name is not supported. The matching offline trigger case
  is removed (now 33 cases, `trigger=5`).

## 2.0.4 - 2026-09-12

### Changed

- In `correct` and `polish`, the reply is the edited text. In `diagnose`,
  the first line is the finding. Do not start with “using this skill…”.
- If a phrase is already correct, keep it in `polish` too. If the request
  is not editing (for example translation), do not do that other job in
  the same reply.
- The first README example is a light polish. Typo-only `correct` is the
  second example.

### Notes

- Offline fixtures are now 34 cases (`trigger=6`). Fixture pass still does
  not prove live model quality. This release does not add a recorded host
  smoke or a runner 18 live execute.

## 2.0.3 - 2026-09-11

### Changed

- Standalone README now uses the shared heading set and points install procedures at the split user guides.

### Notes

- No GitHub tag or GitHub Release is created.

## 2.0.2 - 2026-09-08

### Changed

- Clearly required local grammar repairs now apply in both `correct` and
  `polish`; optional readability and local-flow edits remain `polish` only.
- Repository-document links in both standalone READMEs now use absolute GitHub
  paths, while links to files shipped in the payload remain relative.
- Runner 18 distinguishes positive meaning and attribution evidence from
  unmeasured free-form output, detects positive numeric drift in diagnostic
  restatements, and retains bounded execution evidence separately from the
  final response body.
- Historical runner 10 through 17 receipts remain readable, but cannot
  authorize or skip runner 18 execution under the new semantics.

### Notes

- This is local release preparation for standalone target `2.0.2`. No new
  GitHub tag or GitHub Release has been published.

## 2.0.0 - 2026-08-27

Public legacy standalone asset `korean-writing-editor-v2.0.0.zip` published
under the integrated repository tag `v2.0.0` at
https://github.com/beyondwin/skills/releases/tag/v2.0.0.
No product-qualified tag `korean-writing-editor-v2.0.0` exists.

### Added

- Conservative Korean proofreading, correction, and polish of user-supplied
  text. korean-writing-editor: Codex supported; Agent Skills contract
  portable; other hosts only supported after a recorded smoke.
- Apache-2.0 `LICENSE.txt` and `SKILL.md` license declaration.

### Notes

- Offline success does not prove general Korean editing quality or semantic
  equivalence.
