# Skill practices

Read this before you create a skill or change one. Each rule below was applied in this
repository and checked with live runs; the link after it is the evidence. A rule without
evidence does not belong here.

## Writing the skill

- **The description says only when to use the skill and when not to.** Write it as
  "Use when …" and "Do not use for …" sentences that name the nearby requests other
  skills own. Do not summarize what the skill does; the body says that. Every product's
  contract test checks this. ([trigger eval](../../research/2026-10-skill-trigger-eval/README.md))
- **Do not edit a description that already triggers correctly.** With every installed
  skill present, the descriptions loaded on 96/96 (Claude Code) and 192/192 (Codex)
  calls, and near-misses never loaded them. At that ceiling an edit can only make it
  worse. Measure first with the trigger eval harness. ([trigger eval](../../research/2026-10-skill-trigger-eval/README.md))
- **Say each rule once, plainly.** Current models follow a rule stated once; repeats,
  capitals, and stacked warnings add nothing. Cutting them from how-it-works and
  korean-writing-editor left behavior unchanged (how-it-works format 4/4 on opus, sonnet,
  and haiku before and after; korean meaning kept 12/12 before and after). Before you
  delete a repeat, check that another copy exists: one cut rule was the only copy.
  ([how-it-works testing](../products/how-it-works/testing.md), [korean-writing-editor testing](../products/korean-writing-editor/testing.md))
- **Gotchas come from real failures.** A `## Gotchas` section lists mistakes a run
  actually made, with the symptom and the fix. Do not add guessed ones. Examples: the
  sections in how-it-works, pre-sdd-review, and sddx, each drawn from live runs.
- **Move rarely needed detail to `references/` and point to it.** The model opens a
  reference only when the case needs it: pre-sdd-review opened `references/campaign.md`
  in its multi-plan run and in neither single-plan run, and still wrote every record
  (4/4) after the record format moved to `evidence/README.md`.
  ([pre-sdd-review testing](../products/pre-sdd-review/testing.md))
- **A declared set lives in several files.** Versions, enums, key lists, counts, and
  install lines are copied into the skill, READMEs, user guides, maintainer docs, and
  tests. Grep the name and change every copy in one commit (`AGENTS.md`).

## Measuring a change

- **Compare before and after with live runs on a pinned skill text.** Record the
  SHA-256 of `SKILL.md` and every changed reference, or a full resource manifest.
  Pin the full resource tree throughout the comparison. SKILL.md alone cannot
  distinguish a reference-only candidate: the pre-sdd-review clarification kept
  identical SKILL.md bytes while changing reviewer behavior.
  ([pre-sdd-review comparison](../../research/2026-10-pre-sdd-review-eval/README.md))
- **Write the decision rule before the runs.** Name the metric, the threshold, and what
  counts as a loss, then decide by that rule. A difference smaller than about two
  standard errors is "no measured difference" and changes nothing.
  ([routing pre-registration](../../research/2026-09-waygent-eval/routing-preregistration.md))
- **At the ceiling, improve cost, not quality.** When the baseline already scores near
  100%, a run cannot show a quality gain, and "no loss" there cannot catch a small
  quality drop. Say so in the record.
- **Read what actually ran from the transcript.** The model and effort in config files
  are not always what runs. Claude Code: `message.model` and `effort` in the session and
  `subagents/` transcripts. Codex: the rollout's `turn_context`
  (`skills/sddx/scripts/observed_model.py`).
- **Count each message's usage once.** Claude transcripts log one usage per content
  block of the same message; take the largest per message id, or cost is undercounted.
- **Check the scorer before trusting a single failure.** A test that writes to stderr
  broke `unittest -v` line parsing and showed as a failure that never happened. Run
  hidden tests with `unittest -b`, and treat a missing result as missing, not failed.
  ([waygent results, section 14](../../research/2026-09-waygent-eval/results.md))

## Host facts that shape a skill

- **Claude Code's Agent tool picks a model but not an effort.** To run a subagent at a
  set effort, ship an agent definition (`model`, `effort` in its frontmatter) and
  dispatch it by `subagent_type` with no `model`; a per-dispatch model overrides the
  definition. A skill cannot define agents, so the definition is a file in the skill's
  `agents/` folder that users link into `~/.claude/agents/`. A symlinked definition
  loads, and its effort is honored (probed 2026-10-07). Example: waygent's
  `agents/waygent-final-reviewer.md`.
- **In waygent's loop, opus at xhigh is a cheaper final reviewer than fable** with the
  same results on the app2 task; per-task reviewers at higher effort did not help.
  ([waygent results, section 14](../../research/2026-09-waygent-eval/results.md))
- Host isolation for live runs is in `AGENTS.md` and `CLAUDE.md`.

## Keeping this page useful

Add a rule only with a link to the run that showed it. When a later run contradicts a
rule, change or delete the rule in the same commit that records the run. Keep each rule
to what an agent must do differently; the numbers stay in the linked record.
