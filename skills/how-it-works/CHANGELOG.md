# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 3.0.3 - 2026-10-02

### Fixed

- An analogy the user asks for (animals included) is no longer refused. `SKILL.md`
  now matches `references/output.md`: one analogy, mapped per the Metaphor
  isomorphism rule, with the Map still Mermaid plus the hop list.

### Changed

- `SKILL.md` is shorter. The Dump gate table is removed (each row restated a rule
  stated elsewhere), rung precedence is stated once in Slots, and the tagline and
  the closing red-flag line are gone. Behavior is unchanged.
- A new Gotchas section records two observed failures: replies written without
  the references dropped parts of the skeleton, and a skeleton with Korean and
  English labels side by side was echoed in both languages.

## 3.0.2 - 2026-10-01

### Fixed

- Replies keep the title, headings, `**H1**` hop list, and `다음:` / `Next:` line even when the model skips the references: `SKILL.md` now carries the reply skeleton, mirrored from `references/output.md`, with the hop list before Mermaid. A host that can read files first reads the references the EXPLAIN section lists, starting with `output.md` (so `visuals.md` is no longer skipped); only a host that cannot read files replies from the skeleton alone.
- A new red flag catches a Mermaid hop id with no matching `**Hk**` list item.
- The picture box rule is the same in `output.md` and `visuals.md`: 4–6 boxes, one per hop; more than 6 means recut the slice.
- Hop ids stay the same across rungs: each hop's Mermaid label starts with its id (`H1: …`), a skeleton branch reuses its parent id (`H3a`), and the picture hop list is the baseline.
- Medical, legal, and financial topics get the stakes banner and are still explained in the same turn, never paused for confirmation.
- Comparison tables use the same four columns at every rung.
- The other-angle next move offers only the four real types.

### Changed

- English replies get English labels for the rung in the title and for the next move.
- Classify says how to handle re-explaining an earlier answer, a bundled non-mechanism ask, and more than one mechanism, using the existing Direct, Ask one, and Cut paths.
- Korean replies stay in 해요체 even after 합니다체 turns, never use 너 or 네가, and open the Body (not the reply) with a lived snag. The Korean intent line picks 을/를 and 이/가 and lives only in `SKILL.md`.
- Both READMEs say that a technical-jargon topic with no depth starts at skeleton, and list the hop list before Mermaid.
- The description drops the "invokes the skill explicitly" clause; explicit calls work as before. Stale lines (age motto, rung picker name, duplicated rules) are removed.

## 3.0.1 - 2026-09-28

### Changed

- README wording is shorter and uses plain terms. Behavior is unchanged.
- Docs are English-first: `README.md` is English and `README.ko.md` is the
  Korean user guide. `README.en.md` is removed.
- Instruction text in `SKILL.md` and `references/` is English; Korean stays
  only where it is the output or an example. The workflow path labels are now
  Direct, Ask one, and Cut. Behavior is unchanged.
- The READMEs drop the note about the 2026-08-28 live run. That old record is
  removed from the repository; live runs of the current files stay
  `not_measured`, and Grok and Cursor stay unsupported.

## 3.0.0 - 2026-09-12

### Breaking

- Default rung is 그림. A missing depth is filled by precedence, announced
  in the intent line, and explained in the same turn. The old last step
  `one necessary question` is removed.
- Picture Map prints numbered hops before Mermaid source. Body at 그림
  does not walk the hops again.

### Changed

- `감이 안 와` is a silent 그림 alias. Type word `흐름` still does not fill
  rung. Jargon without a depth alias remains 뼈대.
- First-call README examples use `$how-it-works DNS` / `/how-it-works DNS`.
  Explicit `DNS 길` remains a path example.

### Notes

- Live model quality stays `not_measured`. Fixture pass is not host
  execution evidence. No GitHub tag or GitHub Release is created.

## 2.0.1 - 2026-09-11

### Changed

- Standalone README now uses the shared heading set and points install procedures at the split user guides.

### Notes

- No GitHub tag or GitHub Release is created.

## 2.0.0 - 2026-09-08

### Breaking

- Depth selection now follows explicit rung, explicit depth alias, existing
  jargon default, then one necessary question. Explicit easy aliases override
  jargon. This precedence is a MAJOR behavior change.
- Numeric aliases select a rung only in explicit depth context; numbers such as
  `Raft term 20`, `HTTP/2`, and `5 nodes` remain topic data.
- Required output is complete in chat: one-sentence claim, Mermaid source,
  numbered hop list, rung-specific body, adjacent slices, and one next move.
- Fracture keeps the baseline Mermaid and numbered hops in Map and puts its
  failure/regime table in Body. A host preview is optional and non-fatal.

### Changed

- One-turn hosts emit the complete required deliverable in the current reply
  even if focused references cannot be read this turn.
- Korean and English output stay in the selected language. High-stakes and
  source policy now distinguish verified claims from explicitly unverified
  claims without inventing citations or identifiers.
- Local installation is repeatable for an existing correct link and refuses
  files, directories, different links, dangling links, and targets that appear
  during installation. Links to repository docs now use public repository URLs.
- The preserved schema 1 smoke record is historical evidence only. Its earlier
  host verdicts are not live passing evidence for this version.
- This entry records release metadata and behavior changes. No tag, publication,
  or GitHub Release was created.

## 1.0.0 - 2026-08-28

### Notes

- The unpublished working identity `graspic` was replaced by `how-it-works`
  before first public release. No alias exists. Users install and invoke only
  `how-it-works`. This product was not published as `graspic 2.0.0` and was
  not part of the integrated `v2.0.0` GitHub Release. This section does not
  claim a GitHub tag or GitHub Release.
