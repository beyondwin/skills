# Visuals

Default: a fenced Mermaid block in the chat Markdown, plus a numbered hop list that still reads when the diagram is shown as source. No host-specific drawing tool is required. HTML boxes are not substitutes for Mermaid.

At 그림, the numbered hops are the human map. Put them before the mermaid fence in Map. Mermaid stays required as interchange.

Keep that baseline Mermaid and its numbered hops at every rung. `output.md` owns the hop id rules: deeper rungs may redraw the diagram type but keep the 그림 H ids.

Stick to flowchart/graph, sequenceDiagram, stateDiagram. Other types may show as source.

Rules:

- ASCII node ids: `[A-Za-z][A-Za-z0-9_]*`
- Labels quoted: `A["커밋"]`
- No style, classDef, click
- 그림: hops first, then 4–6 boxes, one per hop; more than 6 means recut the slice
- 길: sequenceDiagram, 4–6 actors; each message label starts with its hop id (`H1: …`)
- 뼈대: same sequence + alt/opt, a branch reusing its parent hop id (`H3a`); optional second flowchart of the hidden decision
- 허점: keep the baseline Mermaid in Map; put the failure/regime table in Body
- 비교: keep the baseline Mermaid in Map; put the conditional tradeoff table in Body
- 절차: boxes are states, not commands
- 되먹임: loops, not a sequence that hides them
- Mind map only for “what exists in this field”
- Do not hand-draw structure in HTML or `image_gen`. Mermaid source plus the hop list is the map

Redraw if a hop has no box, a box has no hop, 그림 uses an unglossed term, or 허점 is a different machine.
