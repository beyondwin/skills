# Visuals

Use Mermaid source plus the numbered hop list in [Output](output.md). That reference
owns the per-rung map, box/actor counts, hop IDs, branch labels, and table placement.
HTML boxes are not substitutes for Mermaid. Rendering is optional; no host-specific
drawing tool is required.

Use flowchart/graph, sequenceDiagram, or stateDiagram. Other types may show as source.

- Use ASCII node IDs: `[A-Za-z][A-Za-z0-9_]*`.
- Quote flowchart labels: `A["커밋"]`.
- Do not add style, classDef, or click directives.
- In a procedure, boxes are states, not commands.
- Show feedback as loops rather than a sequence that hides it.
- Do not substitute `image_gen` or hand-drawn HTML for the map.

Redraw if a hop has no box, a box has no hop, 그림 uses an unglossed term,
or 허점 describes a different mechanism.
