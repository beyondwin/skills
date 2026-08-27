---
name: graspic
description: Use when the user wants to grasp how something works, asks for a visual or flow explanation, types /graspic, names a rung 그림/길/뼈대/허점, or asks in Korean to 원리부터 / 그림으로 / 어떻게 돌아가 / 감이 안 와. Do not use for debugging, implementing, reviewing, translating, one-line factual lookups, or child-register explainers.
license: Apache-2.0
compatibility: Requires local Agent Skills file access. Mermaid is best-effort; hop lists must remain readable if the host cannot draw diagrams.
argument-hint: "<topic> [그림|길|뼈대|허점]"
metadata:
  version: "2.0.0"
  updated_at: "2026-08-27"
---

# graspic

Same machine, chosen rung. The picture holds. Age does not go down.

<HARD-GATE>
Do not explain until `slice`, `type`, `rung`, and `language` are filled.
Violating the letter of this gate is violating the spirit.
If the noun is a civilization (인터넷, AI, 자본주의), do not explain — cut a slice first.
Do not activate on eli5, /eli5, or “explain like I’m 5”. That is a different skill.
</HARD-GATE>

## Classify

Say one line before any question so the user can override:

> {slice}네. **{rung}**로 보고, {particle}를 따라갈게.

Paths:

| Path | When | Do |
| --- | --- | --- |
| 바로 | slice + rung already present | One-line plan. Explain next if unsurprising. |
| 하나 | one required slot missing | Ask one closed question. |
| 자르기 | blob noun | Three slices + Other. No essay. |

Do not stack two questions. Do not re-ask a filled slot. Do not survey genre, audience, or tone.

## Slots

Required before EXPLAIN: `slice`, `type`, `rung`, `language`.

Infer `type` when the verb is obvious (`vs` → 비교, `어떻게 고치냐` → 절차, `왜/원리` → 개념, `흐름` → 흐름). Ask type only if the guess would change the output.

Missing-slot order: slice → rung → language.

Rung picker (recommendation first):

- **길** — 누가 무엇을 넘기는지 (default)
- **그림** — 한 장
- **뼈대** — 갈림길과 실패
- **허점** — 이 그림이 금 가는 곳

Silent aliases (never print numbers or ages): 쉽게/한눈에/한 장/`5` → 그림; 흐름/원리/따라가/`10` → 길; 내부/실무/속/`15` → 뼈대; 한계/깊게/예외/반례/`20` → 허점.

If the prompt already uses domain words (`rebase`, `TTL`, `Raft`), default **뼈대** unless they named the word 그림. Aliases (쉽게, 한눈에, `5`) do not count as naming 그림 — jargon wins.

Intent line:

> {slice}를 **{rung}**로, {particle}를 따라갈게. 안 다루는 것: {out of scope}.

Do not wait for a nod when they already chose the rung. Pause when the slice is surprising or the topic is medical, legal, or financial — then read `references/stakes.md`.

## After EXPLAIN

One next move only:

- 다음 칸 (그림→길→뼈대→허점)
- 흐린 홉 하나
- 다른 각도 (비교 / 절차 / 실패)
- 한 줄로 되말하기

## EXPLAIN

Read `references/output.md`, then `references/visuals.md`. If Korean → `references/korean.md`. If metaphor → the isomorphism section in `output.md`. If medical/legal/financial → `references/stakes.md`.

## Dump gate

| Excuse | Reality |
| --- | --- |
| They asked 설명해줘 so answer now | Wrong type/rung wastes the answer. One question. |
| Topic is obvious | Announce type+rung. If they specified both, 바로. |
| HTML will look nicer | HTML tags are not the visual channel. Mermaid is. |
| They asked 동물로 so use animals | Animals requested still means no animals. Map is mermaid + table. Analogy vehicle is not a mascot. |
| Depth 그림 means simpler than true | 그림 is a smaller true map. False-simple is a bug. |
| They said 쉽게 so pick 그림 | rebase/TTL/Raft still 뼈대. 쉽게 is an alias, not the word 그림. |
| I’ll add sources from memory | Fetch or omit 근거. |
| Korean and English to be safe | One language. Gloss once. |
| I’ll explain the whole internet then zoom | 자르기 first. |

## Red flags

- Essay in the same turn as the first classification when a slot is missing
- `/eli5` handled as this skill
- `여러분`, `답니다`, animals, HTML artifacts
- 허점 that cannot collapse to 그림

All of these mean: stop, classify, restart the gate.
