# korean-writing-editor testing

Offline fixtures (fixed examples that lock the rules without a model) live in
`tests/products/korean-writing-editor/offline/`. Keep the thirty-five property
cases (`normative=10 preservation=8 noop=6 voice=4 trigger=7`) and the mutation
checks in its `cases.json` and `run.py`. A mutation check confirms that a
deliberately broken candidate fails.

The numeric limits in this document are live-call budgets.

## Payload checks

`--scope full` also reads `README.md` and `README.ko.md` as required payload
(installed files) files. It then checks that every local link in a copied
standalone payload leads to a real file inside that payload. Repository doc
links are absolute GitHub URLs, so their status is not checked over the
network.

The product package regression tests check `release.toml`, `SKILL.md`, the
dated CHANGELOG entry, and rejection of a broken README link together.
They also check that the description is trigger-only: it starts with
"Use when" or "Use only when", and every sentence starts with "Use" or
"Do not use".

## Deterministic fixtures

- Trigger work needs both a positive record and a near-miss (a similar,
  out-of-scope request) record.
- Mode, output, and preservation work need matching `expected_mode` and
  `expected_noop` records.
- A triggered record's `request` contains its `source`, so a reference
  candidate never relies on text the request did not supply.
- `expected_noop: true` means the candidate equals the source;
  `expected_noop: false` means it differs. A near-miss candidate is a short
  handoff line, never the echoed source.
- Voice cases protect a small span of tone or attitude. Do not require the
  whole candidate string to match the source.
- Mixed normative cases may protect an already-correct obligation or modality
  span in the same record as a local spelling fix.
- A candidate with a process preamble must fail the replaced
  `norm-spacing-can-01` properties.
- `norm-grammar-particle-correct-09` and `norm-grammar-particle-polish-10`
  check that the same obvious duplicated-particle error is fixed in both
  modes. A candidate that leaves the source error, and one that turns the
  ambivalent final clause into certainty, must each fail their own mutation
  check.
- `trigger-diagnose-05` is `diagnose` findings. It fails if it has a rewritten
  draft, the unchanged source, or a process preamble.
- `trigger-diagnose-clean-07` is `diagnose` on clean text: one "nothing to
  fix" line. Returning the unchanged source fails.
- `trigger-explicit-no-text-06` is an explicit call with no source text. The
  reply asks once for the text; a no-op handoff fails.
- `meaning-quote-07` keeps the speaker, the quoted words, and the reporting
  verb. Swapping the reporting verb fails its mutation check.
- Each of these mutations must also fail: the English and Korean skill-usage
  preambles on `norm-spacing-can-01`, the possibility-to-maybe substitution on
  `meaning-negation-01`, and refuse-then-translate on
  `trigger-translation-03`.
- `--self-test` runs the evaluator's own unit tests and combines with
  `--scope`; the package tests run that combination.
- A fixture pass proves only the offline oracle (answer checker) contract. It
  does not prove live model quality.

## Live evidence limits

The source of truth for the procedure is
`tests/products/korean-writing-editor/live/README.md`. That document defines
reservations, receipts, report leases, and status names.

When you change the live harness (the tool that evaluates with real model
calls), update `tests/products/korean-writing-editor/live/live_cases.json`,
`live_matrix.py`, `test_live_matrix.py`, and
`tests/products/korean-writing-editor/live/README.md` together. Live cases are
synthetic. Do not put private manuscripts or full transcripts in these files.
A `live_cases.json` change also updates `APPROVED_CASES_SHA256` in
`live_matrix.py`.

Near-miss live cases forbid markers of the excluded task's output, and edit
cases fail on skill or mode narration (`process_narration`).

Before the first preflight of a run ID, `live_matrix.py --bootstrap-install`
swaps the reviewed source into the install target (default
`${CODEX_HOME:-~/.codex}/skills/korean-writing-editor`) and keeps the previous
install in the run directory.

Product evidence must be made fresh with runner 18 (live runner version 18).
Records from older runners are rejected and cannot resume or skip a run.

### Budget

When you change the live budget, update the 119-producer, 3-reviewer,
122-baseline, 38-remediation, 160-total dry-run and the parser assertions
together. A producer call makes the edit, a reviewer call reviews it, and
remediation is a separately approved follow-up run.

The dry-run (prints the plan without calls) must report `producer_calls=119`,
`reviewer_calls=3`, `baseline_calls=122`, `remediation_calls=38`, and
`approved_total_ceiling=160`. Starting several cycles does not add up to one
approved 160-call result.

### Resume and remediation

- A resume change (continuing an interrupted run) with a report needs two real
  temporary Git tests: first publish with no prior report, and a crash after
  the report is published.
- Remediation binds at least one immutable planned producer call ID, in the
  canonical full-plan order, to the run identity.
- Do not send reviewer calls until a separately approved reviewer mechanism is
  designed.
- Before a paid call (dispatch), reserve the state that matches the report
  target. Do not use the final report write as the first ownership claim.

## Codex smoke, 2026-10-01

A direct probe on macOS with Codex CLI 0.157.1, `codex exec --json`, model
`gpt-6-astra` with `model_reasoning_effort="high"` (the config default model is
refused for `codex exec` on a ChatGPT account). It is not a runner 18 baseline: no
reservation, receipt, or reviewer step, and the responses were judged by reading
them. Prompts were synthetic and are not stored.

Output contract, before and after the 2.0.6 text. Each run used a fresh empty
working directory and a copy of the skill passed by path (`SKILL.md` `3b8fca30` for
2.0.5; `b655ab67` for 2.0.6, the text before the version bump and before the last
Preservation Gate and hold-line wording fixes), so no repository `AGENTS.md` was
loaded. Two runs per
cell; every run read the pinned `SKILL.md`.

| Case | 2.0.5 | 2.0.6 |
| --- | --- | --- |
| `diagnose` on clean text | a free-form "no problem" sentence (2/2) | the one-line no-issue reply `SKILL.md` names (2/2) |
| high-stakes contract clause, no mode | corrected text only (2/2) | corrected text, then a needs-check line (2/2) |
| explicit call with no text | asks for the text (2/2) | asks for the text (2/2) |
| `polish` keeps a reporting verb | kept (2/2) | kept (2/2) |
| `correct` on an obligation sentence | exact expected sentence (2/2) | exact expected sentence (2/2) |
| explicit call asking for translation | refuses, no English (2/2) | refuses, no English (2/2) |

Discovery and activation, with the installed skill (`~/.agents/skills` link to
this checkout, 2.0.5 text; the activation bounds did not change in 2.0.6):

- explicit `$korean-writing-editor`: the rollout carries the installed `SKILL.md`
  as an injected skill block, and the reply is the corrected sentence (1/1 checked
  in a saved rollout, 2/2 replies correct);
- explicit `/korean-writing-editor`: the agent reads the installed `SKILL.md` and
  replies with the corrected sentence (2/2);
- implicit spelling request with no skill name: the skill loads and the reply is
  the corrected sentence (2/2);
- near-miss translation request with no skill name: the skill does not load and
  Codex translates normally (2/2).

Limits: n = 2 per cell; one model and effort; the 2.0.5-to-2.0.6 difference shows
in two of six cases, and the other four already passed on 2.0.5. Those four guard
against regressions; they do not tell the texts apart. The runner 18 baseline has
still not been executed.

## Claude Code activation probe, 2026-10-02

Claude Code 2.1.284, `claude -p`, Opus 5.5 at effort high, with the 2.0.6 skill
copied into a fresh repository's `.claude/skills/` and `--setting-sources project`
(`SKILL.md` `16ce16cb3964`). No skill name in the prompt. Prompts were synthetic and
are not stored.

| Request | Skill tool called | Reply |
| --- | --- | --- |
| spelling and spacing check of one Korean sentence | 2/2 | the corrected sentence only (2/2) |
| translate one Korean sentence into English | 0/2 | a normal translation (2/2) |

This matches the Codex result above, so implicit activation is right on both hosts
with the English-only description. Real use is still 0 on both hosts, so there is
no missed request to justify Korean trigger words in the description. n = 2 per
cell; about $0.25 in all.

## Codex trigger eval and preservation probe, 2026-10-02

Recorded in full in the [skill trigger eval](../../../research/2026-10-skill-trigger-eval/README.md).

**Trigger eval.** Codex gpt-6-astra/high with every installed skill and plugin. The 2.0.6 text
(`16ce16cb`) loaded for 24 of 24 proofreading requests: spelling and spacing, polishing an
email, typos only, a report paragraph, a notice, a PR description, and so on. It loaded for
0 of 24 near-misses: translation, drafting, summary, a 되/돼 question, AI detection,
author imitation, code review, small talk, detector evasion, and expansion. There were 12
prompts per kind with 4 held out, two repeats each. The description stays as it is.

**Preservation probe, 2.0.6 against 2.0.7.** Codex, an isolated home holding only this skill,
`$korean-writing-editor 맞춤법이랑 띄어쓰기 고쳐줘: …` on six synthetic sentences. Each
sentence carries one invariant:
- negated obligation (반드시 … 필요는 없)
- modality (수 있을 것 같)
- a quantity with attribution (약 30%, 밝혔다)
- partial negation (모든 … 아닙니다)
- a limit (두 번 이상, 안 됩니다)
- negation with attribution (반대하지 않았, 말했다)

Both texts kept every invariant in 12 of 12 runs (two repeats each). In 1 of the 12 runs on
2.0.7 the model answered without opening SKILL.md. Stating the invariant list once
(`d8ccefa5`) cost nothing measurable at this n.

## Commands

```bash
python3 scripts/verify.py --skill korean-writing-editor
python3 scripts/verify.py
python3 tests/products/korean-writing-editor/offline/run.py --self-test --scope full
python3 tests/products/korean-writing-editor/live/live_matrix.py --dry-run
git diff --check
```

A live canary (a small real-call check) is optional and reported separately.
Do not describe offline fixture results as evidence of live calls or model
quality. Do not put provider IDs in `SKILL.md`. Live runs are local, explicit,
optional, may cost money, and are not required by CI.
