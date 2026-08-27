# Output

Chat is the artifact. Do not write a spec file per explanation. Save to a file only if the user asks. Visual channel is mermaid + GFM, not HTML artifacts.

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

**Ontology lock:** if 허점 is an emergent process, 그림 may not be an agent with a goal.

**Term monotonicity:** a word introduced at 길 keeps its meaning at 허점. If 허점 must split a term, 길 should have used a more careful everyday word or flagged the split.

Chrome order is authoritative. Length is a budget, not a target. Restating the same sentence to fill space is a failure.

```text
# {slice}  ·  {그림|길|뼈대|허점}

{banner or omit}

## 한 줄

## 지도

## 본문

## 지금 다루지 않은 것

다음:
```

- 한 줄: one sentence that remains true at 허점
- 지도: mermaid; caption is the diagram’s claim
- 본문: type-specific; see recipes below
- 지금 다루지 않은 것: 2–5 adjacent slices as prose links, not a second essay
- If a metaphor was used, include **이 그림이 깨지는 지점** as a short section. At 허점 that *is* the body; do not duplicate a cute “breaks at” box.

## Rung overlay

| Rung | Map | Body | Forbidden |
| --- | --- | --- | --- |
| **그림** | Happy-path pipeline, 5–7 boxes | Identity, use, ≤2-joint backbone. Optional one analogy plus one break line. | Baby talk, second metaphor, formulas, `여러분`, `답니다` |
| **길** | `sequenceDiagram`, 4–6 actors, same path, message numbers = hop IDs | Numbered hops: who holds it, what they hand off, where it stops on failure | New metaphor, architecture hairball |
| **뼈대** | Same sequence + `alt`/`opt` (cache, error) | Terms as labels on hops already seen. What happens if you change one part. Common mistakes. Optional second flowchart of the hidden decision | Restarting from 그림, pizza |
| **허점** | Failure/regime **table**. Not a prettier poster | What this picture cannot see. Rivals mapped onto the same slots. How you would inspect. Collapse to the one-liner | Re-teaching 그림, name-dropping without a one-line “what they showed” |

## Type recipes (body only; chrome stays)

| Type | Body |
| --- | --- |
| **개념** | One relation → popular wrong picture → correction |
| **흐름** | Walk the hops. 길 gets the sequence diagram. 그림 gets boxes only |
| **비교** | Required GFM table: what it optimizes / what it gives up / failure shape / how to undo. The 한 줄 is a **recommendation**, not a tie. 그림 uses 3 axes; 길 uses 5 |
| **절차** | Start state → end state. Each step is one state change. Recover from failure. “What is rebase” is not a command list |

`리베이스가 뭐야` is concept/flow. `conflict 난 다음` is procedure. Classify from the **job**, not the noun.

## Citations

```text
## 근거
- 검증함: {title} — {url}   (only URLs fetched this turn)
- 불확실: {claim} — 확인하지 않음
```

If nothing was fetched, omit the heading. Invented arXiv IDs are a failure. Stable textbook facts need no theater-citation.

## Metaphor isomorphism

Optional, single, mapped, broken-out. 그림 may open one analogy. Later rungs use the same analogy or drop it. Never switch pizza → army → water. Ban *wants / tries / decides* for non-agents.

1. List source parts.
2. Map each to a vehicle part.
3. One disanalogy per mapping.
4. If a central part has no image or the lie reverses the causal arrow, drop the metaphor.
5. 깨지는 지점 is that list. At 허점 this is the body.

Forbidden as proof: qubit spinning coin; DNS phonebook with no cache.
