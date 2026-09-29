# Results

The task, conditions, and scoring are in [Method](method.md). Numbers were extracted from the JSON
in [`results/`](results/) with [`harness/summarize.py`](harness/summarize.py).

## At a glance

64 hidden tests = the original 60 + 4 added after blind scoring. The "re-create defect" is the one
of those 4 that split the conditions most. Re-creating a deleted prompt under the same id resets
its version to 1, so a stale form silently overwrites the new prompt (violates design section 4).

| Condition | Model | n | Hidden 64 | Avoided re-create defect | Cost | Time | Subagents | Max main context |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| Plain | opus | 3 | 63/63/63 | 0/3 | $1.44 | 6.5 min | 0 | 69k |
| waygent_fo (final review only) | opus | 3 | 63/64/64 | 2/3 | $4.02 | 17.5 min | 12 | 55k |
| waygent (wording B) | opus | 3 | 64/63/64 | 2/3 | $7.50 | 33.6 min | 22 | 86k |
| waygent rev2 (wording C) | opus | 2 | 64/58 | 2/2 | $7.23 | 29.2 min | 22 | 88k |
| superpowers SDD | opus | 2 | 64/64 | 2/2 | $15.38 | 87.4 min | 25 | 151k |
| Coexist (superpowers + waygent, wording C) | opus | 1 | 64 | 1/1 | $7.39 | 33.0 min | 22 | 89k |
| Plain | fable | 1 | 63 | 0/1 | $4.08 | 9.2 min | 0 | 78k |
| waygent (wording B) | fable | 1 | 64 | 1/1 | $25.95 | 58.2 min | 23 | 105k |
| Plain | Cursor grok-4.7-high | 1 | 63 | 1/1 | tokens only | 48.5 min | 3 | - |
| waygent (wording B) | Cursor grok-4.7-high | 2 | 63/64 | 1/2 | tokens only | 290.9 min | 29 | - |

- Costs are converted at API prices. No run committed to `main`.
- Main context is the max tokens (input + cache) sent in one main-session call.
- Cursor reports no dollars and does not split subagent usage from the main agent.
- The skill wording changed during measurement, so waygent runs got different wordings (checked
  by the sha256 of the SKILL.md copied into each run repo). B: the rule "hand findings that change
  a plan signature to the user" (`d57a799b`; waygent opus 3 runs, fable, grok 2 runs). C: "first
  the smallest fix that keeps the plan; dismiss only after reproducing" (`260f7b2d`; rev2 2 runs,
  coexist). D: C + "async stays async" (`40163be6`; waygent kill-and-resume). waygent_fo is B with
  step 4 removed. The current installed file (`6b8ef448`) is D plus "the final review also checks
  remaining behavior defects" and was not measured as is.
- Plain opus run 1 and superpowers run 1 were pilots, with the same task and scoring as the main
  measurement. The waygent pilot (early skill wording) is left out of the table (64 of 64, $7.17).

## 1. Quality: almost every hidden test passed

Almost every run passed the original 60 hidden tests. Plain Claude Code (opus) scored 60/60 on all
3 runs, even after the task was enlarged once (36/36 on v1 too). When the plan and design doc are
written this fully and the code fits in one context, the model gets nearly everything right on its
own. This points the same way as the user's feeling from the v26/v27 comparison that "the outputs
were not very different".

The one exception is waygent rev2 run 2 (58/64). A Task 5 review said "the second call must raise
`Busy` immediately", and the fix turned the coroutine the plan fixed as `await ws.run_batch(...)`
into "a plain method that returns a Task". Awaiting it inside a coroutine works, but
`asyncio.run(ws.run_batch(...))` breaks. This is a post-review fix changing the plan's call shape.
The pilot had the same kind of thing (an extra argument on `save`). So the skill got "first look for
the smallest fix that keeps the names and signatures the plan fixed (async stays async)". That last
part, "(async stays async)", was added after measurement and has not been measured.

## 2. What split the conditions: one hidden defect

Four blind-scorer findings that the design doc clearly requires and the plan's API can reproduce
were turned into hidden tests: the re-create defect, a rejection arriving after a pause counted as
a rejection, a deleted marker left after re-creation, and a workspace busy forever when cancelled
before it starts. Of these, the re-create defect split the conditions. Each of the other three was
missed by only one or two runs (superpowers resume, grok plain).

| Approach | Avoided re-create defect |
| --- | --- |
| One session implements alone (plain opus 3 runs, plain fable 1 run, plain kill-and-resume 1 run) | 0/5 |
| Fresh implementer + review per Task (all waygent variants in Claude Code, superpowers, coexist) | 11/14 |
| Cursor grok plain (used 3 subagents on its own) | 1/1 |
| Cursor grok waygent | 1/2 |

The progress files of the first 6 waygent opus runs (3 with per-Task review, 3 with final review
only) show that the review found this defect in all 6. What decided the outcome was the main agent's
(controller's) judgment.

- Runs that fixed it chose the small fix of continuing the version on re-create after delete (first
  create is 1).
- 2 runs that did not fix it handed it to the user because of the early rule "hand findings that
  change a plan signature to the user". rev2, which changed this rule to "first look for the smallest
  fix that keeps the plan", fixed it 2/2.
- 1 run that did not fix it had the main agent dismiss the finding ("same body, so nothing is lost").
  So "dismiss High and Medium findings only after running the repro code" was added.

## 3. Per-Task review did not pay off at this scale

The only difference between waygent and waygent_fo is the per-Task review.

| | waygent (review per Task) | waygent_fo (final review only) |
| --- | ---: | ---: |
| Hidden 64 | 64/63/64 | 63/64/64 |
| Avoided re-create defect | 2/3 | 2/3 |
| Cost | $7.50 | $4.02 |
| Time | 33.6 min | 17.5 min |
| Subagents | 22 | 12 |
| Max main context | 86k | 55k |

Without per-Task review, quality was the same and cost and time roughly halved. When the final
review is told to also check behavior defects (mid-flight cancel, stale state, partial failure,
races), one final review caught the same defects at this scale. But this task cannot measure a scale
like the user's v26, with 16 Tasks and a UI, where one final reviewer cannot read the whole change.
So the skill default stays at the "review per Task" the user asked for, skipping only Tasks with no
behavior (docs, config, renames). Deleting step 4 of SKILL.md makes it nearly the same as waygent_fo
(waygent_fo was cut from wording B, before the fix-rule change, so the `note for user:` in fo run 1
comes from that early rule).

## 4. Main context

The "main agent uses little context" the user wanted showed up only in the final-review-only
variant.

- waygent_fo 55k < plain 69k < waygent 86k < superpowers 151k.
- waygent grew past plain because it receives both an implementer report and a review report per
  Task.
- On this task even the plain session finishes within 70k tokens (the window is 1M). Saving
  context matters only for large work that one session cannot hold in one context, and this task
  cannot show it.

## 5. Cost and time

- waygent (opus) cost 5.2x plain and took 5.2x the time. That is half of superpowers' cost and 38% of
  its time.
- waygent_fo cost 2.8x plain and took 2.7x the time.
- superpowers SDD cost 10.7x plain and took 13.4x the time. It ran an implementer, review, and
  re-review per Task and also called `finishing-a-development-branch`.
- fable was expensive: plain fable $4.08 (2.8x opus), waygent fable $25.95 (3.5x opus). Hidden tests
  were the same as opus.

## 6. Kill and resume

The session was force-killed the moment Task 3 was committed and restarted in a new session with
"이어서 해줘" ("continue").

| Condition | Killed at | Tasks redone | Result | Resumed session cost |
| --- | --- | --- | --- | ---: |
| waygent (wording D) | Right after Task 3 commit, before review | 0 | 64/64. Found Task 3 through the progress file and trailer, and resumed from the missing review | $5.42 |
| Plain | Right after Task 3 commit | 0 | 63/64. Read git history and continued from Task 4 | $0.86 |
| superpowers | Right after Task 3 commit | 0 | 62/64 (re-create defect, rejection after pause). Continued from Task 4 | $11.60 |

The killed sessions' cost could not be counted because they have no result line. At this scale even
plain resumed from git history alone without duplicate work. waygent's only difference is that it
picked up the step (review) the kill had skipped.

## 7. Installed alongside superpowers

The superpowers plugin (with session-start hook) and waygent were installed together and invoked
with `/waygent`. waygent drove from start to finish, and no superpowers skill was ever called. The
result was 64/64, $7.39, the same as waygent alone.

## 8. Cursor Agent (grok-4.7-high)

Cursor Agent also read the project skill (`.cursor/skills/waygent`) and started subagents with the
`Task` tool. With no subagent model given, the subagents used the same `grok-4.7-high` as the main
agent.

- It was slow. One subagent took 5-10 minutes, so even plain took 48.5 minutes and waygent averaged
  290.9 minutes (close to 5 hours).
- Both runs hit the 2.5-hour turn limit, and the driver sent "계속 진행해" ("keep going") in the same
  conversation. These are not clean single runs.
- Run 1 hit the limit on its second turn too and was cut off during the Task 10 review. All 10 Tasks
  were committed, but the final review never ran and the re-create defect remained (63/64).
- Run 2 finished the final review and scored 64/64. The final review fixed 2 High findings.
- It followed the skill rules (progress file, trailers, review per Task, no re-review, no commit to
  main) the same way as in Claude Code. The slowness is on the model and host side.

## 9. About blind scoring

GPT-5.6 Sol High listed defects for each output, but raw counts are not used. Of 43 findings on the
first 11 outputs, 19 pointed at code I prebuilt for the task (event log, fake model, concurrency
helper, existing `create`). Only findings the design doc clearly requires and the plan's API can
reproduce were turned into tests. The design-doc sentence "paused items must also emit progress
events" reads two ways, so it was not turned into a test.

## 10. Task defects

- The task's initial commit included `__pycache__`. Running tests changed the .pyc files, so some
  runs looked like they had "leftover changes", but all leftover changes were .pyc. They were removed
  from the harness copy committed to this repo.
- The fake `save` in two hidden tests accepted only 3 arguments, unfairly failing implementations
  that added an optional keyword. After the fix, every run was rescored.

## 11. Final 0.1.0 wording and Codex (added 2026-09-27)

After adding the review model, record location, and Codex support, runs were repeated. Wording E is
`.waygent/`, one tier up only for the final review and retries, and the first Codex rules. Wording F
is E plus "on Codex, inherit the model instead of naming it; subagents do not start subagents".
Codex was `codex-cli 0.154.0`, `gpt-5.6-sol`, `reasoning_effort=high`, with an isolated HOME (only
the auth file copied). `codex exec` does not load an explicit-invocation-only skill via `$waygent`,
so `agents/openai.yaml` was removed from the measurement copy only. Numbers are in
[results/v2.json](results/v2.json).

| Run | Wording | Hidden 64 | Re-create defect | Time | Cost / tokens | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| waygent opus | E | 64 | Fixed | 44.5 min | $10.82 | Final reviewer ran on fable. 13 record files left in `.waygent/`, not tracked by git |
| Plain Codex | — | 63 | Remained | 9.7 min | 1.24M input (1.19M cached), 27k output | |
| waygent Codex 1 | E | 63 | Remained | 85.5 min | Main 4.11M input, 17k output | The coordinator described itself as `gpt-6-astra / xhigh` and started all 22 children on that model (the real session was sol high). The final reviewer was `ultra`, and that reviewer started children of its own. The Task 2 review found the defect as High, but the coordinator deferred it with `note for user:`. At 38 minutes the turn was cut off with "model is at capacity" and the driver continued it |
| waygent Codex 2 | F | 62 | Fixed | 79.4 min | Main 3.49M input, 19k output | All 22 children inherited sol high. No grandchildren. The final reviewer was given `high`, so it did not go up a tier. 2 cancel-before-start tests failed |

- In Claude Code, one tier up for the final review worked as worded. Cost was above wording B's opus
  average of $7.50, but with 1 run it cannot be attributed to the final review.
- The Codex coordinator does not know its own model and effort. So the Codex rule was changed to
  "inherit the model instead of naming it" (F), and one tier up is written as the fixed value
  `reasoning_effort: "xhigh"`. This last wording was not measured live; an isolated check only
  confirmed that giving just an effort applies that effort to the same model.
- Codex tokens count only the main session. `codex exec --json` does not report children's usage.
- On Codex too, the fresh per-Task implementer and review found the defect, and the coordinator's
  judgment decided whether it was fixed (the same shape as in Claude Code).

## 12. 0.2.0 and the multi-layer app task (added 2026-09-29)

0.2.0 added final-review blind spots (contract drift between layers, money on failure
paths, startup config and deploy order), one app check on real data, a fast check in
`guide.md`, and the no-spawn line in every brief. The 10-Task library cannot show the first
three, so a small app task was added: `harness/fixture-app` (server, client, mock, TOML
config, seed data; 3 Tasks) with `harness/hidden-app` (12 tests: 5 basic, 7 traps modeled on
the 2026-09-28 won-sec-ai defects). The traps: estimated tokens of failed attempts billed,
per-call rounding, `""` from storage leaking into a `null` contract field, the console not
sending the `X-Caller` the server now requires while the mock never checks it, and
`config/prod.toml` missing the new required key. The reference passes 12/12; a plan-literal
implementation passes its own tests and 6/12 (traps 1/7). `fixture-app2` is the same task
with the trap rules left out of the design, so they show only in code, data and config.

All runs on Claude Code 2.1.284, opus (final review fable), skill text pinned by sha256
(0.2.0 `1e26a14a`, 0.1.0 `c64911ae` in `harness/skill-variants/waygent-0.1.0`).

| Task | Condition | Runs | Hidden (of 12) | Missed | Cost each | Minutes each |
| --- | --- | --- | --- | --- | --- | --- |
| 10-Task library | waygent 0.2.0 | 1 | 64/64 of 64 | none | $11.38 | 47.5 |
| app (rules in design) | vanilla | 1 | 12 | none | $0.51 | 2.5 |
| app (rules in design) | waygent 0.1.0 | 1 | 12 | none | $4.20 | 16.8 |
| app (rules in design) | waygent 0.2.0 | 1 | 12 | none | $4.61 | 18.2 |
| app2 (rules left out) | vanilla | 2 | 11, 12 | prod config (1 run) | $0.45-0.48 | 2.0-2.2 |
| app2 (rules left out) | waygent 0.1.0 | 2 | 12, 11 | prod config (1 run) | $3.61-4.94 | 14.0-17.7 |
| app2 (rules left out) | waygent 0.2.0 | 2 | 12, 12 | none | $4.82-4.96 | 21.4-24.9 |

- With the rules written in the design, every condition caught every trap at implementation
  time; this task does not separate conditions.
- With the rules left out, the only miss was the prod config, in 1 of 2 vanilla runs and 1 of 2
  0.1.0 runs. In the 0.1.0 miss the controller saw the gap and left it as `note for user:`
  because the plan scoped Task 3 to `config/dev.toml` (the "outside the task" exit in step 5).
  Both 0.2.0 runs, and the 0.1.0 run that passed, fixed it by a ruling during Task 3, not in the
  final review. So n=2 does not attribute the difference to the new final-review wording.
- Every waygent run, 0.1.0 included, started the real server and console at least once,
  because the README gives the commands. 0.2.0 wrote the final app walk into progress in 2 of 3
  app runs. In app1 the subagents left two `usage.server` processes running; the controller
  stopped them and left an unrelated port alone.
- No subagent spawned a subagent in any 0.2.0 run; every brief carried the no-spawn line.
- Rerun with 4 more runs per condition on app2 (0.2.0 text `61367283`, which adds "a start or
  deploy gap is never outside the task" and "stop what it started"):

  | Condition | Runs | Missed | Mean cost | Mean minutes |
  | --- | --- | --- | --- | --- |
  | vanilla | 4 | estimated tokens billed (1), prod config (1) | $0.43 | 1.9 |
  | waygent 0.1.0 | 4 | none | $3.45 | 13.6 |
  | waygent 0.2.0 | 4 | none | $5.05 | 22.4 |

  Across both app2 batches (6 runs each): vanilla missed a trap in 3 of 6, 0.1.0 in 1 of 6,
  0.2.0 in 0 of 6. Both waygent versions run the per-task review; the one 0.1.0 miss came from
  the "note for user" exit that 0.2.0 closed. 0 vs 1 of 6 is too few to separate. Means of 6:
  0.1.0 $3.73 and 14.4 minutes, 0.2.0 $4.99 and 22.6 minutes (about 34% more cost, 58% more time).
- Leftover processes: after the rerun, `usage.server` processes were still running from two
  0.2.0 runs and two vanilla runs. In the 0.2.0 runs a Task 2 implementer and a Task 3 reviewer
  started them, not the final app check, so the rule was widened to every subagent.
- Time and cost: 0.2.0 took 8% longer than 0.1.0 on app (1 run each) and about 46% longer on
  app2 (mean of 2), at about 10-15% more cost.

## 13. 0.3.0 (added 2026-09-30)

0.3.0 came from a three-model review of 0.2.0 (Fable: control flow, Opus: the 0.2.0 run
logs, Sonnet: consistency across docs). The changes: `progress.md` records who did each step
(`impl=` and `reviewer=` as `model/effort`); a ruling cannot cancel a High or Medium without
running its reproduction; a task with its commit but no `done` line resumes at its review;
Lows are not fixed in the final batch; implementers start the app only when their task
changes how it starts.

Claude Code 2.1.284, opus (final review fable). Text A is SKILL.md sha256 `ba2adb39`. Text B
(`89299286`) adds one rule after run A2: a finding that only disputes a recorded ruling
changes no code.

| Task | Text | Runs | Hidden | Missed | Mean cost | Mean minutes |
| --- | --- | --- | --- | --- | --- | --- |
| app2 | A | 4 | 12, 11, 12, 12 | estimated tokens billed (1) | $4.12 | 17.0 |
| app2 | B | 4 | 12, 12, 12, 12 | none | $3.99 | 16.4 |
| app2 | 0.2.0 (section 12) | 6 | all 12 | none | $4.99 | 22.6 |
| library | A | 1 | 63/64 | one edge test | $11.73 | 48.0 |
| library, killed after Task 3 | A | 1 | 64/64 | none | $8.34 and more | 39 |

- The one app2 miss (A2) came from the final review. Task 3 had passed all 12. The final
  reviewer questioned the recorded billing ruling ("confirm with billing") and the
  controller changed the code, which no one reviewed again. Text B keeps the ruling in that
  case; in B1 the controller wrote the same question as `note for user:` and left the code alone.
- Resume: the kill came right after the Task 3 commit, before its review. The new session
  wrote "no review found -> step 4", ran the review, and fixed 2 Mediums. A session limit
  then cut off the final review three times; one manual resume of the same session finished
  it. The first session's cost was not reported, so the cost is a lower bound.
- The library run A hit a session limit during a Task 8 fix, wrote `paused: limit`, and
  picked up again.
- Every task and final line recorded `impl=opus/inherit` and `reviewer=opus/inherit`, or
  `reviewer=fable/inherit` on the final line. Low lines used the fixed format.
- App starts by subagents did not drop (a mean of 8.5 per app2 run in 0.2.0, 8.4 in 0.3.0).
  The per-task rule allows starts in Task 3, which changes startup.
- Leftover processes: none after any run. In B4 the final reviewer left a server running
  and the controller stopped it.
- Against 0.2.0 on app2, mean cost fell about 19% and time about 26% (8 runs vs 6). Which
  change caused it was not measured.
- Not measured on 0.3.0: Codex, Cursor Agent, Grok Build.

## Cost totals

- Measurement (Claude Code): $147.41. Main measurement $124.94, reruns after the rule fix $14.46,
  waygent pilot $7.17, v1 pilot $0.84. The killed sessions in the 3 kill-and-resume runs could not be
  counted and are excluded.
- Design analysis: $3.40 for the two Claude models. Grok and GPT-5.6 Sol report tokens only.
- Section 11 extra measurement: Claude Code $10.82 (1 opus run). The 3 Codex runs report tokens only.
- Section 12 (2026-09-29): Claude Code $39.95 (library 1 run $11.38; app 3 runs $9.32; app2 6
  runs $19.25); rerun 12 runs $35.70; effort-inheritance probes about $1.
- Section 13 (2026-09-30): Claude Code about $52.5 (app2 8 runs $32.45; library 2 runs $20.07,
  with the killed session not counted).
- Cursor runs and blind scoring (codex, 22 outputs) are not reported in dollars.
- Same-day isolated gstack rerun from the previous comparison: agent $52.17, simulated user $4.36,
  scoring $1.30.
