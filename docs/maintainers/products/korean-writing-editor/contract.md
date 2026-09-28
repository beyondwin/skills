# korean-writing-editor contract

Keep the trigger, modes, output, evidence, fixtures, and version in step within
one change. Changing the instructions while fixtures or public guides go stale
breaks this contract. Public install guides live in the product `README.md`
(English), `README.ko.md` (Korean), and `docs/users/`. The product READMEs ship
in the installed files.

## Trigger and defaults

An explicit call is `$korean-writing-editor` or `/korean-writing-editor` with
Korean source text. Implicit activation is allowed only when there is both a
proofreading or polishing request and Korean text the user supplied.

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

Model tiers are `fast`, `balanced`, and `frontier`. Do not hard-code provider
model names. Do not call a classifier model.

## Output

- In `correct` and `polish`, the default output is the edited text only. The
  first character belongs to that text.
- In `diagnose`, the default output is the findings. The first line names an
  issue, class, or hold.
- Do not attach a rewritten draft, rubric, change list, score, routing
  receipt, or "using the skill" narration. Add the short hold note defined in
  `SKILL.md` only when a real hold is needed.
- A non-editing request (translation, drafting, and so on) gets a refusal only.
  Do not do that other job in the same turn.
- Replacing an already-correct expression with a synonym is reverted in both
  `correct` and `polish`.

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
- High-stakes text (legal, medical, financial) defaults to mechanical
  `correct` or `diagnose`.
- Live cases use synthetic examples only. Do not commit private manuscripts or
  full transcripts.

## Files that change together

Do not put a behavior change in one file only.

- Trigger or near-miss change (a similar request that must not activate):
  activation text in `skills/korean-writing-editor/SKILL.md`, positive and
  near-miss fixtures in `tests/products/korean-writing-editor/offline/cases.json`,
  the product READMEs, and shared public guides.
- Mode or output change (`diagnose`, `correct`, `polish`, edited-text-only
  output, hold marking): `SKILL.md`,
  `skills/korean-writing-editor/references/editorial-guide.md`, fixtures, and
  public guides.
- Model tier change (`fast`, `balanced`, `frontier`, routing, delegation):
  routing fixtures in `tests/products/korean-writing-editor/offline/cases.json`
  and public guides. Do not hard-code provider model names or call a
  classifier model.
- Normative claim change: the authoritative source entry in
  `skills/korean-writing-editor/references/sources.md` and fixtures that hold
  its boundary.
- Using an external project: record the pinned revision, license, check date,
  and adopt/reject boundary in `references/sources.md`. Do not copy third-party
  rule lists or corpora.
