# Voice

Write `voice.md` in phase 3 from this starting point and the user's samples, if any. Writers
read it before every chapter. The numbers below are starting defaults, not pass/fail rules.

## Starting defaults

- 합니다체, unless the user's samples use another register.
- Explain in plain words first, then name the term. On first use, put the original term in
  parentheses: 멱등성(idempotency). Use the term table spelling afterwards.
- One idea per paragraph. Start a paragraph with its point, not with a connective.
- Concrete over abstract: a file, a request, a number from the ledger, a failure that happened.
- Empathy phrases ("어렵게 느껴질 수 있습니다") at most one or two per chapter.
- The "A가 아니라 B" contrast at most three times per chapter.
- Bold sparingly: a term on first definition, or one sentence per section the reader must not miss.
  Close the bold before a parenthesis or particle: `**멱등성**(idempotency)은`, never
  `**멱등성(idempotency)**은`, which Markdown renderers show with literal asterisks.
- No headline slogans, no rhetorical triplets, no "결론적으로", no summary that repeats the
  previous paragraph.
- Do not address the process: no mention of drafts, agents, ledgers, plans, or this skill.

Places to look when a sentence feels machine-written (not a ban list): stacked hedges,
sentence-final "~것입니다" chains, the same paragraph opening three times, an abstract noun as
subject where a person or system acts.

## Calibration (phase 4)

Show chapter 1 and ask the user what to change. Write the answer under `## 보정` in `voice.md`
as concrete rules with an example from chapter 1, then revise chapter 1 by those rules.
A user rule overrides any default above. If the user had no changes, write `## 보정` with
`변경 없음` and the date.
