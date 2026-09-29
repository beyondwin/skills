---
name: waygent
description: Use only when the user message contains /waygent or $waygent. Runs a multi-task implementation with one fresh implementer subagent per task, test-first, one review per task, one final review, and resume from a progress file. Do not use for brainstorming, writing specs or plans, a single small fix, /sddx, or Superpowers subagent-driven-development.
license: Apache-2.0
compatibility: Requires a Git repository and a host with a subagent tool (Claude Code Agent tool, Codex spawn_agent with multi_agent enabled, Cursor Agent Task tool, or Grok Build spawn_subagent). Works with or without a plan file.
metadata:
  version: "0.1.0"
  updated_at: "2026-09-27"
---

# waygent

A thin loop around a strong model. You are the controller: you dispatch, check, and
keep the progress file. Subagents write the code. Keep your own context small: never
paste history into a dispatch, and never read whole diffs or files unless a decision
needs them.

Run only when the user's message contains `/waygent` or `$waygent`.

## Input

- `/waygent <plan-file>`: the plan's tasks are the scope. Read the plan once.
- `/waygent <request>` with no plan: write a numbered task list (goal, files,
  done-check per task) into the progress file, show it, and ask once to proceed.
- Ask only when docs and code contradict each other, or a choice changes what the
  user will see. Everything else: decide, and record the ruling in progress.

## Start or resume

State lives in `P=<repo root>/.waygent/<plan-slug>/`: `progress.md`, `guide.md`, and
`reviews/`. If `.waygent/.gitignore` is missing, write it with the single line `*`, so
the folder is never committed and the user's `.gitignore` stays untouched.

If `$P/progress.md` exists, or this branch has `Waygent-Task:` commits, resume:

- Git is the truth. A task is done only if a commit with trailer `Waygent-Task: <N>`
  is reachable from HEAD. Add missing progress lines for such commits; never redo them.
- Dirty tree: an attempt was cut off. Look at `git status` and `git diff --stat`, then
  hand the partial work to a fresh implementer ("continue from the uncommitted
  changes"). Never discard it.
- Continue at the lowest task with no trailer commit.
- Progress missing (for example after `git clean -fdx`): rebuild it from those commits.

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
4. Review once. A fresh reviewer gets the task heading, `<P>/guide.md`, and
   `BASE..HEAD`, and runs the diff itself. Ask for: behavior defects (interrupts,
   stale state, partial failure, races, error paths), mismatches with the plan's
   rules, and tests that do not measure what they claim. It writes the full review to
   `<P>/reviews/task-N.md` and replies with only High / Medium / Low, each with
   file:line, at most 15 lines. Skip only a task with no behavior (docs,
   config, rename) and append `review: skipped (<why>)`.
5. Fix once, no re-review. Send High and Medium findings verbatim to the same
   implementer if you can still message it, otherwise to a fresh one. Every fix
   starts from a test that fails before the fix. Overrule a High or Medium only
   after running its reproduction and seeing the code behave correctly; write one
   line why. If a fix seems to need a name or signature the plan fixed (async stays
   async), first look for the smallest fix that keeps them (internal state, an
   optional keyword, a continuing counter) and send that. Only when none exists, or
   the finding is outside the task, write `note for user:` in progress and in the
   report. Put Low findings in progress for the final review. Check as in step 3.
6. Append `task N: done <sha7> review=<clean|fixed K|skipped> tests=<summary>`.

## When a task fails

BLOCKED, a red suite after the fix, or no commit:

1. Read the actual error output. Reproduce it with one command.
2. Write one cause in progress: `task N: failure: <symptom> — cause: <x> — next: <y>`.
3. Retry once with that cause: fix the cause, not the symptom. Send it to a fresh
   implementer one model tier above yours when the host lets you pick one
   ("continue from the uncommitted changes"); otherwise to the same implementer. If
   the plan itself is wrong, rule on it, record the ruling, and redispatch.
4. Second failure: stop and report the cause, the sha, and what you tried.

On a usage or rate limit, append `paused: limit` and stop; resume picks up there.

## Final review, once

After the last task, one fresh reviewer (see Models) reads `start..HEAD`, the plan,
and the Low list, writes the full review to `<P>/reviews/final.md`, and replies with
the short list. Ask for behavior defects still left (the step 4 list) and for what
per-task review cannot see: duplicated helpers or components, state shared across
tasks, broken contracts between tasks, dead code, tests that assert nothing. Send
in-scope High and Medium to one implementer in one batch, test-first, with the same
overrule and plan-name rules as step 5.
No second review. Run the full suite once more.

## Models

Implementers and per-task reviewers run on the same model and effort as this session.
Never switch to a cheaper model or lower effort. Go one tier up in exactly two places:
the final reviewer, and the retry after a failure. At the top tier, or when the host
cannot pick, use your own. No subagent spawns subagents of its own.

- Claude Code: name the model in every dispatch; tiers are sonnet, opus, fable.
- Codex: spawn with `fork_turns: "none"` and leave `model` and `reasoning_effort` unset
  so the child inherits yours; do not guess your model name. One tier up means setting
  only `reasoning_effort: "xhigh"`.
- Grok Build: `spawn_subagent` with `run_in_background: false`, no `model`, no effort.

## Report

At most 15 lines: tasks done with commits, review findings fixed or overruled,
the final suite result, rulings you made, and anything you did not verify. Do not
claim a result you did not run.

## Not in this skill

No brainstorming, spec, or design phase. No per-task brief, diff, or report files
beyond the reviewers' `reviews/`. No parallel implementers, worktree pools, re-review
loop, human checkpoint per task, generated docs, or edits to CLAUDE.md or AGENTS.md.
