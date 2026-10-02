# Routing cells: decision rules (written 2026-10-02, before the batch)

Task: app2 (12 hidden tests, 7 of them traps), Claude Code 2.1.284, orchestrator `opus` at the
session default (medium, no `--effort`). Every cell uses a frozen copy of waygent 0.3.2 that
differs from `waygent-0.3.2-base` only in the Models section, plus one `--agents` definition
that carries the model and effort (a one-line neutral prompt, no tools field). The pilot
(tag `route-pilot`, one run per cell) confirmed in the host transcripts that each named role
ran on the intended model and effort, and that the base final reviewer (Fable, no effort
named) runs at **high**, not medium.

| Cell | Change | n (pilot + batch) |
| --- | --- | --- |
| base | none: Fable/high final reviewer, opus/medium everywhere else | 0 + 6 (the pilot base run is excluded: an implementer hit a 429 mid-final and was replaced) |
| final-xhigh | final reviewer opus/xhigh | 1 + 5 |
| review-high | per-task reviewers opus/high | 1 + 3 |
| impl-sonnet | implementers and fixes sonnet-5-5/high | 1 + 3 |

Jobs run four at a time with one run of each cell per wave, so a change in billing or cache
lifetime during the batch lands on every cell alike.

app2 is near saturation (one trap miss in ten 0.3.0 runs), so these runs can catch a gross
quality loss and measure cost; they cannot rank reviewer quality. Rules:

- **final-xhigh replaces Fable** if mean final-review cost drops by more than twice its
  standard error, no run scores below 12/12 hidden or 7/7 traps, and the valid High/Medium
  final findings per run (read from progress.md and reviews/final.md) are not lower than the
  base range. Otherwise the Fable rule stays.
- **review-high** is adopted only if per-task reviews raise more valid High/Medium findings
  per run than base beyond the run-to-run range, with no hidden or trap loss; a cost rise
  alone is not a reason either way.
- **impl-sonnet** is adopted only if no hidden or trap loss, implementer turns per task stay
  within 2x of base (the v26 failure was 211 vs 66 turns), and cost per run drops.
- Anything inside the noise is reported as "no measured difference" and changes nothing.
