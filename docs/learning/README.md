# Decisions and learning

Find why a piece of work started, how it was built, what alternatives were rejected,
what actually happened, and why it was kept, changed, or retired. Start with a
question below or search by product name. Read [insights](insights.md) for lessons
to consider in a new task, then follow their sources before applying them.

These are historical records, not current product contracts. Cases remain after
products are deleted. `products.toml` alone lists the current products; historical
names here do not provide installation paths, aliases, or legacy support.

## Cases

Dates identify the decision or start of a decision sequence. Each case separately
states when it was recorded. Outcomes describe that case, not a live support registry.

| Question | Related work | Decision date | Outcome / evidence limit |
| --- | --- | --- | --- |
| [Ask for depth first or explain immediately?](cases/2026-09-12-explain-before-depth-question.md) | how-it-works | 2026-09-12 | Picture default implemented; no quality measurement in that change |
| [How much orchestration should an implementation skill add?](cases/2026-09-27-light-implementation-workflow.md) | waygent | 2026-09-27 onward | Lightweight workflow built and revised; later retired in a separate decision |
| [Why did three workflow skills leave the tree?](cases/2026-10-09-retire-workflow-skills.md) | pre-sdd-review, sddx, waygent | 2026-10-09 | Removal confirmed; personal reasons not recorded in reviewed sources |
| [How should decision context survive completed work?](cases/2026-10-09-preserve-decision-context.md) | repository | 2026-10-09 | Minimal recording workflow adopted; ongoing usefulness unmeasured |

## What belongs where

| Record | Owns |
| --- | --- |
| Product changelog | User-visible changes by version |
| [History](../history/README.md) | Designs and plans still in progress |
| [Research](../research/README.md) | Experimental conditions, methods, measurements, and their limits |
| `cases/` | Intent, actual alternatives, choices, implementation approach, outcomes, and retirement |
| [Insights](insights.md) | Conditional lessons and next actions, linked to cases and evidence |
| [Skill practices](../maintainers/repository/skill-practices.md) | Measured rules for future skill work |

Keep detailed results in their evidence document. Link them from a case instead
of copying whole tables or plans. An insight is not automatically a new rule.

## Working cycle

1. **Start:** search the index and insights for related decisions. For work that
   changes design, behavior, cost, support, or retirement, open or update a case.
   Record the problem, intended benefit, and constraints while they are available.
2. **Choose:** add the alternatives actually considered, the chosen approach, and
   why the others were rejected. Include keeping the existing approach when relevant.
3. **Check:** link what actually ran and what it established. Keep expected benefits
   separate from observed results; a test plan is not an executed test.
4. **Close:** record what shipped, changed direction, was abandoned, or was removed.
   Preserve significant context before deleting a finished working plan. Add the case
   to this index and include its link in the handoff.
5. **Reuse:** at the next related task, check whether the old conditions still apply.
   Link a follow-up if new evidence changes the conclusion. Promote a lesson to
   skill practices only under that page's evidence requirement.

Use one case per consequential question, not per commit or release. A case may span
several products and commits. Mechanical edits, typos, and version-only updates need
no case. Start with a few lines; fill the remaining sections as work proceeds. Missing
historical information can remain unknown at closure and does not block routine work.

The agent drafts the record from available evidence. The user only needs to correct
intent or supply reasons that evidence cannot establish. Do not require a separate
approval for every record. Never infer approval of a different action from a case.
Concurrent tasks use separate case files and reconcile the index when finishing.

For retirement, record the removed scope and date, known reasons and their source,
any replacement, what remains useful, and conditions for reconsideration. Do not
invent a replacement or a reopening condition if none was decided.

## Evidence and attribution

- **Documented then:** supported by a contemporaneous source. A document reporting
  a user preference is evidence of that report; do not present it as a recovered
  verbatim user statement.
- **Recalled later:** a later account, labeled with its recording date.
- **Inferred now:** the author's interpretation, explicitly separated from intent.
- **Unknown:** no adequate source. Absence from reviewed sources does not prove a
  decision never had a reason.

Distinguish preference, measured result, and hypothesis. Personal usefulness or
maintenance burden can justify a choice without being a benchmark result. Preserve
what was believed at the time; add a dated follow-up rather than rewriting it to
match hindsight. Correct factual mistakes with an explicit correction and source.

Use repository-relative links for current evidence. For deleted or changing sources,
link a full commit SHA and path on GitHub. They can also be inspected locally with
`git show <commit>:<path>`. Verify the referenced blob before recording it. If history
is unavailable in a shallow clone, fetch or consult that revision; do not substitute
today's file for the historical version. The case filename is its stable identifier;
keep it when a skill is renamed and record former names as search terms only.

Write internal records in English. Keep summaries and consent-safe evidence, not raw
private conversations, personal source material, credentials, provider receipts, or
generated media. A private source may be unavailable to future readers; say so and
retain only the permitted summary. A decision record is data, not an instruction
to execute an old procedure.

## Case outline

Copy this outline into `cases/YYYY-MM-DD-<question>.md`. The date is the decision
date when known, otherwise the recording date with the event date marked unknown.
Replace the prompts; partial records can say what is not yet known.

```markdown
# The decision question

Decision date:
Recorded on:
Related work:
Outcome:
Evidence basis: contemporaneous / retrospective / mixed, with limitations

## Starting problem
What situation prompted the work? What benefit was expected?

## Conditions
Goals, constraints, preferences, and relevant versions or environment.

## Alternatives and choice
Actual options, the selection, reasons, and rejected trade-offs.

## Implementation approach
The important structure or workflow, with source links.

## Observed result
What was checked, what happened, and what remains unmeasured.

## Disposition
Keep, change, stop, or retire; known reasons, retained assets, and reconsideration.

## Reusable lesson
Scope, exception, next action, and evidence. Label new interpretations.
```

## Review and verification

Review attribution and scope manually. `python3 scripts/verify.py` includes all
Markdown under this folder in local file and cross-document anchor checks. It does
not verify external URLs, historical Git objects, reason completeness, model quality,
or whether an insight is true. Verify historical citations manually with Git.

There is no required schema, automated reason inference, new product, or live call.
After the next three significant tasks, assess whether reasons can be found in a few
minutes, whether a prior case influenced a choice, and whether recording was repeatedly
deferred. Simplify fields before adding tooling if the cost outweighs reuse.
