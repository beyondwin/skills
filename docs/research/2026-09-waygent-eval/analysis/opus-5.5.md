Evidence and the key harness sources are read. Writing up the analysis and SKILL.md draft now.

## 1. KEEP

| Mechanism | Evidence | Cost |
|---|---|---|
| **One Opus implementer per task, given only its own task** | §B l.70: the v27 brief averaged 1,564 chars against v26's 3,221. The v26 implementers were slower on 9 of 10 Opus-vs-Opus tasks (13.5h vs 10.0h, l.65). The superpowers SDD file warns that a dispatch reached 42k chars, 99% of it pasted history. | One fresh context per task. |
| **One shared guide file** (where to work, commands, repo traps) that every brief points to | §B l.70, l.168. This is the main reason v27 was faster. | Written once, about 1 page. |
| **Pin the model and stop on a rate limit; never downgrade** | §B l.64: the Fable detour lost 5h04m and $128. §B l.74: Sonnet made 211 turns where Opus made 66, costing $19.8 vs $3.9. | You wait out the limit. |
| **Per-task review, but only for tasks with state or async behaviour** | §B l.99–110: 5 of the 7 high-severity defects the v26 review caught are still in v27. All were cancellation, reload or stale-form bugs. v27's main-agent check caught none of them (l.73). | $52 and 2.4h was the v26 cost *including* re-reviews (16%). One pass costs less. |
| **One final full review, then one fix round** | §B l.67, l.113, l.170: only the final review found the cross-task bugs (stale shared form, duplicated badge and particle helpers). It cost about $16 and 51 min. | Same as the evidence. |
| **Progress file that reconciles with git** | SDD Setup: "controllers that lost their place have re-dispatched entire completed task sequences — the single most expensive failure." | A few lines per task. I make git the source of truth with a commit trailer, because a git-ignored ledger dies on `git clean` (SDD admits this). |
| **Record BASE before each dispatch; diff BASE..HEAD, never HEAD~1** | SDD §3 | Nothing. |
| **Implementers never spawn subagents; never run implementers in parallel** | SDD §1. §B l.149: 130 files conflict. §B l.172: two sessions sharing one quota hit the limit together. | Serial wall-clock time. |
| **Reviewer checks what the tests actually measure** | §B l.114, l.146: tests that asserted nothing, tests passing only by name. | One line in the review prompt. |
| **Say "unverified" honestly** | wo SKILL.md:60–68. §B l.177: neither side ran the real-model check. §B l.178: v27's final report contained a false claim. | Nothing. |
| **Manual invocation only** (`disable-model-invocation`) | §E S4: an explicit command won; the hook-driven skill hijacked plain prompts. | Nothing. |

## 2. DROP

- **Re-review loops and 5 fix rounds with escalation** (SDD §4). They took 27 reviewer runs and 2.4h (§B l.66), and 42 deferred items were still left at the end (l.116).
- **Mixing model tiers or picking the cheapest model per task** (SDD "Model Selection"). §B l.74 shows it cost more and produced worse code.
- **Brief, diff and report files per task, and the review-package scripts.** They added up to 6.7MB (§B l.68). The reviewer can run `git diff` itself.
- **Pre-flight conflict table** (SDD Setup). There is no evidence it returned anything.
- **Session-start hook and the "1% rule".** In §E S1 superpowers needed 11 human replies against 4 for the baseline. In S2 it still made the same wrong assumption as the baseline (pattern 4).
- **The Iron Law "delete code written before the test"** (TDD SKILL.md:37). In the probe every condition added regression tests anyway (S3). v26 wrote 39k lines of tests against 23.8k and did not measure the right things better. Keep "a failing test first" as a strong default, but drop the rituals around it.
- **Spec, docs and constitution generation.** dryforge created 15–20 files on a one-character fix ($3.14 vs $0.13, §E pattern 1).
- **500 parallel subagents and auto-push** (Ralph PROMPT_build.md).

**Where I disagree with your premise:**
- **"Harnesses are unnecessary now" is only half-true.** v27's time saving did not come from skipping review. v27's main-agent check took 3.3h, *more* than v26's 2.4h of review round-trips. The saving came from shorter briefs, a pinned model and no detour.
- **"Review every task" is wrong by your own report.** In layout-only tasks, the screen-fidelity comparison caught more than review did (l.169).
- **"No re-review" is safe only if every fix comes with a failing test.** That test is what stands in for the re-review.

## 3. OPEN QUESTIONS

1. **Selective review vs every-task review vs final-only.** Use a 12-task plan with 12 seeded high-severity defects, half of them in state/async tasks. Run 3 conditions × 3 repeats and measure the seeded highs still present at the end, per dollar.
2. **How many fixes break something when there is no re-review?** Mine v26's ledger first; it is free. Of the 27 re-reviews, how many returned NOT ADDRESSED or found new breakage? Then run a mutation test on fix commits.
3. **Does strict test-first beat tests written alongside the code?** Take the same 6 tasks and compare mutation score on the changed modules plus behaviour defects found by blind reviewers.
4. **Opus reviewer vs Sonnet reviewer.** Compare turns, dollars and highs found on the same diffs. The Sonnet data in §B covered implementers only.
5. **Does resume work?** Kill the session at 10 random points in a 6-task plan. Count completed tasks that get re-dispatched, duplicate commits, and lost work.
6. **Why were v26 implementers 35% slower?** Ablate brief length alone (1.5k vs 3.2k chars) with everything else fixed, and compare implementer wall-time.

## 4. DRAFT

```markdown
---
name: waygent
description: Execute a multi-task implementation plan with one Opus implementer subagent per task, TDD, one review per risky task, and one final review. Resumable. Invoke explicitly with /waygent [plan-file].
disable-model-invocation: true
---

# waygent

A thin loop. You (main) coordinate; subagents write code. Keep your context small:
never paste history into a dispatch, never read full diffs yourself unless deciding something.

## 0. Gate
- Small change (≤2 files, one obvious fix): don't use this loop. Do it inline with a regression test.
- Otherwise continue. Plan file given → use its tasks. No plan → write a numbered task list
  (one line of goal + files + done-check each) into the progress file and proceed. Ask the user
  first only if docs and code contradict each other or a choice changes user-visible behavior.

## 1. Setup (once)
- Work on a feature branch or worktree. Never commit to main/master without explicit consent.
- `WG=.waygent/<plan-slug>/` (add `.waygent/` to .git/info/exclude). Record `START=$(git rev-parse HEAD)`.
- Write `$WG/guide.md` (≤1 page): work dir, install/test/lint/typecheck commands (verified by
  running them once), repo traps you found, conventions, global constraints copied verbatim
  from the plan/spec. Every implementer reads it; do not repeat it in briefs.
- `$WG/progress.md` first line: `# waygent — plan: <path> — start: <START>`.

## 2. Resume (every start, before dispatching)
Git is truth; progress.md is notes.
- Done tasks = commits in `git log START..HEAD` with trailer `Waygent-Task: N`.
- progress says done but no trailer commit → not done. Trailer commit but no progress line → done; add the line.
- Dirty tree → a task was interrupted. Look at `git status`/`git diff --stat`, then either hand the
  partial work to a fresh implementer ("continue from the uncommitted changes") or `git stash`
  and record why. Never discard silently.
- Resume at the lowest task number without a trailer commit. Never re-dispatch a done task.

## 3. Per task
1. `BASE=$(git rev-parse HEAD)`; append `Task N: start BASE=<sha>` to progress.
2. Dispatch ONE implementer, `model: "opus"`, with this brief (target ≤1,500 chars):
   - Goal (1–2 lines) and where it fits.
   - "Read $WG/guide.md first." Plan path + "your task is Task N" (or the task text if no plan).
   - Interfaces/decisions from earlier tasks this task depends on (names, signatures only).
   - Done-check: exact commands that must pass.
   - Contract: TDD — write a failing test for each behavior, see it fail, make it pass.
     Tests must assert the behavior the task claims, not just exist. Stage only your files.
     Commit with trailer `Waygent-Task: N`. Do not spawn subagents. Do not push.
     Reply ≤10 lines: DONE | DONE_WITH_CONCERNS | BLOCKED, commits, test command + result, concerns.
3. Review — once, only if the task touches state, async, cancel/retry, reload/refresh,
   concurrency, persistence, auth, money, error paths, or a component other tasks reuse.
   Skip for layout/copy/config/mechanical tasks whose done-check is deterministic; note `review: skipped (<reason>)`.
   Reviewer: `model: "opus"`, fresh, gets task text + guide path + `BASE..HEAD`.
   Ask for: behavior defects (esp. interrupt, stale state, partial failure, races),
   tests that don't measure what they claim, spec mismatches. Severity High/Medium/Low, file:line.
   Tell it not to re-run the suite unless a finding needs proof.
4. Fix — no re-review. Send High/Medium findings (you may overrule wrong ones; log one line why)
   to the SAME implementer (SendMessage) or a fresh one with the findings. Each fix starts with a
   failing test that reproduces the finding. You check the reported test output, then continue.
   Low findings → `Task N: low: <one-liner>` in progress for the final review.
5. Append `Task N: done <sha> review: <done|skipped> fixes: <n>`.

## 4. When a task fails
Triggers: BLOCKED, done-check still red after the fix, or the implementer loops.
- Analyze before retrying: read the actual error output, reproduce it with one command,
  state ONE root-cause hypothesis, test it with the smallest check. Write to progress:
  `Task N: failure: <symptom> — cause: <confirmed|suspected> <x> — action: <y>`.
- Then one of: re-dispatch with the finding; split the task; fix the plan (log the ruling);
  or stop and ask the user if every option is a guess.
- At most 2 attempts per task, then stop and report. Do not switch models.
- Rate/usage limit: stop, write `paused: limit` to progress, tell the user. Never downgrade the model.

## 5. Final review (once)
- One fresh Opus reviewer over `START..HEAD` + the plan + the `low:` list. Focus on what per-task
  review cannot see: duplicated components/helpers, cross-task stale state, broken contracts
  between tasks, dead code, docs pointing at old paths.
- One fix dispatch for High/Medium (TDD as above). No re-review.
- Run every verification command from the plan/guide once. Record exact results.

## 6. Report
≤20 lines: tasks done, commits, review findings fixed/overruled/deferred, verification results,
and an explicit UNVERIFIED list (anything not actually run — e.g. real model, browser, deploy).
Don't claim anything you didn't run. Don't push, merge, or open a PR unless the user asked.

## Rules that matter
- All subagents `model: "opus"` (explicit). Never parallel implementers.
- Dispatches describe one task, never session history. Keep subagent replies short.
- After compaction, trust `git log` + progress.md over memory.
```

## 5. RISKS

- **The review trigger is a judgment call.** Main can misread a "UI" task that hides async state and skip the review. The five highs that stayed in v27 were in exactly such tasks. A plan tag like `[review]` would help, but not every plan has one.
- **No re-review means a wrong fix ships quietly** if the reproducing test is weak. That makes Open Question 2 the first thing to measure.
- **SendMessage back to a finished implementer may not work** in some builds. The fallback, a fresh implementer, repays the context cost.
- **Trailer reconciliation fails** if an implementer squashes commits, forgets the trailer, or amends. Rebasing also breaks START.
- **The "≤2 files, go inline" gate bypasses TDD and review** on small but risky edits.
- **The final review's single fix round can itself break things across tasks.** Only the verification run guards against that.
- **Evidence base is thin:** one 16-task comparison and 30 single-sample probe runs on toy repos. Nothing here is statistically settled.