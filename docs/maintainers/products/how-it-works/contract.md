# how-it-works contract

This document sets how-it-works' triggers, slots, output, safety rules, and the files
that change together. When behavior changes, update the instructions, test fixtures,
and public docs in the same change. Leaving any one of them stale breaks the contract.
Public install steps live in the product `README.md` (English), `README.ko.md`
(Korean), and `docs/users/`.

Rung names below use their English labels. In the skill files and in Korean output
they are the Korean words listed in `skills/how-it-works/SKILL.md`.

## Triggers and defaults

Explicit calls are `$how-it-works` on Codex and `/how-it-works` on Claude Code. The
skill also turns on for Korean requests like "start from the principle", "as a
picture", "how does it run", or "I can't picture it" (the exact words are in the
`SKILL.md` description). `/eli5` and "explain like I'm 5" belong to another skill;
this skill does nothing for them.

Before explaining, it fills four slots: `slice` (the piece to explain), `type` (kind
of explanation), `rung` (depth), and `language` (reply language). It infers `type`
and `language`.

There are four rungs: picture, path, skeleton, and fracture. The rung picker
recommends picture first. The rung is set in this order:

`explicit rung > explicit depth alias > existing jargon default > default picture`

- An explicitly named rung, in Korean or as picture/path/skeleton/fracture, wins.
- The "easy" and "at a glance" aliases (and "I can't picture it") select picture even
  when jargon such as `rebase`, `TTL`, or `Raft` is present.
- The jargon default, skeleton, applies only when no rung and no depth alias was
  given.
- Numeric aliases `5` picture, `10` path, `15` skeleton, `20` fracture count only
  when the user is explicitly picking a depth. Numbers in `Raft term 20`, `HTTP/2`,
  or "5 nodes" are topic data.
- A filled slot is never replaced.
- With no rung, the skill announces default picture in the intent line and explains
  in the same turn.

## Output

The required result is complete inside the chat reply. A host page, Canvas, browser,
URL, file, or mermaid renderer is not required. A missing renderer is not a failure.
A preview may be added only after the complete reply, and a failed preview is not
fatal.

The six required parts:

1. one-sentence claim — what moves, in one sentence
2. Mermaid — the diagram
3. numbered hop list — the steps in order
4. rung-specific body — the body for the chosen rung
5. adjacent slices — nearby topics this reply leaves out
6. one next move — one thing to try next

At picture, the Map lists the numbered hops before the Mermaid source. The picture
Body does not walk the hops again.

- `skills/how-it-works/references/output.md` owns the reply chrome and hop ID rules.
- The visual channel is mermaid. Hand-drawn HTML boxes are not a diagram.
- Every rung keeps the baseline Mermaid and a numbered hop list with ids like `H1`,
  `H2` in the Map. Ids stay the same across rungs; added detail attaches to the same
  hops.
- The fracture failure/regime table goes in the Body. It never replaces the Mermaid.

Headings, intent line, body, banner, and next move use only the selected language.
Paired labels in the shared template (Korean / English) mean "pick the one for this
language", not "print both".

Comparisons explain the tradeoff under the user's stated conditions. Medical, legal,
and financial comparisons do not have to end in a personal action recommendation.

## Safety

- User topics are never saved as fixtures or logs.
- Only URLs actually fetched in the current turn may be shown as verified sources.
  There is no private source corpus.
- Stable general principles need no lookup.
- Claims that depend on date, jurisdiction, or real uncertainty are verified or
  marked unverified. When host policy and the user allow it, check primary sources.
  When lookup is unavailable or the user forbids it, mark the claim unverified and
  state the date/jurisdiction limit.
- Never invent paper or statute ids. An unverified note is allowed even when the
  citation heading is left out.

Medical, legal, and financial slices explain the general mechanism only and give no
personal advice. `skills/how-it-works/references/stakes.md` owns the exact Korean and
English banners. The skill does not call `korean-writing-editor`.

## Version and install

The current product version is `3.0.1`. The source of truth is
`skills/how-it-works/release.toml`; `SKILL.md` `metadata.version` copies it.
`metadata.updated_at` is the date of the latest installed-file change. None of this
metadata means a tag, publication, or GitHub Release exists.

Both product READMEs keep the Python block right after
`<!-- how-it-works-local-links -->` byte-for-byte identical. The block:

- takes source and target, and checks that source exists and has `SKILL.md`;
- treats the same symlink as success;
- refuses, without changing anything, a different symlink, a dangling symlink, a
  file, a directory, or a target that appears after the check.

README run examples use a quoted here-document and quoted source/target arguments, and
call the Codex and Claude Code targets separately. Nothing is tested against the real
HOME. The shared install contract test owns the counterexamples on temporary paths
with spaces.

## Files that change together

Don't put a behavior change in one file only.

- Trigger or near-miss (a similar request that must not activate) changes
  (`$how-it-works`, `/how-it-works`, the "principle first" trigger, `/eli5` no-op):
  the activation text in `skills/how-it-works/SKILL.md`,
  `tests/products/how-it-works/cases.json`,
  `tests/products/how-it-works/test_contract.py`, both product READMEs, and shared
  public docs.
- Slot default or alias changes (`slice`, `type`, `rung`, `language`, explicit
  rung/alias precedence, the conditional jargon default, numbers as topic data): the
  `SKILL.md` dump gate (the table that stops an early info dump), fixtures, and public
  docs.
- Output chrome, type recipes, hop ids, the fracture Body table, comparison policy:
  `skills/how-it-works/references/output.md` and the matching fixture ids.
- Visual channel: `skills/how-it-works/references/visuals.md`. Every rung keeps the
  baseline mermaid source and numbered hop list.
- Korean voice and the Korean intent/picture examples:
  `skills/how-it-works/references/korean.md`. Do not call `korean-writing-editor`.
- Stakes banner and high-stakes checks: the exact per-language banner bytes in
  `skills/how-it-works/references/stakes.md`.
- Source or citation policy: `skills/how-it-works/references/sources.md`. Keep
  verified and unverified apart; never invent paper or statute ids.
- Version, install block, links inside and outside the installed files:
  `skills/how-it-works/release.toml`, `SKILL.md`, `CHANGELOG.md`, both product READMEs,
  and `tests/products/how-it-works/test_contract.py`. The integration owner keeps the
  shared install counterexamples and shared version pins.
