I have what I need. Here is the design.

# waygent: evidence-based design

## 1. KEEP

- **One implementer subagent per task, sequential, short inline brief.** Evidence: report B, v27 ran 16 subagents vs 46, 37% cheaper, 16% faster, briefs averaged 1,564 chars vs 3,221 with no brief files. Cost: main context grows by roughly 1.5k chars per task, about 6k tokens over 16 tasks. Acceptable. Keep the SDD rule "never paste prior-task history into a dispatch" (`subagent-driven-development/SKILL.md` §1) and the no-subagents contract for implementers (`implementer-prompt.md`, "every reviewer a worker spawned duplicated the task review").
- **One shared guide file read by every implementer.** Evidence: B, "v27 why fast": one page with repo location, test commands, repo traps; Ralph's `AGENTS.md` is the same idea. Cost: one file written once, ~60 lines.
- **Review once per task, by a fresh reviewer, for state/async tasks.** The user's premise that results "did not differ much" is contradicted by their own report: v26's reviews found 44 real defects, 7 high, and 5 of those 7 remain in v27 (`use-style-apply.ts:163`, `:118`, `shared-edit.client.tsx:428`). Every high finding was in a save/cancel/reload/sequential-run task. The main agent's own check caught fidelity issues and zero behavior defects. Cost: 27 review runs cost $52 and 2.4h, so about $2 and 5 minutes each. The round trips, not the reviews, were the expense.
- **Skip the review for layout-only tasks with a deterministic oracle.** Evidence: B, "layout-only tasks: the fidelity comparison caught more than review", and B's own recommendation. Dryforge's `go/SKILL.md` review policy (review only RISKY tasks with dependents) is the same mechanism. Cost: one judgment call by the controller per task.
- **Fix once, verified by a failing-then-passing test, no re-review.** Evidence: `executing-plans/SKILL.md` Final Review ("Do not dispatch a re-review: the covering tests already answer addressed"), dryforge's lightweight fix path. Cost: trust in the implementer's report.
- **One final whole-branch review with a cross-task lens.** Evidence: B, only the final review caught the stale shared form (high) and two duplicated components; $16 and 51 minutes. Cost: one large-diff reviewer run.
- **TDD with RED evidence in the report.** Evidence: B, both branches were green (2,899 vs 2,857 unit tests) yet differed in quality, and v26 had "tests whose name claims what they do not measure". A green suite did not discriminate; watching the test fail is the only cheap guard. Cost: one extra test run per behavior.
- **Progress ledger plus git reconciliation.** Evidence: SDD Setup section ("controllers that lost their place re-dispatched entire completed task sequences, the single most expensive failure observed"); the `Task N: complete (commits base..head)` line format is worth copying verbatim. Cost: one appended line per task.
- **Model pinned to opus, stop on limits.** Evidence: B, sonnet Task 4 took 211 turns vs 66 and cost $19.8 vs $3.9; the fable detour wasted 5h 4m and $128 because the main downgraded itself. This directly contradicts SDD's Model Selection tiering, which I drop.
- **Root cause before fix, bounded retries.** Evidence: `systematic-debugging/SKILL.md` Phase 1 (read the error, reproduce, check recent changes) and workflow-orchestrator's "same approach at most twice". Cost: a few lines of prompt.

## 2. DROP

- **Fix loop with re-review, 5 rounds** (`subagent-driven-development/SKILL.md` §4, `re-review-prompt.md`). B: 27 reviewer plus re-reviewer runs, 2.4h, and 42 deferred items still left at the end.
- **Per-task brief files, report files, review-package diffs** (`scripts/task-brief`, `scripts/review-package`). B: 6.7MB of handoff documents. A reviewer can run `git diff BASE..HEAD` itself.
- **Model tiering** (SDD Model Selection). B: cheaper models were not cheaper.
- **Brainstorming, spec, constitution, harness-doc generation.** Probe E, S1: superpowers needed 11 human answers, gstack 29 and 62 minutes; S3: dryforge $3.14 and 20 files vs baseline $0.13 for a one-character fix. Skills did not change correctness on any of the three tasks.
- **Pre-flight interface conflict table** (SDD Setup). Unmeasured; the final review already caught cross-task conflicts in B.
- **Three parallel reviewer lenses** (BMAD `step-04-review.md`). Unmeasured benefit; BMAD violated the git rule in S2.
- **Parallel implementers and worktree pools** (dryforge parallel wave, mattpocock `implement-spec`, Ralph's 500 subagents). B: merging the two branches conflicted in 130 files because every task touched the same CSS and copy files. Sequential is the safe default.
- **Fresh-context loop per iteration** (Ralph). S1: $9.39, 34.6 minutes, 11 docs, for a CLI the baseline built in 1.8 minutes.
- **Per-task human checkpoints.** Probe pattern 6: the tools with the fewest human replies finished with equal correctness.

## 3. OPEN QUESTIONS

1. **Review every task vs. selective.** Measure from existing data first: in the v26 ledger, count Critical/Important findings on layout-only tasks. If near zero, selective is safe. Then a benchmark: a 12-task plan, half state/async and half layout, run under all/selective/none, three seeds each. Metric: high-severity defects found by two blind auditors, plus cost and wall time.
2. **Does dropping re-review lose anything?** From the v26 ledger: of 27 re-reviews, how many returned NOT ADDRESSED or new breakage? Under 10% means the drop is free.
3. **Does RED evidence produce better tests?** Same tasks with and without a required RED line. Metric: mutation score, or an auditor counting tests that still pass when the implementation is stubbed.
4. **Inline brief vs. brief file at scale.** Run a 30-task plan. Metric: main-context tokens at the end, compaction count, and tasks where the implementer missed a brief requirement.
5. **Fix pass without re-review at the final stage.** Metric: regressions introduced by the fix pass, found by the suite and one blind auditor, across ten runs.
6. **Resume reliability.** Kill the session at ten random points. Metric: duplicated tasks, lost commits, wrong resume point.

## 4. DRAFT SKILL.md

```markdown
---
name: waygent
description: Implement a multi-task plan with one opus implementer per task, TDD, one review per task, one final review, no re-review loops. Use on /waygent or "implement this plan". Not for one-file fixes.
---

# waygent

You are the controller. You dispatch, read short reports, review once, fix once, keep a
progress file. You never implement a task yourself and never add process the plan did not ask for.

## Gate
Run only on `/waygent` or when asked to implement a plan with several tasks. A single small
change (one or two files, obvious fix): say so and do it directly with a test. No workflow.

## Input
- `/waygent <plan.md>`: plan with `## Task N` headings. Read it once; never re-read it per task.
- `/waygent` alone: write `.waygent/plan.md` yourself, 3 to 12 tasks, each with goal, files,
  tests to write, done-when. Show it once and proceed unless the user objects. No brainstorming.
- Read CLAUDE.md/AGENTS.md. Find the test, lint and typecheck commands now, once.

## Setup
- Refuse to run on main/master. Create or check out `waygent/<plan-slug>` unless the user
  named a branch. Tree must be clean or the user consented.
- `.waygent/` is scratch: write `.waygent/.gitignore` containing `*`.
- Progress file `.waygent/progress.md`, first line `# waygent plan: <path> branch: <name>`.
  If it already names this plan, go to Resume.
- Write `.waygent/guide.md` once, max 60 lines: repo layout, exact test/lint/typecheck
  commands, repo traps, conventions the plan fixes. Every implementer reads it.

## Per task
1. `BASE=$(git rev-parse HEAD)`. Append `Task N: started BASE=<sha7>`.
2. Dispatch ONE implementer: Agent tool, general-purpose, `model: opus`. Never two at once.
   Brief in the prompt, max ~40 lines, no brief file:
   ```
   Task N of M: <title>. Read .waygent/guide.md first.
   Goal: ...
   Files: create ... / edit ... / do not touch ...
   Interfaces from earlier tasks: <names and signatures only>
   Tests: write failing tests for <behaviors> first, run them, keep the failing output,
   then implement, then green. Run the full suite once before committing.
   Done when: ...
   Rules: no subagents. Do not ask the user; return BLOCKED with specifics instead.
   Commit on this branch: "task N: <title>".
   Return max 15 lines: STATUS (DONE | DONE_WITH_CONCERNS | BLOCKED), commits,
   RED (command + failing line), GREEN (command + count), concerns. No diff.
   ```
3. DONE_WITH_CONCERNS: read the concerns; correctness concerns go to step 5 as findings.
   BLOCKED: go to Error analysis.
4. Review once. Fresh reviewer, `model: opus`, read-only. Give it the same brief, BASE, HEAD
   and the plan's global constraints. It runs `git diff BASE..HEAD` itself and returns
   Critical / Important / Minor with file:line, plus "cannot verify from diff" items.
   Skip the review only when BOTH hold: the task has no state, async, cancel, reload, error
   path or shared-component change; AND a deterministic oracle already in the repo
   (snapshot, fidelity or contract test) ran green. Append `Task N: review skipped (<oracle>)`.
5. Fix once, no re-review. Critical and Important: resume the same implementer with the
   findings verbatim: "per finding, add a test that fails, fix, green, run the suite, commit,
   report the test name". A trivial one-liner you may fix yourself and commit.
   Minor: append `Task N: deferred: <one line>`; do not fix now.
   Accept when the report names a test per finding and the suite is green. Never re-review.
6. In the same message as the last commit action append
   `Task N: complete (commits <base7>..<head7>, tests: <cmd> -> <result>, review: clean|K fixed|skipped)`.

## Final review, once
After the last task: MERGE_BASE=`git merge-base <base-branch> HEAD`. One reviewer,
`model: opus`, over the whole range, plus the deferred list. Ask explicitly for cross-task
issues: duplicated components or helpers, stale state shared between screens, contracts
between tasks, tests that assert nothing. Then ONE fix pass by one implementer under the
step 5 rules. No second review. Run the full suite. Report: what was built, rulings you made,
deferred minors, anything unverified.

## Resume
After any restart or compaction trust progress.md and `git log`, not memory.
- `Task N: complete`: run `git log --oneline <base7>..<head7>`. Commits present: skip.
  Missing (reset or rebase): treat as not started.
- `Task N: started` without complete: commits after BASE present: run step 4 on that range
  and continue. No commits and a dirty tree: `git stash push -m waygent-task-N`, then
  redispatch with "a partial attempt is in stash waygent-task-N; inspect or ignore it".
- Unrelated red tests at resume: record them in progress and guide.md; do not fix them.

## Error analysis (BLOCKED, red tests in a report, or a failed fix)
- Read the exact command, error text and stack line. Reproduce the one failing test if cheap.
- Classify: plan wrong or ambiguous -> rule, append `Task N: ruling: <what, why>`, redispatch
  with the ruling. Missing context -> add it to guide.md or the brief, redispatch the same
  implementer. Code wrong -> resume the implementer with the exact error and "find the root
  cause before changing code; no symptom patch; if the fix spans more than 3 files, say so".
- Same approach at most twice. Third failure: append `Task N: stuck: <summary>`, stop, ask.
  Never switch models and never skip the task silently.

## Git
- All work on the waygent branch, at least one commit per task. Never push, merge, open a PR
  or rebase unless the user asked. Never `git add -A`; `.waygent/` stays ignored. Do not
  commit CLAUDE.md or docs the plan did not ask for.

## Model
- `model: opus` on every Agent call, implementer and reviewer. Never omit it, never downgrade.
  On a usage or rate limit: finish the current call, append `paused: limit`, tell the user, stop.

## Not in this skill
No brainstorming, spec or constitution phase. No per-task human checkpoint. No brief, report
or diff files. No parallel implementers, no worktree pools, no reviewer trios, no re-review,
no generated docs. No model tiering.
```

## 5. RISKS of this draft

- **The skip rule depends on the controller's classification.** A task labeled "layout" that quietly touches form state loses its review, and B shows those are exactly the high-severity defects. The rule requires a named oracle, but the controller can still misjudge.
- **Fixes without re-review are only as honest as the report.** An implementer can name a test that does not exercise the finding. Open question 3 measures this; until then it is trust.
- **Inline briefs grow the main context.** At 16 tasks this is small; at 40 tasks compaction is likely mid-run, and resume then rests entirely on the ledger line being appended in the same message as the commit. One skipped append means a duplicated task.
- **The final reviewer may not fit a 16-task diff in context.** The draft says nothing about splitting; the reviewer will either truncate or self-split unpredictably.
- **Stopping on rate limits stalls unattended runs.** B shows that continuing on opus worked while downgrading did not, so the stop is right, but a run left overnight simply halts.
- **Sequential implementers are slower.** Parallelism was dropped on the strength of one merge-conflict observation. For plans whose tasks touch disjoint files, this leaves time on the table.
- **No-plan mode is unmeasured.** Nothing in B or E tests the controller writing its own task split. The split quality drives everything downstream.
- **Stash on resume is a judgment call.** A stashed partial attempt is easy to forget, and a second stash with the same name is confusing. It is safer than discarding and cheaper than reviewing a dirty tree, but untested.