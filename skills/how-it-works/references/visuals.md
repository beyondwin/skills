# Visuals

Default: a fenced Mermaid block in the chat Markdown, plus a numbered hop list that still reads when the diagram is shown as source. No host-specific drawing tool is required. HTML boxes are not substitutes for Mermaid.

At 그림, the numbered hops are the human map. Put them before the mermaid fence in Map. Mermaid stays required as interchange.

Keep that baseline Mermaid and its numbered hops at every rung. Deeper rungs add detail against the same hop identifiers.

Stick to flowchart/graph, sequenceDiagram, stateDiagram. Other types may show as source.

Rules:

- ASCII node ids: `[A-Za-z][A-Za-z0-9_]*`
- Labels quoted: `A["커밋"]`
- No style, classDef, click
- 그림: hops first, then ≤7 boxes (hard cap 12; over 12 means recut the slice)
- 길: sequenceDiagram, 4–6 actors, message numbers = hop IDs
- 뼈대: same sequence + alt/opt; optional second flowchart of the hidden decision
- 허점: Map의 기준 Mermaid 유지; Body의 실패/적용 범위 표
- 비교: keep the baseline Mermaid in Map; put the conditional tradeoff table in Body
- 절차: boxes are states, not commands
- 되먹임: loops, not a sequence that hides them
- Mind map only for “what exists in this field”
- Do not hand-draw structure in HTML or `image_gen`. Mermaid source plus the hop list is the map

Redraw if a hop has no box, a box has no hop, 그림 uses an unglossed term, or 허점 is a different machine.
