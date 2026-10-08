# Why did three workflow skills leave the tree?

Decision date: 2026-10-09. Recorded on: 2026-10-09.
Related work: pre-sdd-review, sddx, waygent.
Outcome: removal confirmed; personal reasons remain unknown in reviewed sources.
Evidence basis: deletion and registry commits plus retained research. The original
deletion conversation was not reviewed. This case is closed as a factual record
with an explicit gap, not as a complete explanation of intent.

## Starting problem

Unknown. The [removal commit](https://github.com/beyondwin/skills/commit/c5a0251fe4ab9b2e052b410c70594d70e2d0f0fa)
states the action and affected scope, but does not explain what problem motivated
removing the three skills. A joint commit does not prove a shared reason.

## Conditions

The three products existed immediately before removal. The repository separately
held research about waygent and pre-sdd-review. Those experiments describe specific
tasks and conditions; they cannot substitute for the user's retirement decision.
No inference about dissatisfaction, maintenance burden, or replacement is recorded
as an established personal reason.

## Alternatives and choice

Known choice: remove all three skill payloads, their product tests, and their
maintainer docs from the current tree, retaining their Git history.
Alternatives actually considered, the decision maker's rationale, and any intended
replacement are unknown from the reviewed commits.

## Implementation approach

The removal was followed by a [registry and documentation correction](https://github.com/beyondwin/skills/commit/9974e73f5cd84bbadd566c134f75550a2cad30bc),
which aligned product lists, checks, and install guides with the remaining products.
For source recovery, the following files exist at the full pre-removal revision:

- [pre-sdd-review payload](https://github.com/beyondwin/skills/blob/7ebdf1af53fdbee4e0628d250e6778102dbc8691/skills/pre-sdd-review/SKILL.md)
- [sddx payload](https://github.com/beyondwin/skills/blob/7ebdf1af53fdbee4e0628d250e6778102dbc8691/skills/sddx/SKILL.md)
- [waygent payload](https://github.com/beyondwin/skills/blob/7ebdf1af53fdbee4e0628d250e6778102dbc8691/skills/waygent/SKILL.md)

These are historical citations, not installation or restoration instructions.

## Observed result

The removal diff and following registry revision establish what left the tree.
The retained [pre-sdd-review report](../../research/2026-10-pre-sdd-review-eval/README.md#decision)
explicitly says its experiment does not justify deleting the skill. It found no
added discoveries on the tested small plans and described traceability benefits
and unmeasured larger cases. Treating this as proof of the user's deletion motive
would overstate both the experiment and the historical record.

The [waygent record](2026-09-27-light-implementation-workflow.md) likewise preserves
specific benefits, costs, and rejected changes. Neither record demonstrates that
all three products failed or became universally unnecessary.
No runtime or quality test was run for this historical reconstruction.

## Disposition

Retired from this repository. Research and Git history remain useful evidence;
there is no supported alias or compatibility shim. An intended replacement and
conditions for reconsideration are unknown. If the user later supplies a reason,
append a dated recollection with its source and specify whether it applies to one
product or all three. Keep the distinction from evidence recorded at deletion time.

## Reusable lesson

Inferred now: preserve the retirement decision separately from nearby performance
studies. Record the reason before removing the product's working documentation;
leave unknowns explicit when reconstructing older work. See
[the insight](../insights.md#retirement-and-experimental-results-are-different-claims).
