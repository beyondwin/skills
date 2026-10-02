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

The Direct, Ask one, and Cut paths also cover three common request shapes:

- Re-explaining the assistant's own earlier answer: the slice is the one mechanism
  that answer rests on.
- A bundled ask that is not a mechanism (pending decisions, a recap) is answered after
  the next move as a short separate list.
- More than one mechanism in one request goes to Ask one or Cut.

A medical, legal, or financial topic adds the stakes banner and is still explained in
the same turn; it never pauses for confirmation.

There are four rungs: picture, path, skeleton, and fracture; picture is the default.
The rung is set in this order:

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
2. numbered hop list — the steps in order
3. Mermaid — the diagram
4. rung-specific body — the body for the chosen rung
5. adjacent slices — nearby topics this reply leaves out
6. one next move — one thing to try next

The parts are numbered in chrome order: the Map lists the numbered hops before the
Mermaid source. At picture, the Body does not walk the hops again.

- `skills/how-it-works/references/output.md` owns the reply chrome and hop ID rules.
  `SKILL.md` "Required deliverable" carries a mirror of the reply skeleton, and a test
  keeps the two equal. When the host can read files, the skill reads the references
  the EXPLAIN section lists (`output.md`, then `visuals.md`, then `korean.md`,
  `stakes.md`, or `sources.md` as they apply) before replying; only a host that
  cannot read files emits from the mirror alone.
- The title names the rung in the reply language: the Korean rung name or
  picture/path/skeleton/fracture. The next-move labels have Korean and English forms
  in `SKILL.md`.
- The visual channel is mermaid. Hand-drawn HTML boxes are not a diagram. Picture
  draws 4–6 boxes, one per hop; `output.md` and `visuals.md` state the same rule.
- An analogy, including one the user asks for (animals, say), is a single analogy
  mapped per the Metaphor isomorphism rule in `output.md`, with a break line. It never
  replaces the Mermaid map or the hop list.
- Every rung keeps the baseline Mermaid and a numbered hop list with ids like `H1`,
  `H2` in the Map. The baseline is the picture hop list: deeper rungs may redraw the
  diagram type but keep the same ids, and added detail attaches to the same hops.
  Each hop's Mermaid label starts with its id (`H1: …`); an `alt`/`opt` branch reuses
  its parent id with a letter suffix (`H3a`), and the numbered list keeps parent ids.
- The fracture failure/regime table goes in the Body. It never replaces the Mermaid.

Headings, intent line, body, banner, and next move use only the selected language.
Paired labels in the shared template (Korean / English) mean "pick the one for this
language", not "print both".

Comparisons use one table with four fixed columns at every rung (what it optimizes,
what it gives up, failure shape, how to undo) and explain the tradeoff under the
user's stated conditions. Medical, legal, and financial comparisons do not have to end
in a personal action recommendation.

Korean replies use the polite informal ending even when earlier turns used the formal
one, and never address the user with first-person plural, collective, or second-person
forms (the list is in `references/korean.md`).

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

The current product version is `3.0.3`. The source of truth is
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
  single rung precedence rule in `SKILL.md` "Slots", fixtures, and public docs.
- Output chrome, type recipes, hop ids, the fracture Body table, comparison policy:
  `skills/how-it-works/references/output.md`, the skeleton mirror in `SKILL.md`
  "Required deliverable", and the matching fixture ids.
- Visual channel: `skills/how-it-works/references/visuals.md`. Every rung keeps the
  baseline mermaid source and numbered hop list. The picture box rule and the per-rung
  hop id rules appear in both `output.md` and `visuals.md`; change them together.
- Korean voice and the Korean picture examples:
  `skills/how-it-works/references/korean.md`. The Korean intent line lives only in
  `SKILL.md` "Classify". Do not call `korean-writing-editor`.
- Stakes banner and high-stakes checks: the exact per-language banner bytes in
  `skills/how-it-works/references/stakes.md`.
- Source or citation policy: `skills/how-it-works/references/sources.md`. Keep
  verified and unverified apart; never invent paper or statute ids.
- Version, install block, links inside and outside the installed files:
  `skills/how-it-works/release.toml`, `SKILL.md`, `CHANGELOG.md`, both product READMEs,
  and `tests/products/how-it-works/test_contract.py`. The integration owner keeps the
  shared install counterexamples and shared version pins.
