# Ask for depth first or explain immediately?

Decision date: 2026-09-12. Recorded on: 2026-10-09.
Related work: how-it-works (formerly the unpublished working name graspic).
Outcome: picture default implemented in the 3.0.0 change.
Evidence basis: retrospective reconstruction from a contemporaneous approved design,
implementation commits, and changelog; no new user interview or model run.

## Starting problem

The [approved design](https://github.com/beyondwin/skills/blob/e9de3a1aed94f69d9e7018df837c2210ff375a73/docs/history/specs/2026-09-12-how-it-works-first-picture-design.md)
records that a mechanism request without an explicit explanation depth consumed a
turn asking for that depth. Its context reports user dissatisfaction with the effort
needed to invoke the skill and the resulting explanation. This is the design's account,
not a newly recovered user quotation or a measured quality comparison.

## Conditions

The choice had to preserve the skill's identity: explaining the same mechanism at
different depths, keeping the picture truthful, and respecting an explicit depth.
The approved scope excluded live quality evaluation and host-support expansion.
The terminal could show Mermaid source without rendering it, so first-screen
readability could not depend on a diagram renderer.

## Alternatives and choice

- Keep asking when depth is missing: the existing behavior, rejected for this
  bounded mechanism request because it postponed the explanation.
- Fill an absent depth with picture and announce it: selected in the design.
  Explicit depth, explicit aliases, and named jargon defaults still took precedence.
- Convert the skill into an ELI5 tool or remove required outputs: explicitly out
  of scope. Easier invocation did not authorize changing that identity.

The design retained questions for missing subjects or meaningful conflicts, and
retained narrowing for topics too broad to explain as one mechanism.

## Implementation approach

[Implementation](https://github.com/beyondwin/skills/commit/730f6785b03a114c3061cdc4817b007ba0702144)
changed the missing-depth gate and precedence. Picture output put numbered hops
before Mermaid and avoided walking the same hops again in the body. Fixtures,
contract text, references, and guides changed together. The
[version change](https://github.com/beyondwin/skills/commit/6eb353a4f3a065c77655a0cc3e6dcc843587c7b0)
recorded 3.0.0 because defaults and required-input behavior changed.

## Observed result

The [recorded changelog](https://github.com/beyondwin/skills/blob/6eb353a4f3a065c77655a0cc3e6dcc843587c7b0/skills/how-it-works/CHANGELOG.md)
confirms the one-turn picture default and the output-order change. It explicitly
leaves live model quality unmeasured and claims no tag or GitHub Release. The
design's proposed test commands are not treated here as execution receipts.
This case establishes an implemented interaction choice, not that users learned
more or that generated explanations became better.

## Disposition

The change was implemented; the working spec was subsequently deleted. Its pinned
source above preserves the reasoning without restoring the obsolete plan. For
today's behavior use the [current contract](../../maintainers/products/how-it-works/contract.md).
No historical reopening threshold was found. A proposed reason to revisit the
choice is evidence that the default repeatedly produces the wrong level of detail.

## Reusable lesson

Inferred now: for a bounded explanation with a reversible presentation choice,
announce a default and provide value in the same turn. Preserve explicit choices
and ask when the subject or consequential constraints are missing. This is a design
lesson from this case, not a measured rule for every ambiguous request. See
[the scoped insight](../insights.md#defaults-can-remove-an-unnecessary-turn).
