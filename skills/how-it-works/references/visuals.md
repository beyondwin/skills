# Visuals

Default: mermaid inside the published page, in `<pre class="mermaid">` blocks. Artifacts draw it. The hop list must still read on its own — a terminal prints the diagram as source.

Stick to flowchart/graph, sequenceDiagram, stateDiagram. Other types may show as source.

Rules:

- ASCII node ids: `[A-Za-z][A-Za-z0-9_]*`
- Labels quoted: `A["커밋"]`
- No style, classDef, click
- 그림: ≤7 boxes (hard cap 12; over 12 means recut the slice)
- 길: sequenceDiagram, 4–6 actors, message numbers = hop IDs
- 뼈대: same sequence + alt/opt; optional second flowchart of the hidden decision
- 허점: table, not a prettier 그림
- 비교: table is the picture; mermaid is the choice path
- 절차: boxes are states, not commands
- 되먹임: loops, not a sequence that hides them
- Mind map only for “what exists in this field”
- The page's HTML is frame only: no boxes hand-drawn in `<div>`, no image_gen for structure. Mermaid draws every map

Redraw if a hop has no box, a box has no hop, 그림 uses an unglossed term, or 허점 is a different machine.
