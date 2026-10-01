---
name: how-it-works
description: Use when the user wants to understand how a mechanism or flow works visually, asks for a diagram or step-by-step path, names 그림/길/뼈대/허점, or asks 원리부터, 그림으로, 어떻게 돌아가, or 감이 안 와. Do not use for debugging, implementation, review, translation, one-line factual lookup, child-register explanation, or ELI5 requests.
license: Apache-2.0
compatibility: Requires an Agent Skills host that can read this directory and return Markdown text.
metadata:
  version: "3.0.1"
  updated_at: "2026-09-28"
---

# how-it-works

Same machine, chosen rung. The picture holds.

<HARD-GATE>
Do not explain until `slice` is a cut mechanism.
Fill `type` and `language` by inference. Fill `rung` by precedence, including
default 그림. Announce the rung in the intent line. Explain in the same turn.
If the noun is a civilization (인터넷, AI, 자본주의), do not explain — cut a slice first.
Do not activate on eli5, /eli5, or “explain like I’m 5”. That is a different skill.
Do not use this explanation flow on debugging, implementation, review, translation, one-line lookup, or eli5 requests.
</HARD-GATE>

Prefer explicit invocation: `$how-it-works` on Codex and `/how-it-works` on Claude Code.

## Classify

Say one line before any question or explanation, so the user can redirect on the next turn.
Use only the selected language. In Korean, use this intent line, picking 을/를 and
이/가 by the final consonant of the word before it:

> {slice}을/를 **{rung}** 깊이로 설명할게요. {moving_thing}이/가 이동하는 순서를 따라가요.

In English, state the same intent in English without repeating the Korean line.
The intent line may add the out-of-scope slice, in the same language and register.

Paths:

| Path | When | Do |
| --- | --- | --- |
| Direct | slice is a cut mechanism | Fill rung by precedence. Intent line, then explain in the same turn. |
| Ask one | slice missing, conflicting rungs, or mixed KO/EN that would change the output | Ask one closed question. |
| Cut | blob noun | Three slices + Other. No essay. |

How these paths apply to common requests:

- Re-explaining your own earlier answer: the slice is the one mechanism that answer rests on.
- A bundled ask that is not a mechanism (pending decisions, a recap): answer it after the next move as a short separate list.
- More than one mechanism in the request: Ask one, or Cut.

Do not stack two questions. Do not re-ask a filled slot. Do not survey genre, audience, or tone.

## Slots

Required before EXPLAIN: `slice`, `type`, `rung`, and `language`. Infer `type`
and `language`. Fill `rung` by precedence. Do not wait for a user token for
`rung`.

Infer `type` when the verb is obvious (`vs` → 비교, `어떻게 고치냐` → 절차, `왜/원리` → 개념, `흐름` → 흐름). Ask type only if the guess would change the output. Type inference does not fill `rung`.

Missing-slot order: slice, then a language question only if KO/EN mix would change the reply.

Rungs:

- **그림** — 한 장 (default)
- **길** — 누가 무엇을 넘기는지
- **뼈대** — 갈림길과 실패
- **허점** — 이 그림이 금 가는 곳

Depth precedence: explicit rung > explicit depth alias > existing jargon default > default 그림
An explicitly selected 그림/길/뼈대/허점 (picture/path/skeleton/fracture) wins.
Explicit 쉽게/한눈에/한 장 selects 그림 even with jargon such as rebase, TTL, or Raft.
Interpret numeric aliases only when explicitly selecting depth; numbers in the topic are not depth choices.
Never replace a filled rung.

Silent aliases (never print numbers or ages): 쉽게/한눈에/한 장/감이 안 와 → 그림; 따라가 → 길; 내부/실무/속 → 뼈대; 한계/깊게/예외/반례 → 허점. Explicit numeric depth selections use `5` → 그림, `10` → 길, `15` → 뼈대, and `20` → 허점. `Raft term 20`, `HTTP/2`, and `5개 노드` contain topic data, not depth choices.

If the prompt already uses domain words (`rebase`, `TTL`, `Raft`), default **뼈대** only when neither a rung nor a depth alias was supplied.

Medical, legal, or financial topic: read `references/stakes.md`, add its banner, and still explain in the same turn.

## Runtime

```text
request
  -> fill slice, type, rung, language
  -> missing rung → default 그림
  -> emit one intent line
  -> read focused references
  -> emit complete Markdown + Mermaid source + numbered hop list
  -> offer one next move
```

When the host can read files, read `references/output.md` (and `references/korean.md` for a Korean reply) before replying.
Only when the host cannot read files this turn, emit the complete required deliverable from the skeleton in Required deliverable.

## After EXPLAIN

One next move only:

- 다음 칸 / Next rung (그림→길→뼈대→허점 / picture→path→skeleton→fracture)
- 흐린 홉 하나 / One blurry hop
- 다른 각도 / Another angle
- 한 줄로 되말하기 / Say it back in one line

그림's default next move is 길, naming a hop ID.

다음 칸 and 흐린 홉 하나 keep the same hop IDs. 다른 각도 recuts the type (개념, 흐름, 비교, or 절차). 한 줄로 되말하기 patches gaps in chat.

## Required deliverable

The explanation is complete in this chat reply. Do not wait for a renderer. Include all of, in this order:

1. one-sentence claim that remains true at 허점
2. numbered hop list whose identifiers match the diagram
3. Mermaid source in a fenced mermaid block
4. rung-specific body
5. adjacent slices this reply does not cover
6. one next move

Skeleton, mirrored from `references/output.md`, which owns it. Headings, intent line,
body, banner, and next move all use the reply language.

````markdown
{intent line}

# {slice} · {그림|길|뼈대|허점}

{high-stakes banner or omit}

## 한 줄

## 지도

1. **H1** — {what moves or changes}
2. **H2** — {what moves or changes}

```mermaid
{diagram source}
```

## 본문

## 지금 다루지 않은 것

다음: {exactly one move}
````

English replies use the same skeleton with these labels: `# {slice} · {picture|path|skeleton|fracture}`, `## One sentence`, `## Map`, `## Body`, `## Adjacent slices`, `Next:`.

Korean replies use 해요체. At 그림, Body does not walk the hops again.

Mermaid labels carry the hop ids (`H1: …`; a branch reuses its parent id, `H3a`).
A missing renderer is not a failed task; the Mermaid source and the numbered hop list
stay. Every rung keeps the 그림 hop ids and explains added detail against the same
hops. At 허점, add the failure/regime table to the body without replacing the map.

## Optional preview

A host page, Canvas, or visual preview may be added only after the complete output. It never replaces the required deliverable. Preview failure is non-fatal.

## EXPLAIN

Read `references/output.md`, then `references/visuals.md`. If Korean → `references/korean.md`. If metaphor → the isomorphism section in `output.md`. If medical/legal/financial → `references/stakes.md`. For claims that depend on date, jurisdiction, or material uncertainty, also read `references/sources.md`.

## Dump gate

| Excuse | Reality |
| --- | --- |
| They asked 설명해줘 so answer now | Missing slice still waits. Missing rung takes default 그림, announces, explains. |
| Topic is obvious | Announce type+rung. Explain same turn. |
| I'll draw the boxes in HTML | Mermaid draws the map. Hand-authored boxes are not a diagram. |
| I'll skip hops because a renderer will draw them | Source plus hop list is required. Rendering is enhancement only. |
| I'll add a preview first and fill chat later | Preview comes after the complete output, and only if useful. |
| They asked 동물로 so use animals | Animals requested still means no animals. Map is mermaid + table. Analogy vehicle is not a mascot. |
| Depth 그림 means simpler than true | 그림 is a smaller true map. False-simple is a bug. |
| I’ll add sources from memory | Verify in this turn or mark the dependent claim unverified. Never invent a reference. |
| Korean and English to be safe | One language. Gloss once. |
| I’ll explain the whole internet then zoom | Cut first. |

## Red flags

- Essay in the same turn as the first classification when slice is missing
- `/eli5` handled as this skill
- `여러분`, `답니다`, animals, hand-drawn HTML boxes in place of mermaid
- A reply that omits Mermaid source or the numbered hop list
- A Mermaid hop id with no matching `**Hk**` list item (a branch `H3a` matches `**H3**`), or hop list items without `**Hk**`
- 허점 that cannot collapse to 그림

All of these mean: stop, classify, restart the gate.
