---
name: waygent
description: Use only when the user message contains /waygent. Runs a multi-task implementation with one fresh implementer subagent per task, test-first, one final review (bench variant: no per-task review), and resume from a progress file. Do not use for brainstorming, writing specs or plans, a single small fix, /sddx, or Superpowers subagent-driven-development.
license: Apache-2.0
compatibility: Requires a Git repository and a host with a subagent tool (Claude Code Agent tool or Cursor Agent Task tool). Works with or without a plan file.
metadata:
  version: "0.1.0"
  updated_at: "2026-09-27"
---

# waygent

A thin loop around a strong model. You are the controller: you dispatch, check, and
keep the progress file. Subagents write the code. Keep your own context small: never
paste history into a dispatch, and never read whole diffs or files unless a decision
needs them.

Run only when the user's message contains `/waygent`.

## Input

- `/waygent <plan-file>`: the plan's tasks are the scope. Read the plan once.
- `/waygent <request>` with no plan: write a numbered task list (goal, files,
  done-check per task) into the progress file, show it, and ask once to proceed.
- Ask only when docs and code contradict each other, or a choice changes what the
  user will see. Everything else: decide, and record the ruling in progress.

## Start or resume

State lives in `P=$(git rev-parse --git-path waygent)`: `progress.md` and `guide.md`.
It is never committed and survives `git clean`.

If `$P/progress.md` exists for this plan, resume:

- Git is the truth. A task is done only if a commit with trailer `Waygent-Task: <N>`
  is reachable from HEAD. Add missing progress lines for such commits; never redo them.
- Dirty tree: an attempt was cut off. Look at `git status` and `git diff --stat`, then
  hand the partial work to a fresh implementer ("continue from the uncommitted
  changes"). Never discard it.
- Continue at the lowest task with no trailer commit.

Otherwise start:

- If on `main` or `master`, create `waygent/<plan-slug>` unless the user named a
  branch. Never commit to `main` or `master`. Never push, merge, or open a PR unless asked.
- Write `$P/progress.md`: `plan: <path>`, `branch:`, `start: <sha>`, `model: <yours>`.
- Write `$P/guide.md` once, at most 40 lines: working directory, the exact test and
  lint commands (run each once to confirm), repo traps you found, and the plan's
  global rules copied verbatim. Every implementer reads it; do not repeat it in briefs.

## Per task

1. `BASE=$(git rev-parse HEAD)`. Append `task N: start base=<sha7>`.
2. Dispatch one implementer. Never two at once. Brief, at most ~1,500 characters:

   ```
   Task N of M: <title>. Read <P>/guide.md first. Plan: <path>, section "<task heading>".
   Depends on: <names and signatures from earlier tasks, nothing else>.
   Test first: for each behavior, write a test, run it, see it fail for the right
   reason, then implement until it passes. A test that passes before the code exists
   proves nothing. Cover the plan's principles that apply to this task, not only its
   happy path. Run the full suite before committing.
   Commit on this branch: "task N: <title>" with trailer "Waygent-Task: N".
   Do not spawn subagents, push, or edit files outside this task.
   Reply in at most 10 lines: DONE | BLOCKED, commit sha, RED (one failing line),
   GREEN (suite summary line), concerns.
   ```

3. Check cheaply: the trailer commit exists and the suite passes (run it yourself,
   keep only the summary line). A missing commit or red suite is a failure, not done.
4. No per-task review. Put anything you noticed in progress for the final review.
5. (none)
6. Append `task N: done <sha7> review=final-only tests=<summary>`.

## When a task fails

BLOCKED, a red suite after the fix, or no commit:

1. Read the actual error output. Reproduce it with one command.
2. Write one cause in progress: `task N: failure: <symptom> — cause: <x> — next: <y>`.
3. Send that cause to the implementer once: fix the cause, not the symptom. If the
   plan itself is wrong, rule on it, record the ruling, and redispatch.
4. Second failure: stop and report the cause, the sha, and what you tried.

Never switch to a cheaper model. On a usage or rate limit, append `paused: limit`
and stop; resume later picks up from progress.

## Final review, once

After the last task, one fresh reviewer reads `start..HEAD`, the plan, and the Low
list. Ask for behavior defects (interrupts, stale state, partial failure, races, error
paths), mismatches with the plan's rules, and also for what spans tasks: duplicated helpers or components,
state shared across tasks, broken contracts between tasks, dead code, tests that
assert nothing. Send in-scope High and Medium to one implementer in one batch,
test-first. A finding outside the plan's scope, or one whose fix would change a
name or signature the plan fixed, is not sent: write it as `note for user:`.
No second review. Run the full suite once more.

## Models

Give every subagent the same model as this session, stated explicitly in the
dispatch. Do not use cheaper models for implementers or reviewers.

## Report

At most 15 lines: tasks done with commits, review findings fixed or overruled,
the final suite result, rulings you made, and anything you did not verify. Do not
claim a result you did not run.

## Not in this skill

No brainstorming, spec, or design phase. No per-task brief, diff, or report files.
No parallel implementers or worktree pools. No re-review loop. No human checkpoint
per task. No generated docs or edits to CLAUDE.md or AGENTS.md.
