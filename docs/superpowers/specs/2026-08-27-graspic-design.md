# graspic Design

**Date:** 2026-08-27

**Status:** Spec approved in chat; implementation has not started

**Install target:** `~/.grok/skills/graspic/` (personal skill)

**Not in scope for this repository’s catalog:** `beyondwin/skills` remains a two-skill public catalog (`korean-writing-editor`, `image-workbench`). This spec is a design record only. Do not add `graspic` to `skills/`, the plugin manifest, README skill table, or `v2.0.0` release artifacts unless governance is explicitly reopened.

## 1. Decision Summary

Create a personal Agent Skill named `graspic` (`grasp` + `pic`).

It is not an agent. It is not ELI5. It does not listen for `eli5`, `/eli5`, or “explain like I’m 5” as invocation. Existing community `eli5` skills stay untouched.

`graspic` helps a person **get a handle on how something works** by following **one particle** through **the same machine** at a chosen rung:

| Printed rung | What the user can do afterwards |
| --- | --- |
| **그림** | Gesture the whole thing in about 30 seconds, with real part names. No baby talk. |
| **길** | Name the actors and walk the happy path. |
| **뼈대** | Walk the important branch, use terms as labels on hops already seen, predict a failure. |
| **허점** | Know where this picture lies, how to inspect, what specialists fight about — and collapse back to the one-line picture. |

The picture does not change movies when the rung changes. Later rungs add joints. They do not retract the backbone.

Output is Grok-TUI-native: GitHub-flavored markdown and mermaid. Not HTML posters. Not `image_gen` diagrams.

Korean prose follows the conservative voice rules of `korean-writing-editor` **for drafting**, without invoking that skill (it is an editor of user-supplied text, not a writer).

## 2. Context

The Claude community `eli5` skill is one line: HTML artifact, big pictures, few words. That is a poster, not a progression.

[eli5.cc](https://eli5.cc) already ships four depths, a visual map, citations, and confidence. Its DNS and quantum pages still reuse one metaphor at every depth, one infographic for all rungs, and treat Expert as denser jargon. Quantum still uses “0 and 1 at the same time.” DNS never walks a single query hop by hop.

This skill steals eli5.cc’s **chrome idea** (one idea, several resolutions, written page primary) and rejects its **pedagogy** (same cute lie, expert = vocabulary).

Grok Build TUI renders mermaid as Unicode box art (`flowchart`, `sequenceDiagram`, `stateDiagram`). HTML/CSS/JS artifacts do not render as UI. Imagine cartoons fail at labeled structure. “More visual than eli5” here means a diagram whose boxes are 1:1 with the hop list.

## 3. Goals

1. Let the user pick **그림 / 길 / 뼈대 / 허점** and receive that rung of the same causal skeleton.
2. Ask at most one missing question before explaining. If topic and rung are already present, explain.
3. Make flows graspable by following one particle (one DNS lookup, one handshake, one commit).
4. Write Korean that sounds like a person sitting next to you, not translated ELI5.
5. Keep the skill discoverable without stealing `/eli5`.
6. Stay a personal install. Do not expand the public two-skill catalog.

## 4. Non-goals

- Replacing, forking, or aliasing the community `eli5` skill as `name:`.
- Auto-invoking on the words `eli5`, `explain like I'm 5`, `5살처럼`.
- HTML artifacts, CSS posters, or `image_gen` as the visual channel.
- Emitting all four rungs unless the user asked for a full ladder.
- A public library of explanations, SEO pages, or citations-from-memory theater.
- Installing into `beyondwin/skills` `skills/` or claiming plugin-bundle membership.
- Curriculum / “Learn a whole subject” (eli5.cc Learn). One question, one machine, one rung.
- Baby talk, animal mascots, or age-as-intelligence.

## 5. Name and Discovery

| Piece | Value |
| --- | --- |
| Directory and `name:` | `graspic` |
| Slash | `/graspic` |
| Wordplay | grasp + pic; sounds like *graphic* |
| Korean face | 그래스픽 (spoken). Do not invent a second Korean product name. |
| One-line promise | 같은 기계를 고른 칸으로. 그림이 잡힌다. |

`description` states **when to use**, not how. It must not summarize the workflow. It must not include `eli5`.

Draft (WHEN only):

```yaml
name: graspic
description: Use when the user wants to grasp how something works, asks for a visual or flow explanation, types /graspic, names a rung 그림/길/뼈대/허점, or asks in Korean to 원리부터 / 그림으로 / 어떻게 돌아가 / 감이 안 와. Do not use for debugging, implementing, reviewing, translating, one-line factual lookups, or child-register explainers.
```

Synonyms that fill the **rung** slot after `graspic` is already active (not invocation):

| User says | Rung |
| --- | --- |
| 쉽게, 한눈에, 한 장, `5` | 그림 |
| 흐름, 원리, 따라가, `10` | 길 |
| 내부, 실무, 속, `15` | 뼈대 |
| 한계, 깊게, 예외, 반례, `20` | 허점 |

Numbers and school-age talk are never printed. They are silent aliases only.

## 6. Interaction

Classify out loud in one line before any question, so the user can override:

> DNS네. **길**로 보고, `google.com` 조회 하나를 따라갈게.

Three paths. Classification always happens. Ceremony scales; the gate does not disappear.

| Path | When | Behavior |
| --- | --- | --- |
| **바로** | Slice and rung already present (`DNS 길`, `/graspic TLS 그림`) | One-line plan, then explain. No extra question if the plan is unsurprising. |
| **하나** | One required slot missing | Ask **one** question. Closed choice when possible. |
| **자르기** | The noun is a civilization (`인터넷`, `AI`, `자본주의`) | Do not explain. Offer three concrete slices + Other. |

Do not stack two questions. Do not re-ask a filled slot. Do not survey genre, audience, or tone.

### Required slots before EXPLAIN

`slice`, `type`, `rung`, `language`. Infer `type` from the verb when obvious (`vs` → comparison, `어떻게 고치냐` → procedure, `왜/원리` → concept, `흐름` → flow). Ask type only when the inference would change the output.

Ask missing slots in this order:

1. **Slice** — only if the topic is too large.
2. **Rung** — 그림 / 길 / 뼈대 / 허점. Put the recommendation first. Default **길**. If the prompt already uses domain words (`rebase`, `TTL`, `Raft`), default **뼈대**.
3. **Language** — only if mixed: 한국어 / English / 한영 혼용 (prose Korean, identifiers English).

Intent line immediately before the explanation:

> DNS를 **길**로, `google.com` 조회 하나를 따라갈게. 안 다루는 것: DNSSEC, DoH.

Do not stop for a nod when the user already chose the rung. Stop a beat when the slice was surprising, or when the topic is medical, legal, or financial (banner, then explain mechanism only).

### After every explanation

Offer exactly one next move:

- next rung (그림→길→뼈대→허점)
- the foggiest hop in the last diagram
- another angle (comparison / procedure / failure)
- say the path back in one line

Not a quiz. Do one chosen thing.

### Hard gates

- No explanation in the same turn as the first classification unless **바로** (every required slot present and unsurprising).
- No essay on an uncut blob (`인터넷 설명해줘`).
- High-stakes banner before EXPLAIN when the slice is advice-shaped medical, legal, or financial.
- Metaphor isomorphism is internal and blocking: if the vehicle cannot carry the causal arrow, omit the metaphor.
- Time-sensitive or disputed claims: fetch before naming a source. No `## 근거` from memory.

## 7. Same skeleton

Every rung fills the same slots. Empty slots are allowed. Contradictory fillings are not.

1. Identity (what kind of thing: entity, sequential process, emergent process)
2. Function
3. Backbone (one sentence at 그림, more clauses later)
4. Parts (empty at 그림, labeled from 길)
5. Couplings (from 뼈대)
6. Boundaries (one hedge at 그림; regime at 허점)
7. “This is not X”
8. Optional handle (analogy), mapped, with a break line
9. Optional footer check: if they pick “한 줄로 되말하기,” patch only the gaps

**Collapse test:** shrink 허점 to three sentences; you must get 그림, not a different movie.

**No-retraction test:** later rungs may say “그림 left out X.” They may not say “그림 was wrong,” unless 그림 was labeled a toy that remains a special case.

**Hop IDs stay stable.** 그림 hop 1 is 허점 hop 1. “3번만 더 깊게” must work.

**Term monotonicity:** a word introduced at 길 keeps its meaning at 허점. If 허점 must split a term, 길 should have used a more careful everyday word or flagged the split.

**Ontology lock:** if 허점 is an emergent process, 그림 may not be an agent with a goal.

**Metaphor policy:** optional, single, mapped, broken-out. 그림 may open one analogy. Later rungs use the same analogy or drop it. Never switch pizza → army → water. Ban *wants / tries / decides* for non-agents. Qubit-as-spinning-coin and DNS-as-phonebook-without-cache fail the isomorphism test; do not ship them as proof.

## 8. Output contract

Chat is the artifact. Do not write a spec file per explanation. Save to a file only if the user asks.

Shared chrome, in this order:

```text
# {slice}  ·  {그림|길|뼈대|허점}

{high-stakes banner, or omit this line}

## 한 줄
(one sentence that remains true at 허점)

## 지도
(mermaid; caption is the diagram’s claim)

## 본문
(type-specific; see below)

## 지금 다루지 않은 것
(2–5 adjacent slices as prose links, not a second essay)

다음:
- …
```

If a metaphor was used, include **이 그림이 깨지는 지점** as a short section. At 허점 that *is* the body; do not duplicate a cute “breaks at” box.

Length is a budget, not a target. Restating the same sentence to fill space is a failure.

### Rung overlay

| Rung | Map | Body | Forbidden |
| --- | --- | --- | --- |
| **그림** | Happy-path pipeline, 5–7 boxes | Identity, use, ≤2-joint backbone. Optional one analogy plus one break line. | Baby talk, second metaphor, formulas, `여러분`, `답니다` |
| **길** | `sequenceDiagram`, 4–6 actors, same path, message numbers = hop IDs | Numbered hops: who holds it, what they hand off, where it stops on failure | New metaphor, architecture hairball |
| **뼈대** | Same sequence + `alt`/`opt` (cache, error) | Terms as labels on hops already seen. What happens if you change one part. Common mistakes. Optional second flowchart of the hidden decision | Restarting from 그림, pizza |
| **허점** | Failure/regime **table**. Not a prettier poster | What this picture cannot see. Rivals mapped onto the same slots. How you would inspect. Collapse to the one-liner | Re-teaching 그림, name-dropping without a one-line “what they showed” |

### Type recipes (body only; chrome stays)

| Type | Body |
| --- | --- |
| **개념** | One relation → popular wrong picture → correction |
| **흐름** | Walk the hops. 길 gets the sequence diagram. 그림 gets boxes only |
| **비교** | Required GFM table: what it optimizes / what it gives up / failure shape / how to undo. The 한 줄 is a **recommendation**, not a tie. 그림 uses 3 axes; 길 uses 5 |
| **절차** | Start state → end state. Each step is one state change. Recover from failure. “What is rebase” is not a command list |

`리베이스가 뭐야` is concept/flow. `conflict 난 다음` is procedure. Classify from the **job**, not the noun.

### Language

| Request | Output |
| --- | --- |
| Korean | Korean prose. First use of a term: `리베이스(rebase)`. Then one form. |
| English | English. No sprinkled Hangul. |
| 한영 혼용 | Korean prose, English identifiers in backticks. |
| Mixed / unclear | Ask once (required slot). |

Do not emit a full bilingual duplicate.

### Citations

```text
## 근거
- 검증함: {title} — {url}   (only URLs fetched this turn)
- 불확실: {claim} — 확인하지 않음
```

If nothing was fetched, omit the heading. Invented arXiv IDs are a failure. Stable textbook facts need no theater-citation.

### High stakes

Insert after the title, keep in the closer:

```text
이건 시술/계약/투자 조언이 아니다. 단순화는 예외와 관할을 지운다.
결정 전에 자격이 있는 사람에게 물어라.
```

그림 still cannot turn “may” into “is,” or “should” into a personal directive. Mechanism only.

## 9. Visual rules

One diagram, one claim. Boxes and hop IDs are 1:1. If they drift, fix the diagram. Do not pad prose to match.

ASCII node IDs, quoted labels:

```text
A["커밋"] --> B["스테이징"]
```

No `style` / `classDef` / `click`. If 그림 needs more than 12 boxes, the slice is wrong — go back to 자르기.

### Diagram type by rung (flows)

| Rung | Required | Optional second | Forbidden |
| --- | --- | --- | --- |
| 그림 | Happy-path boxes, 5–7, nicknames allowed but real names present | None | 8-lifeline sequence, mind map |
| 길 | `sequenceDiagram`, happy path | Cast list in prose | Architecture blob |
| 뼈대 | Same sequence + alt/opt | Flowchart of the decision the sequence hides | New unrelated metaphor drawing |
| 허점 | Failure/regime table; state diagram if needed | Inspection as a code block | Infographic restating 그림 |

### Diagram type by kind (when it is not a flow)

| Kind | Map |
| --- | --- |
| 개념 | One relation. Wrong picture in prose first; diagram is the corrected relation |
| 비교 | The table is the main picture. mermaid is the **choice path**, not two posters |
| 절차 | State transitions. Boxes are states, not commands |
| 되먹임 (markets, congestion, evolution) | 그림 one loop; 길 two loops; 뼈대 polarities and delay. Do not hide loops in a sequence |

Mind maps are not the default. They are for “what exists in this field,” never for “how does this happen.”

Mermaid types the TUI actually draws: `flowchart` / `graph`, `sequenceDiagram`, `stateDiagram`. Other types may show as a framed source listing. The hop list must remain readable if the diagram engine fails.

Analogies are not the map. The map is who holds the particle.

Redraw if: a hop has no box, a box has no hop, 그림 introduces an unglossed term, 허점 is a different machine from 그림, or a comparison has two pretty pictures and no recommendation.

## 10. Korean voice

Do not activate `korean-writing-editor`. Steal its constraints for **drafts**:

- **해요체.** Not lecture `합니다`. Not baby `답니다`. Banmal is not the default.
- No `우리` / `여러분` / `당신`. Korean drops subjects.
- Do not translate English word order. Ban `그것은 ~이다`, `당신은 ~할 수 있습니다`, `~에 의해`, `~하는 것을 허용한다`.
- Do not pad with `쉽게 말하면`, `즉`, `다시 말해`, `이제 설명해볼게요`.
- Phenomenon before analogy. Analogy only when needed, with the break line.
- Do not jitter sentence length on purpose. Do not synonym-spin to “sound human.” That is detector-evasion-shaped, and the editor skill forbids it.
- Do not inflate possibility into certainty, advice into obligation, correlation into cause.
- Gloss a term once.

Awkward eli5 Korean (do not emit):

> DNS는 인터넷의 전화번호부와 같아요. 여러분이 웹사이트 이름을 입력하면, DNS가 그 이름을 컴퓨터가 이해할 수 있는 특별한 숫자로 바꿔준답니다!

그림 target:

> 사이트 이름은 사람이 읽고, 컴퓨터는 숫자 주소를 본다. DNS는 그 둘을 이어 주는 조회다.

## 11. Skill files

Installed payload (personal):

```text
~/.grok/skills/graspic/
  SKILL.md
  references/
    output.md      # chrome, rung overlay, type recipes, metaphor test
    visuals.md     # mermaid, rung diagrams, TUI limits
    korean.md      # 해요체, translationese, one-gloss
    stakes.md      # medical / legal / financial
```

Optional share path: `~/.agents/skills/graspic/` as a copy or symlink. Directory name must match `name:`.

**SKILL.md** (always loaded) contains only:

- YAML `name`, `description` (WHEN only), `argument-hint: "<topic> [그림|길|뼈대|허점]"`
- One-sentence principle
- Hard gate
- Classify + 바로 / 하나 / 자르기
- Rung table + silent aliases
- One-question rule
- Intent-line template
- Footer recipe
- Rationalization table (dumping only)
- Pointers to `references/` — do not paste recipes again

Keep SKILL.md tight. Recipes live in `output.md`. One home per fact.

**Do not ship** in the installed skill: HTML templates, mermaid tutorials, bilingual duplicate examples, “be cute / use animals,” test runners, this design document.

### Metaphor isomorphism (in `output.md`, not its own file)

1. List source parts you will name.
2. Map each to a vehicle part.
3. Write one disanalogy per mapping.
4. If a central part has no image, or the lie would reverse the causal arrow, drop the metaphor.
5. The “깨지는 지점” section *is* that disanalogy list.

## 12. Error handling

| Condition | Behavior |
| --- | --- |
| Missing rung or slice | One question. No mermaid in that turn |
| Blob noun | 자르기. Three slices |
| User already used domain jargon and asked 쉽게 | Default 뼈대 unless they explicitly said 그림. Do not infantilize |
| No isomorphic metaphor | Omit metaphor. Map still required |
| High-stakes slice | Banner + mechanism. No dose, no “you should” |
| Named paper/RFC | Fetch first, or omit 근거 |
| HTML / artifact / animals requested | mermaid + markdown anyway |
| Mixed KO/EN | One language question, then one output language |
| Host cannot draw mermaid | Hop list still stands |

## 13. Testing

No skill without a failing baseline. Tests live **outside** the installed payload (personal folder). They do not extend `beyondwin/skills` CI.

### Discipline (dumping / skipping gates)

Run without the skill first. Expect instant essays, animals, HTML. Then with the skill.

| Pressure | With skill |
| --- | --- |
| `빨리. 인터넷 어떻게 돼` | Three slices. No OSI novel |
| `ELI5로 HTML 아티팩트 DNS` | Does **not** activate on ELI5-as-invocation. If already in `/graspic` and they meant 그림: 그림 + mermaid, no HTML |
| `시니어야. 리베이스 vs merge 쉽게, 동물로` | Comparison + 뼈대 (or 길). No animals. Table with a recommendation |
| `항응고제 왜 밥이랑, 5살처럼` | If invoked as graspic: banner + 그림. No dose, no “하라” |
| `git rebase가 뭐야` vs `conflict 어떻게` | Concept/flow vs procedure |
| `/eli5 DNS` | **No-op for this skill.** Leave it to whatever eli5 the host has |

### Shape fixtures

Score the artifact: required substrings / forbidden substrings.

| Case | Must | Forbidden |
| --- | --- | --- |
| `gate-dump-01` `DNS 설명해` after `/graspic` | Question or intent line; no mermaid if rung missing | Full essay turn 1 |
| `html-01` | mermaid flowchart | `<html`, `<style`, `<div class=` |
| `rung-허점-01` expert prompt | Domain words in paragraph 1 | “imagine a classroom”, animals |
| `type-cmp-01` `REST vs GraphQL 길` | Table + recommendation | “both have pros and cons” as 한 줄 |
| `scope-01` `인터넷` | Three slice options | End-to-end OSI dump |
| `ko-gloss-01` `리베이스 원리 길` | Korean prose, `rebase` glossed once | Full EN duplicate |
| `skeleton-01` 그림 then 허점 in-thread | Same hop IDs; 허점 collapses to 그림 | New backbone |

Wording micro-tests (5+ reps, no-guidance control) before full pressure runs: hard-gate XML vs soft “prefer asking”; recipe vs “never HTML”; default 길 vs default 그림 on a senior prompt.

## 14. Privacy and rights

- Do not persist user topics as fixtures or logs.
- Do not upload content.
- Citations are user-visible URLs from this turn, not a private corpus.
- High-stakes material is explanation of mechanism, not advice.
- This skill adds no telemetry.

## 15. Acceptance criteria

Implementation is done only when:

1. `~/.grok/skills/graspic/SKILL.md` exists with `name: graspic` matching the directory.
2. `description` contains no workflow summary and no `eli5`.
3. `/eli5` does not activate this skill in a host that also has a community eli5.
4. `/graspic DNS 길` explains in the next turn without asking rung.
5. `/graspic 인터넷` offers slices and does not dump OSI.
6. 그림 → 허점 in one thread keeps hop IDs and passes the collapse test.
7. Korean 그림 output has no `여러분` / `답니다` / phonebook-as-proof.
8. Visual channel is mermaid, not HTML, not `image_gen`.
9. Comparison 한 줄 is a recommendation.
10. Medical/legal/financial slices carry the banner and no personal directive.
11. `beyondwin/skills` plugin still discovers exactly two catalog skills.
12. Baseline pressure cases fail without the skill and pass with it for dumping, HTML, animals, and blob-scope.

## 16. Approved decisions

- Personal skill, not public catalog: approved.
- Name `graspic` (grasp + pic): approved.
- Separate from eli5; do not listen for eli5 as invocation: approved.
- Rungs 그림 / 길 / 뼈대 / 허점: approved.
- Intake 바로 / 하나 / 자르기: approved.
- Output chrome + rung overlay + four types: approved.
- Mermaid map rules: approved.
- Korean 해요체 voice (editor constraints, not the editor skill): approved.
- File split SKILL.md + `output.md` / `visuals.md` / `korean.md` / `stakes.md`: approved.
- Default rung 길; domain jargon upgrades to 뼈대: approved.

## 17. Implementation next step

After the user reviews this spec, the next skill is **writing-plans**. Do not implement SKILL.md in the same breath as spec approval.
