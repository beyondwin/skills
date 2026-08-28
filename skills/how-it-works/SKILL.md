---
name: how-it-works
description: Use when the user wants to understand how a mechanism or flow works visually, asks for a diagram or step-by-step path, names 그림/길/뼈대/허점, invokes the skill explicitly, or asks 원리부터, 그림으로, 어떻게 돌아가, or 감이 안 와. Do not use for debugging, implementation, review, translation, one-line factual lookup, child-register explanation, or ELI5 requests.
license: Apache-2.0
compatibility: Requires an Agent Skills host that can read this directory and return Markdown text.
metadata:
  version: "1.0.0"
  updated_at: "2026-08-28"
---

# how-it-works

Same machine, chosen rung. The picture holds. Age does not go down.

<HARD-GATE>
Do not explain until `slice`, `type`, `rung`, and `language` are filled.
Violating the letter of this gate is violating the spirit.
If the noun is a civilization (인터넷, AI, 자본주의), do not explain — cut a slice first.
Do not activate on eli5, /eli5, or “explain like I’m 5”. That is a different skill.
Do not use the rung picker, the four-slot gate, or this explanation flow on debugging, implementation, review, translation, one-line lookup, or eli5 requests.
</HARD-GATE>

Prefer explicit invocation: `$how-it-works` on Codex, `/how-it-works` on Claude Code and Grok, and `/how-it-works` or optional `@how-it-works` on Cursor.

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

Infer `type` when the verb is obvious (`vs` → 비교, `어떻게 고치냐` → 절차, `왜/원리` → 개념, `흐름` → 흐름). Ask type only if the guess would change the output. Type inference does not fill `rung`. Do not silently pick a depth.

Missing-slot order: slice → rung → language.

Rung picker (recommendation first):

- **길** — 누가 무엇을 넘기는지 (default)
- **그림** — 한 장
- **뼈대** — 갈림길과 실패
- **허점** — 이 그림이 금 가는 곳

Silent aliases (never print numbers or ages): 쉽게/한눈에/한 장/`5` → 그림; 따라가/`10` → 길; 내부/실무/속/`15` → 뼈대; 한계/깊게/예외/반례/`20` → 허점.

If the prompt already uses domain words (`rebase`, `TTL`, `Raft`), default **뼈대** unless they named the word 그림. Aliases (쉽게, 한눈에, `5`) do not count as naming 그림 — jargon wins.

Intent line:

> {slice}를 **{rung}**로, {particle}를 따라갈게. 안 다루는 것: {out of scope}.

Do not wait for a nod when they already chose the rung. Pause when the slice is surprising or the topic is medical, legal, or financial — then read `references/stakes.md`.

## Runtime

```text
request
  -> fill slice, type, rung, language
  -> emit one intent line
  -> read focused references
  -> emit complete Markdown + Mermaid source + numbered hop list
  -> offer one next move
```

## After EXPLAIN

One next move only:

- 다음 칸 (그림→길→뼈대→허점)
- 흐린 홉 하나
- 다른 각도 (비교 / 절차 / 실패)
- 한 줄로 되말하기

다음 칸 and 흐린 홉 하나 keep the same hop IDs. 다른 각도 may recut the type. 한 줄로 되말하기 patches gaps in chat.

## Required deliverable

The explanation is complete in this chat reply. Do not wait for a renderer. Include all of:

1. one-sentence claim that remains true at 허점
2. Mermaid source in a fenced mermaid block
3. numbered hop list whose identifiers match the diagram
4. rung-specific body
5. adjacent slices this reply does not cover
6. one next move

A missing renderer is not a failed task. Keep the Mermaid source and the numbered hop list.

## Optional preview

A host page, Canvas, or visual preview may be added only after the complete output. It never replaces the required deliverable. Preview failure is non-fatal.

## EXPLAIN

Read `references/output.md`, then `references/visuals.md`. If Korean → `references/korean.md`. If metaphor → the isomorphism section in `output.md`. If medical/legal/financial → `references/stakes.md`.

## Dump gate

| Excuse | Reality |
| --- | --- |
| They asked 설명해줘 so answer now | Wrong type/rung wastes the answer. One question. |
| Topic is obvious | Announce type+rung. If they specified both, 바로. |
| I'll draw the boxes in HTML | Mermaid draws the map. Hand-authored boxes are not a diagram. |
| I'll skip hops because a renderer will draw them | Source plus hop list is required. Rendering is enhancement only. |
| I'll add a preview first and fill chat later | Preview comes after the complete output, and only if useful. |
| They asked 동물로 so use animals | Animals requested still means no animals. Map is mermaid + table. Analogy vehicle is not a mascot. |
| Depth 그림 means simpler than true | 그림 is a smaller true map. False-simple is a bug. |
| They said 쉽게 so pick 그림 | rebase/TTL/Raft still 뼈대. 쉽게 is an alias, not the word 그림. |
| I’ll add sources from memory | Fetch or omit 근거. |
| Korean and English to be safe | One language. Gloss once. |
| I’ll explain the whole internet then zoom | 자르기 first. |

## Red flags

- Essay in the same turn as the first classification when a slot is missing
- `/eli5` handled as this skill
- `여러분`, `답니다`, animals, hand-drawn HTML boxes in place of mermaid
- A reply that omits Mermaid source or the numbered hop list
- 허점 that cannot collapse to 그림

All of these mean: stop, classify, restart the gate.
