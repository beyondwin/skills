# waygent compatibility

This document sets which hosts and OS waygent supports, and on what evidence. The
supported hosts are the four in the product registry, `claude-code`, `codex`,
`cursor`, and `grok`, for local or repository-linked use only. Support scope and measurement status
are separate. Measurements are in the record below; installed files changed after that
are `not_measured` until measured again.

- Claude Code: implementation and review run as subagents (the Agent tool).
- Codex: called with `$waygent`. Subagents run through the `spawn_agent` tool, and
  `~/.codex/config.toml` must have `[features]` `multi_agent = true`.
- Cursor Agent: a host for this product. In `sddx` it is still a worker, not a host.
  Subagents run through the `Task` tool and use the main model even when no model is given.
- Grok Build: called with `/waygent`. It reads skills from `~/.agents/skills`,
  `~/.claude/skills`, and `~/.cursor/skills`, so any of the links above works.
  Subagents run through `spawn_subagent`; with no `model` the child inherits the
  session model, and a subagent cannot spawn its own (depth limit 1).
- Claude.ai, Cowork, Skills API upload, and marketplace publication are not supported.

## Supported OS

The supported OS is macOS only. Windows and Linux are unsupported. A passing Ubuntu CI
run is not macOS support evidence.

## Discovery paths

```text
skills/waygent/              repository source
├─ ~/.claude/skills/waygent ─→ Claude Code
├─ ~/.agents/skills/waygent ─→ Codex
└─ ~/.cursor/skills/waygent ─→ Cursor Agent

skills/waygent/agents/waygent-final-reviewer.md   optional, Claude Code only
└─ ~/.claude/agents/waygent-final-reviewer.md ─→ final reviewer at opus/xhigh
```

Grok Build reads all three folders and deduplicates by skill name.

On 2026-09-27, Cursor Agent 2026.09.23 was confirmed to read both the project path
`.cursor/skills/<name>/SKILL.md` and the user path `~/.cursor/skills/<name>/SKILL.md`
(by calling a test skill).

The link block is in the product README and in [local links](../../../users/en/install-local.md).
It does not automatically replace a different link, file, or directory.

## Measurement record

Detailed tasks and numbers are in [waygent design and evaluation](../../../research/2026-09-waygent-eval/README.md).
This record is execution evidence at that point in time and does not vouch for later versions.

- Claude Code: the eval runs below ran `claude -p --setting-sources project` with no
  `--effort`, so the controller, implementers, and per-task reviewers ran at medium
  effort and the fable final reviewer at its own configured high. The 0.3.0 production
  run ran at high throughout. The cost and time numbers are medium-effort numbers, and
  their `inherit` records cannot tell the two apart.
- Claude Code: every eval dispatch returned inline (`run_in_background: false`), while
  interactive production sessions on 2.1.284 returned every dispatch in the background.
  Background mode was measured on 2026-10-02 in an interactive session driven through
  tmux: every dispatch returned "Async agent launched", and the next one went out only
  after the previous one's completion notice (2026-10-02 row). The 0.3.1 run-scoping,
  finished-folder, and final-phase resume rules were measured inline on 2026-10-01.

| Host | Version | Model | Date | waygent | Result |
| --- | --- | --- | --- | --- | --- |
| Claude Code | 2.1.280 | opus (Opus 5.5) | 2026-09-27 | 0.1.0 working copy | 5 runs completed (64/63/64 of 64 hidden tests; 64/58 after the rule fix). 1 interrupt-and-resume run 64/64. 1 run alongside superpowers 64/64 |
| Claude Code | 2.1.280 | fable (Fable 5.1) | 2026-09-27 | 0.1.0 working copy | 1 run completed (64/64), $25.95 |
| Cursor Agent | 2026.09.23 | grok-4.7-high | 2026-09-27 | 0.1.0 working copy | 2 runs. Both committed all 10 Tasks (63/64, 64/64). Run 1 was cut off by the harness turn cap before the final review. Very slow, 291 minutes on average. 0.3.x text: `not_measured` |
| Codex | 0.154.0 | gpt-5.6-sol (high) | 2026-09-27 | 0.1.0 working copy | 2 runs completed, both committed all 10 Tasks (63/64, 62/64). In run 1 the controller misidentified its own model and spawned children on a different model. In run 2, fixed to inherit the model, all 22 children used the session model. The final wording that pins one tier up to `xhigh` was not measured. Under `codex exec` an explicit-only skill is not loaded by `$waygent`, so `agents/openai.yaml` was removed from the measured copy. 0.3.x text: `not_measured` |
| Claude Code | 2.1.284 | opus (Opus 5.5), final review fable | 2026-09-29 | 0.2.0 working copy (SKILL.md sha256 `1e26a14a`…) | 1 run on the 10-Task fixture: 64/64 hidden tests, re-create defect fixed, $11.38, 47.5 minutes (v2 run: 64/64, $10.82, 44.5 minutes). All 21 briefs, reviewers included, carried the no-spawn line; no subagent spawned one. `guide.md` named the fast check and "no app to start", and the app check was skipped for that reason. Final review 0 High, 0 Medium. Review-fix commits also carried the task trailer. The app check, cross-layer drift, and startup config were not exercisable on this one-layer library. Same day, 3 runs on the 3-Task multi-layer app task (1 with the rules in the design, 2 with them left out): 12/12 each, the app walked on dev and prod configs; rerun with 4 more runs per condition on the rules-left-out variant: across 6 runs each, vanilla missed a trap in 3, 0.1.0 in 1, 0.2.0 in 0 ([results, section 12](../../../research/2026-09-waygent-eval/results.md)) |
| Claude Code | 2.1.284 | opus (Opus 5.5), final review fable | 2026-09-30 | 0.3.0 working copies (SKILL.md sha256 `ba2adb39`…, `89299286`…, shipped `58b68889`…) | 8 runs on the app2 task: 12/12 in 7, 11/12 in 1; mean $4.06, 16.7 minutes. 2 more app2 runs on the shipped text: 12/12 each, mean $3.88, 17.8 minutes. 2 runs on the 10-Task library: 63/64 ($11.73, 48 minutes) and a kill-after-Task-3 resume, 64/64, where the resumed session ran the missed Task 3 review. Every progress line recorded `impl=`/`reviewer=`. No process was left running. A 180-call decision probe removed the `89299286` rule. The 954ba4b text of 0.2.0 was never measured; these runs measure its rule as carried into 0.3.0 ([results, section 13](../../../research/2026-09-waygent-eval/results.md)) |
| Claude Code | 2.1.284 | opus (Opus 5.5) at `--effort high` throughout, final review fable | 2026-10-01 | 0.3.1 working copy (SKILL.md sha256 `496dabdb`…) against 0.3.0 (`58b68889`…). Shipped 0.3.1 (`d533a9aa`…) adds only the `Waygent-Task: final` clause of the final-phase resume and the `reviewer=none` wording, both unmeasured | 9 runs on the app2 task, $18.66 in all. Run scoping (the branch carries `Waygent-Task: 1` and `2` from an earlier run, plus a finished `.waygent/old-plan` whose start is not an ancestor; killed at the first new trailer commit), 2 runs per text: all 4 dispatched Task 1 first. The 0.3.0 controllers got there by their own rulings, and one checked `main..HEAD`, which counts the stale trailers. The 0.3.1 controllers checked `start..HEAD` as written. 0.3.0 wrote `model: opus/inherit`, 0.3.1 `model: opus`. $0.60-0.69 each. `/waygent` alone with only the finished folder, 1 run per text: 0.3.0 stopped and proposed starting `docs/plan.md` fresh ($0.19); 0.3.1 said there was nothing to resume and started nothing ($0.12). Full runs on 0.3.1: 12/12 each, $5.13 and 23.2 minutes, $6.11 and 28.5 minutes. In each, 8 dispatches ran one at a time and inline, guide.md named an `app:` line and the fast check, the final fixes carried `Waygent-Task: final`, the lines were `final: start` then `final: done … walk=ok`, and no process was left. Task 3's implementer brief ran over the ~2,000-character cap in every run (2,275-2,319). Kill after `reviews/final.md` was written, before `final: done`, then a fresh session: it resumed at the fixes (2 Medium) and wrote `final: done 9bc7b63 impl=opus reviewer=unknown fixed=2 walk=ok tests=47 OK`, 12/12, $4.51 for both sessions. The higher cost than the 0.3.0 rows comes from high rather than medium effort |
| Claude Code | 2.1.284 | opus (Opus 5.5) at `--effort high`, final review fable | 2026-10-02 | 0.3.2: measured SKILL.md sha256 `b32fc1fb`… (shipped 0.3.2 differs only in the reviewer-leftover command, `git stash push -u` instead of `git restore . && git clean -fd`; no run left a dirty tree, so neither was reached); the earlier 0.3.2 edit `bac260d3`… (before the reviewer-tree line); shipped 0.3.1 `d533a9aa`… for the resume probe | Final-phase resume with `Waygent-Task: final` commits already in `start..HEAD` and no `final: done` (a finished 0.3.1 app2 run with its last line removed), 2 runs per text: 0.3.1 (`d533a9aa`) and 0.3.0-era text (`496dabdb`) behaved the same. No run redid the fixes; each found no walk recorded, walked the app (3 by a fresh implementer, 1 by the controller), and wrote `final: done … fixed=2 walk=ok`; no new commits, $0.28-0.48 each. Full runs on the two-task `wordfreq` plan plus a docs-only Task 3, headless: `bac260d3` 3/3 tasks, 78 tests, $4.23, 20.8 minutes; `b32fc1fb` 3/3 tasks, 34 tests, $3.93, 16.8 minutes. Each wrote `task 3: done … review=skipped (docs only…) reviewer=none`, ended `final: done … walk=ok`, left a clean tree and no process; briefs ran up to 2,175 characters; in `b32fc1fb` all three reviewer asks carried "leave the tree as you found it". Interactive background mode (`bac260d3`, tmux, same plan): 8 dispatches, all async, strictly one at a time; 3/3 tasks, 59 tests, `final: done … walk=none (app: none…)`, clean tree, about $5.00 from the transcript, 19.4 minutes |
| Claude Code | 2.1.287 | opus (Opus 5.5) at the session default (medium); final review the `waygent-final-reviewer` agent (opus/xhigh) | 2026-10-07 | 0.4.0 (SKILL.md sha256 `8393c9af`…), the agent definition symlinked into the fixture's `.claude/agents/` as the install step links it | 1 app2 run: 12/12 hidden, 7/7 traps, $3.76, 16.4 minutes. The final reviewer was dispatched by `subagent_type` with no model and ran opus at xhigh (transcript); the line read `final: done … reviewer=opus/xhigh fixed=1 walk=ok`. The progress lines wrote `model: opus/high` and `impl=opus/high` while the transcripts show medium, a guessed effort against the "never guess" rule. A one-call probe the same day confirmed a symlinked agent file loads with its effort. Routing cells behind the change: [results, section 14](../../../research/2026-09-waygent-eval/results.md) |
| Grok Build | 1.0.41 | grok-4.7 (default effort xhigh) | 2026-09-28 | 0.1.0 working copy (with the Grok line) | 1 smoke run on a 2-Task plan, completed: both Tasks committed with trailers, Task 1 review found 1 issue fixed by resuming the implementer (`resume_from`), final review High/Medium none, 14 tests pass, `.waygent/` records and `.gitignore` written. 6 subagents, none named a model. 29 minutes, $0.88. Not run on the 10-Task fixture. 0.3.x text: `not_measured` |
