# Korean Editorial Guide

Use this guide for `diagnose` decision classes and uncertain normative cases.
The editing procedure, protected wording, and output rules live in
[SKILL.md](../SKILL.md).

## Decision Classes

Classify each proposed change. Include the class in `diagnose` findings; in
`correct` and `polish`, explain it only when the user asks why.

- `normative-rule`: an authoritative source supports one correction.
- `permitted-alternative`: more than one form is allowed; keep the source form
  unless the user asks for consistency.
- `editorial-suggestion`: audience, genre, or readability motivates the
  change; it is not a correctness claim.
- `style-judgment`: rhythm, repetition, indirectness, intensity, or voice is a
  model-dependent choice.
- `hold`: context or intent is insufficient for a safe edit.

A permitted alternative is valid, not a `hold`. Reserve `hold` for unresolved
context or an uncertain norm. Do not silently apply `style-judgment`.

## Normative Pass

A normative correction needs an authoritative Korean-language basis for one
standard form. Distinguish that basis from a visible citation: default editing
replies contain only the work product. Give the relevant normative source when
the user asks why or requests sources; do not invent a citation. An uncertain
rule is a `hold`, not an error. Typical local cases:

- dependent-noun spacing: `할수 있다` → `할 수 있다`
- negation spacing: `하지않았다` → `하지 않았다`
- standard spellings such as `몇일` → `며칠`, `금새` → `금세`, `왠일` → `웬일`,
  `되요` → `돼요`, `어떻해` → `어떡해`, `역활` → `역할`

Do not treat a preferred house style as a spelling rule or copy third-party
pattern catalogs or corpora.

## Grammar And Local Flow

In both `correct` and `polish`, repair unambiguous local grammar errors such as
duplicate particles and clearly broken agreement. These are required local
corrections, not optional flow work. If choosing a repair requires guessing the
intended subject, register, or meaning, retain the source wording and use the
hold rule.

Optional local flow work belongs to `polish`. Preserve the wording protected
by the Preservation Gate in `SKILL.md`; ordinary readability swaps remain
allowed. An error outside the requested span stays untouched. Technical
`leverage`, a factual `X가 아니라 Y`, or deliberate repetition can be valid;
judge the contextual problem, not the token.

Readability heuristics are `editorial-suggestion`, not `normative-rule`.
Length alone does not justify broader rewriting. Preserve the writer's person,
register, and genre: a personal message may stay informal, technical prose may
keep its terms, and a review may remain ambivalent. Do not homogenize sentence
length or replace `나는` with `당사`. Public-document guidance applies only when
the user asks for that register.

## Compact Examples

- **Normative spacing.** `지금 상태에선 배포할수 있다.` →
  `지금 상태에선 배포할 수 있다.` Class: `normative-rule`. Valid in `correct`
  and as the first pass of `polish`.
- **Already-correct obligation.** `이 기능은 사용할수 있지만 반드시 켤 필요는
  없습니다.` → `이 기능은 사용할 수 있지만 반드시 켤 필요는 없습니다.`
  Class: spacing is `normative-rule`; `켤 필요는` stays. Do not write
  `켜야 할 필요는`. Valid in `correct`.
- **Required local grammar in both modes.** `나는 3월 4일에 김민수의 글을을
  읽었지만, 다시 읽을지는 모르겠다.` → `나는 3월 4일에 김민수의 글을
  읽었지만, 다시 읽을지는 모르겠다.` Remove the unambiguous duplicate particle
  in both `correct` and `polish`. This repair does not authorize changing the
  ambivalent final clause to `반드시 다시 읽겠다`.
- **Already natural.** `오늘은 조금 늦을 것 같아요.` → unchanged. No-op in
  `polish`; do not “improve” a clear sentence.
- **Modality.** `일정에 지연 가능성이 있다.` keeps `가능성이 있다`. Do not
  write `확실하다`, `반드시`, or other certainty inflation.
- **Ambivalent review.** `좋았지만, 선뜻 권하기는 어려운 책이었다.` stays
  ambivalent. Do not promote it to `꼭 읽어야 할 책`.
- **Intentional fragment and repetition.** Keep `아무튼.` as a fragment, and
  keep both `그래도` in `그래도 나는, 그래도 한 번은 믿어 보고 싶었다.` These
  are voice, not errors.
- **High-stakes claim.** `본 계약은 해지 후 30일 이내 환불을 보장한다.`
  With no stated mode, apply only mechanical correction and add a `확인 필요`
  line after the text. An explicit `polish` may change wording but keeps the
  claim verbatim. Do not verify the clause or add legal advice. The same
  default applies to medical and financial claims.
- **Reporting verb.** `이서연은 “보류하겠습니다”라고 말했다.` keeps `말했다`.
  Do not write `밝혔다` or `전했다`; the reporting verb is attribution.
- **Already-correct possibility.** `현재 계획으로는 출시하지 않을 수 있다.`
  stays `수 있다`. Do not write `수도 있다`. Valid in `correct` and
  `polish`. Class: already-correct local form.
- **Excluded translation.** `이 문장을 영어로 번역해줘: 내일 오전에 회의가
  있습니다.` is a near-miss. Do not translate it in the same turn. Class:
  excluded task.
