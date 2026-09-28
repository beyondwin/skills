# Model routing and record location

The user asked three questions. Should the reviewer model be better than the implementer
model? Should implementer effort change with task difficulty? Should records live in a
top-level `.waygent/`? On 2026-09-27 we re-read the sources of the 9 harnesses we studied
(same versions and commits as in [Tools](../2026-09-agent-workflow-comparison/tools.md)) and
checked them against this evaluation.

## Model routing by harness

| Harness | Orchestrator | Implementer | Reviewer | Source |
| --- | --- | --- | --- | --- |
| superpowers | Session | Lowest tier that fits the difficulty. 1-2 files with a complete spec get a cheap model, multi-file work gets standard, design judgment gets the top tier. Reviewers and implementers of prose plans have a mid-tier floor | Task review matches the diff's size and risk. Final review uses the top tier. Fix rounds 4-5 go one tier up | `skills/subagent-driven-development/SKILL.md` "Model Selection" |
| dryforge | Session | Session | Session | `go/references/orchestration.md` BLOCKED ladder: add context → stronger model → user |
| BMAD | Session | Subagent. Config can switch it to another model or an external tool | States "same capability as the session" | `bmad-build/step-04-review.md`, `customize.toml` |
| gstack | Session | Session | Claude review + Codex adversarial review (`codex review`, effort high, raised with `--xhigh`) | `review/sections/adversarial.md`, `codex/SKILL.md` |
| Ralph | Opus | Parallel Sonnet for reading, one Sonnet for build and test, Opus for debugging and design | None | `files/PROMPT_build.md`, `files/loop.sh` |
| workflow-orchestrator | No rule | No rule | No rule | `workflow-orchestrator/SKILL.md` |
| mattpocock/skills | No rule | No rule | No rule. The questioning step recommends "the best model" | `docs/engineering/grill-me.md` |
| Spec Kit | No rule | No rule | None | — |
| OpenSpec | No rule | Recommends a high-capability reasoning model | None | `README.md` "Model selection" |

- superpowers and Ralph are the harnesses that move implementation down to a cheaper model.
  In the same section superpowers notes that "the cheapest model takes 2-3x the turns on
  multi-step work, so it ends up more expensive."
- No harness runs every review on a model stronger than the implementer. They either raise
  only the final review (superpowers) or add another vendor's model (gstack).

## Decisions checked against this evaluation

| Question | Decision | Evidence |
| --- | --- | --- |
| Use a better model for the reviewer | Only the final review goes one tier up | In all 6 runs where the progress log was visible, the same-model Task reviewer found the re-creation defect. The runs that missed it were ones where the orchestrator rejected or deferred the finding. The final review runs once, so its cost ceiling is clear, and only the final review catches cross-task problems (v26, and `waygent_fo` in this evaluation) |
| Vary implementer effort by difficulty | Do not lower it. Only a retry after failure goes one tier up | Claude Code picks only the model at call time; effort is set only in the agent definition file. The defect sat in a Task that looked like easy repository work, and all 7 high-severity v26 defects were state or async. In v26 the cheaper-model stretch wasted 5 hours and $128 |
| Review with another vendor's model | Not in the default | In blind grading GPT-5.6 Sol found 4 defect types the Claude conditions missed, but it was never measured as an in-loop reviewer, and it needs one more install |

On Codex, "one tier up" means writing only `reasoning_effort: "xhigh"` on the same model.
An isolated test confirmed that if `spawn_agent` leaves the model empty the child inherits the
session's model and effort, and if only effort is set the same model runs at that effort
(sol high session → child sol high, sol xhigh). In the evaluation the Codex orchestrator did
not know its own model or effort. Run 1 wrote itself down as `gpt-6-astra / xhigh` and spawned
every child with that model. Run 2 wrote itself down as "GPT-5" and gave the final reviewer
`high`. So on Codex we leave the name out and use a fixed `xhigh`.

## Record location

| Harness | Location | How it stays out of git |
| --- | --- | --- |
| superpowers | `.superpowers/sdd/<plan>/` | Writes a one-line `*` `.gitignore` inside the folder (`scripts/sdd-workspace`) |
| dryforge | `.dryforge/` | Advises the user to add it to `.gitignore` |
| gstack | `~/.gstack/projects/` | Outside the repository |
| waygent 0.1.0 draft | `.git/waygent/` | Inside the git directory |

waygent followed superpowers and moved to `.waygent/<plan-slug>/` with `.waygent/.gitignore`
(`*`). Records do not get mixed in even when an implementer runs `git add -A`, and the user's
`.gitignore` is left alone. `git clean -fdx` deletes this folder, but completion is decided from
commit trailers, so the progress file can be rebuilt.

## Not measured

This task cannot separate the effect of the one-tier-up final review, the one-tier-up retry, or
raw review files. Plain opus already got 63 of 64, so there were almost no defects left to
catch. A 16-Task-scale task is needed.
