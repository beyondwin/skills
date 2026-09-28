# Method

## 1. Gathering design evidence

The design started from three sources.

- [Agent workflow comparison](../2026-09-agent-workflow-comparison/README.md): 30 measured runs of
  9 tools and plain Claude Code on 3 tasks.
- The user's own v26/v27 comparison: the same 16-Task plan implemented with superpowers SDD (v26)
  and with the main agent calling implementers directly (v27). v27 was 16% faster and 37% cheaper.
  But 5 of the 7 high-severity defects the v26 review caught were still in v27, all of the
  state/async kind. Only the final full review caught cross-Task problems. The stretch that
  switched to a cheaper model ended up costing more.
- The source code of the tools studied.

## 2. Four independent designs from four models

Four models got the same evidence pack (the two studies above plus the user's requirements) and
the tool source paths, and each wrote a design without seeing the others. The designs were used
only as design input, not as evidence. The evidence is the measurement below.

| Model | Run | Usage |
| --- | --- | --- |
| Claude Opus 5.5 | `claude -p --model opus` | $0.61 |
| Claude Fable 5.1 | `claude -p --model fable` | $2.79 |
| Grok 4.7 High | `cursor-agent -p --model grok-4.7-high` | 115k input, 14k output tokens |
| GPT-5.6 Sol High | `codex exec -m gpt-5.6-sol -c model_reasoning_effort=high` | 74k tokens |

All four agreed on these points.

- Start a fresh implementer for each Task, and give it only a short brief and one shared guide.
- Pin the model. On a rate limit, stop; do not switch to a cheaper model.
- No re-review loop. Prove each fix with a failing test.
- Do one full review at the end.
- Resume by reconciling the progress file with git history.
- Turn on only by explicit invocation.

They split on whether to review every Task or only state/async Tasks. That question was measured
separately with the variant `waygent_fo` (no per-Task review, final review only). The original
designs are in [analysis/](analysis/).

## 3. Task

The task is a 10-Task plan on a small Python domain layer (`promptops`). It uses only the standard
library, and the model is a fake (`FakeModel`), so results are deterministic.

- Existing code: a store, the fake model, a shared concurrency helper, a retry helper, an event
  log, and exception base classes. The conventions new code must follow are written only in the
  existing code and the design doc.
- The plan (`docs/plan.md`) fixes only Task order, files, names, and signatures. For behavior it
  says only "follow the design doc".
- The design doc (`docs/design.md`, about 110 lines) describes in prose the operator's flow,
  conflicts, model calls, events, undo, and errors. The principles to keep are in sentences, not
  in a list.
- Tasks 1-10: store versions, edit sessions, batch apply, pause and locks, workspace and target
  pinning, candidate selection, retrying transient failures (on every model call), progress
  events, undo, workspace undo.

### Hidden tests

Scoring uses 60 tests the agent cannot see. 19 basic tests check the plan's sentences literally;
41 edge tests check behavior the design doc states only as principles. Defects of the same kinds
the v26 review caught at high severity were planted on purpose (stale form after a refresh, save
after a mid-flight cancel, mixed-up targets, partial failure, a lock that never releases). The
reference implementation was confirmed to pass all 60. After blind scoring, 4 more were added for
64 (`hidden/test_x.py`). The reference implementation had one of those defects too (the
re-create defect) and was fixed.

### Why the task was enlarged once

On the first task (v1: 6 Tasks, 7 principles listed in the plan, 36 hidden tests), plain Claude
Code passed all 36 in 3.7 minutes for $0.84. So when every principle is written in the plan, no
harness is needed. The task was enlarged once, toward the v26 conditions: the principles moved into
design-doc prose, existing-code conventions were added, and Tasks went up to 10. It was decided in
advance not to enlarge it again if plain Claude Code scored full marks again (to avoid bending the
task to manufacture a difference).

### Defect scoring (blind)

Defects the hidden tests cannot see were counted too. The final code was renamed to `tree-NN`
with no condition name and given to a non-Claude model (GPT-5.6 Sol High, read-only), which listed
behavior that departs from the design doc, with severity, location, and repro code of 5 lines or
fewer. That model only finds defects. Findings the design doc clearly requires and the plan's API
can reproduce were turned into extra hidden tests, and every output was rescored against the
same bar. Ambiguous findings were marked separately.

## 4. Conditions

| Condition | First message | Installed |
| --- | --- | --- |
| Plain | `docs/plan.md 계획대로 모든 Task를 구현해줘.` ("Implement every Task per the docs/plan.md plan.") | Nothing |
| superpowers | `superpowers:subagent-driven-development 로 docs/plan.md 계획을 끝까지 실행해줘.` ("Run the docs/plan.md plan to the end with superpowers:subagent-driven-development.") | superpowers 6.4.1 plugin (with session-start hook) |
| waygent | `/waygent docs/plan.md` | Project skill `.claude/skills/waygent` (Cursor: `.cursor/skills/waygent`) |
| waygent_fo | `/waygent docs/plan.md` | Measurement-only variant. Wording B (before the fix-rule change) with only the per-Task review step removed. `harness/skill-variants/` |
| Coexist | `/waygent docs/plan.md` | superpowers plugin and waygent installed together |

Every first message ended with "나는 자리를 비우니 중간에 묻지 말고 끝까지 진행해." ("I'll be
away, so don't ask anything midway; carry on to the end."). The point is to see whether the agent
finishes with no human present. If the agent stops before finishing the plan, "계속 진행해"
("keep going") is sent at most 3 times.

Hosts and models:

- Claude Code 2.1.280, models `opus` (Opus 5.5) and `fable` (Fable 5.1).
- Cursor Agent 2026.09.23, model `grok-4.7-high`. superpowers was measured only in Claude Code.
- Codex CLI 0.154.0, model `gpt-5.6-sol`, `reasoning_effort=high`. Only plain and waygent were
  measured ([results, section 11](results.md)).

## 5. Isolation

In the previous comparison, gstack shared a state folder across tasks and the records got mixed.
This time each run creates fresh:

- One run folder (`runs/<tag>/<condition>-<model>-<run>/`) holding the repo copy, git history, and
  tool state.
- Claude Code: `--setting-sources project`, `--strict-mcp-config`, `--disallowedTools AskUserQuestion`.
  No user settings, other plugins, or account connectors come in.
- waygent state (`.git/waygent/`, `.waygent/` in later wordings) lives only inside that run's repo.
- Codex: a fresh HOME and `CODEX_HOME` per run, with only the auth file copied. No user
  skills, plugins, or MCP servers come in. The skill sits in that HOME's `.agents/skills/waygent`.
- Hidden tests run only on a copy, after the run ends.

The previous comparison's gstack S1-S3 were rerun the same way, each run with its own state folder
(`GSTACK_HOME`). The results were corrected in the
[previous comparison's results](../2026-09-agent-workflow-comparison/results.md).

## 6. What was measured

- Hidden tests passed (basic/edge), blind defect count.
- Cost: the session's last `total_cost_usd` (for a resumed session it is cumulative, so summing
  turns inflates it). Only distinct sessions were summed. Cursor gives no dollars, so only tokens
  were recorded.
- Elapsed time, subagent count, brief length.
- Main context: the max and last value of input + cache read + cache write tokens per main-session
  call. Subagent calls are split out by `parent_tool_use_id` and counted separately. Per-message
  output tokens arrive cut into blocks in the stream and are unreliable, so output totals use
  `modelUsage`.
- git: whether it committed to `main`, commit count on the work branch, leftover changes.
- Resume: waygent, plain, and superpowers were force-killed the moment Task 3 was committed and
  restarted in a new session with "이어서 해줘" ("continue"). Checked whether finished Tasks were
  redone and whether the result was correct.

## 7. Limits

- The task is small. All the code fits easily in one context. Any benefit of saving main context
  can appear only on work that does not fit in one context, and this task cannot show it.
- 1-3 runs per condition. Only differences of several-fold or more are treated as meaningful.
- The model is fake, so real model calls, UI, and deployment were not measured.
- The defect scorer is a single model. I filtered its findings against the design doc before
  turning them into tests. About half the raw findings pointed at code I prebuilt for the task, so
  counts are not used.
- The Cursor grok runs hit the turn limit (2.5 hours) and the driver continued them.
- The skill wording was changed twice after measurement. The first change (fix rule) was
  remeasured (rev2); the second ("async stays async", final review also checks behavior defects)
  was not.
