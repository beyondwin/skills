# korean-writing-editor contract

Keep the trigger, modes, output, evidence, fixtures, and version in step within
one change. Changing the instructions while fixtures or public guides go stale
breaks this contract. Public install guides live in the product `README.md`
(English), `README.ko.md` (Korean), and `docs/users/`. The product READMEs ship
in the installed files.

## Trigger and defaults

An explicit call is `$korean-writing-editor` or `/korean-writing-editor` with
Korean source text. Implicit activation is allowed only when there is both a
proofreading or polishing request and Korean text the user supplied. An
explicit call with no source text and no excluded task asks once for the text
in one short Korean line.

A valid request defaults to conservative `polish`.

| Mode | User intent | Boundary |
| --- | --- | --- |
| `diagnose` | "Just tell me the problems; don't fix them." | Name issues, decision class, and holds. Do not rewrite. |
| `correct` | "Fix typos only." | Apply normative corrections and clearly required local grammar only. |
| `polish` | "Polish it naturally." | Apply the same required corrections, then optional readability and local flow edits that keep meaning and voice. |

The real trigger phrases are Korean; `SKILL.md` holds them.

- `correct` and `polish` both fix normative errors and clear local grammar
  errors, such as a duplicated particle or clearly broken agreement.
- Optional readability and local flow edits happen only in `polish`.
- A grammar fix that needs a guess about the subject, register, or meaning is
  not applied; the hold rule applies instead.

There is no model tier routing. The skill uses the active model; it does not
chain rewrites, run a panel, call a classifier model, or launch an external
provider CLI, and it answers `routing unavailable` when asked about routing.

## Output

- In `correct` and `polish`, the default output is the edited text only. The
  first character belongs to that text.
- In `diagnose`, the default output is the findings only, never a rewritten
  draft or the unchanged source. The first line names an issue, class, or
  hold. Clean text gets a one-line "nothing to fix" reply.
- Do not attach a rubric, change list, score, routing receipt, or "using the
  skill" narration. Add the short hold line defined in `SKILL.md` only when a
  real hold is needed; it comes after the edited text.
- A non-editing request (translation, drafting, and so on) gets a refusal only.
  Do not do that other job in the same turn.
- Already-correct negation, modality, obligation, possibility, quantity, and
  attribution wording is kept in both `correct` and `polish`. Attribution
  covers the speaker, the quoted words, and the reporting verb. Ordinary
  readability swaps stay allowed in `polish`.

## Diagnostic evidence limits

This rule comes from approved hardening design K2. If `diagnose` does not
mention a number or other protected expression from the source, that is not
evidence that a fact changed. This replaces the old "not mentioned means hard
failure" expectation, and it does not require rewriting the source.

`diagnostic_fact_drift` is hard only when all of these hold:

- the protected quantity appears once in the source;
- the reply restates the whole normalized source as the same sentence;
- and that restatement changes the number.

Numbers in alternatives, quoted examples, or longer free explanations stay
`diagnostic_semantics_not_measured`. With no other hard violation, the result
is `partially_verified`. That does not mean general meaning preservation or
legal soundness was verified. Literal checks on the edited text, and explicit
checks that catch a forbidden rewrite in `diagnose`, stay in place.

## Safety and privacy

- Do not store user Korean text as fixtures, logs, or voice profiles.
- Do not send text to unofficial web spelling services.
- Do not look up facts unless the user asks separately.
- High-stakes text (legal, medical, financial) with no stated mode gets
  `correct` plus a hold line on the claim. An explicit `polish` changes
  wording only and keeps the claims verbatim.
- Live cases use synthetic examples only. Do not commit private manuscripts or
  full transcripts.

## Files that change together

Do not put a behavior change in one file only.

- Trigger or near-miss change (a similar request that must not activate):
  activation text in `skills/korean-writing-editor/SKILL.md`, positive and
  near-miss fixtures in `tests/products/korean-writing-editor/offline/cases.json`,
  live cases in `tests/products/korean-writing-editor/live/live_cases.json`,
  the product READMEs, and shared public guides.
- Mode or output change (`diagnose`, `correct`, `polish`, edited-text-only
  output, hold marking): `SKILL.md`,
  `skills/korean-writing-editor/references/editorial-guide.md`, offline
  fixtures, `live/live_cases.json`, and public guides.
- Model or routing change: the `## Model` section in `SKILL.md`, the
  `routing unavailable` check in
  `tests/products/korean-writing-editor/offline/run.py`, and public guides. Do
  not hard-code provider model names or call a classifier model.
- Normative claim change: the authoritative source entry in
  `skills/korean-writing-editor/references/sources.md` and fixtures that hold
  its boundary.
- Using an external project: record the pinned revision, license, check date,
  and adopt/reject boundary in `references/sources.md`. Do not copy third-party
  rule lists or corpora.
