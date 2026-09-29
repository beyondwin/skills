---
name: waygent
description: Use only when the user message contains /waygent or $waygent. Runs a multi-task implementation with one fresh implementer subagent per task, test-first, one review per task, one final review, and resume from a progress file. Do not use for brainstorming, writing specs or plans, a single small fix, /sddx, or Superpowers subagent-driven-development.
license: Apache-2.0
compatibility: Requires a Git repository and a host with a subagent tool (Claude Code Agent tool, Codex spawn_agent with multi_agent enabled, Cursor Agent Task tool, or Grok Build spawn_subagent). Works with or without a plan file.
metadata:
  version: "0.3.0"
  updated_at: "2026-09-30"
---

# waygent

A thin loop around a strong model. You are the controller: you dispatch, check, and
keep the progress file; subagents write the code. Keep your context small: no history
in a dispatch, no whole diffs, and whole files only once at start, for repo traps.

## Input

- `/waygent <plan-file>`: the plan's tasks are the scope. Read the plan once.
- `/waygent <request>` with no plan: write a numbered task list (goal, files, done-check
  per task) into the progress file, show it, ask once to proceed; it is the plan now.
- `/waygent` alone: resume the one folder under `.waygent/`, else this `waygent/` branch.
- Ask only when docs and code contradict each other, or a choice changes what the
  user will see. Everything else: decide, and record the ruling in progress.

## Start or resume

State lives in `P=<repo root>/.waygent/<plan-slug>/`: `progress.md`, `guide.md`, and
`reviews/`. If `.waygent/.gitignore` is missing, write it with the single line `*`.

If `$P/progress.md` exists, or this branch has `Waygent-Task:` commits not on `main`
or `master`, resume:
- Git is the truth. A task is done only if a commit with trailer `Waygent-Task: <N>`
  is reachable from HEAD; never redo it.
- Continue at the lowest task with no trailer commit. A trailer commit with no `done`
  line: go on at step 5 if `reviews/task-N.md` exists, else at step 4.
- Dirty tree: an attempt was cut off. Give it to the same implementer if reachable, else
  a fresh one ("continue from the uncommitted changes"). Never discard it; keep `base=`.
- Progress missing (say, after `git clean -fdx`): rebuild it from those commits, with
  `start` = merge-base with `main`/`master` and `review=unknown`; rewrite guide.md.

Otherwise start:
- If on `main` or `master`, create `waygent/<plan-slug>` unless the user named a branch.
  Never commit to `main` or `master`. Never push, merge, or open a PR unless asked.
- Write `$P/progress.md`: `plan: <path>`, `branch:`, `start: <sha>`, `model: <m/e>`.
- Write `$P/guide.md` once, at most 40 lines: working directory, the exact test and
  lint commands (run each once, note the result) split into a fast check and the slow
  rest (one command: it is the fast check), how to start the app for the final walk
  if the repo has a way, repo traps, and the plan's global rules verbatim.

## Per task

1. `BASE=$(git rev-parse HEAD)`. Append `task N: start base=<sha7>`.
2. Dispatch one implementer. Never two at once. Brief, at most ~1,500 characters:

   ```
   Task N of M: <title>. Read <P>/guide.md first. Plan: <path>, section "<task heading>".
   Depends on: <names and signatures from earlier tasks, nothing else>.
   Test first: for each behavior, write a test, run it, see it fail for the right
   reason, then implement until it passes. A test that passes before the code exists
   proves nothing. Cover the plan's principles that apply to this task, not only its
   happy path. Run the full suite before the trailer commit.
   Commit on this branch in the repo's message format; several commits are fine, and
   only the task's last one carries the trailer "Waygent-Task: N" in its last paragraph.
   Do not spawn subagents, leave a process running, push, or edit outside this task.
   Start the app only if this task changes how it starts.
   Reply in at most 10 lines: DONE | BLOCKED, commit sha, RED (one failing line),
   GREEN (suite summary line), concerns.
   ```

3. Check: `git log --grep='^Waygent-Task: N$'` finds the commit, the tree is clean, and
   guide.md's fast check passes when you run it (slow suites run once at the end).
4. Review once. A fresh reviewer gets the task heading, `<P>/guide.md`, and
   `BASE..HEAD`, and runs the diff itself. Ask for: behavior defects (interrupts, stale
   state, partial failure, races, error paths), mismatches with the plan's rules, and
   tests that do not measure what they claim. It spawns nothing, stops what it starts,
   writes the full review to `<P>/reviews/task-N.md`, and replies only High / Medium /
   Low, each with file:line and a one-line reproduction, at most 15 lines. Skip only a
   task with no behavior (docs, rename): `review=skipped (<why>) reviewer=none`.
5. Fix once, no re-review. Send High and Medium verbatim to the same implementer if
   reachable, else a fresh one. Each fix starts from a test that fails first. A ruling
   never cancels a High or Medium: overrule one only after running its reproduction and
   seeing the code behave correctly; write one line why. A finding that only disputes a
   recorded ruling, without showing it breaks the plan or design, changes nothing and
   goes to `note for user:`. If a fix seems to need a name or signature the plan fixed
   (async stays async), send the smallest fix that keeps them (internal state, an
   optional keyword, a continuing counter). Only when none exists, or the finding is
   outside the task, write `note for user:`; a gap that keeps the changed code from
   starting or deploying is never outside the task. The fix commit also carries the
   trailer. Check as step 3. Append each Low as `task N: low: <file:line> <gist>`.
6. Append `task N: done <sha7> impl=<m/e> review=<clean|fixed K|skipped> reviewer=<m/e>
   tests=<summary>`. `<m/e>`: `<model>/<effort>`, each as set, else `inherit`; never guess.

## When a task fails

BLOCKED, a failed check at step 3 or 5, or no commit:
1. Read the actual error output and reproduce it with one command. Write one cause:
   `task N: failure: <symptom> — cause: <x> — next: <y>`.
2. Retry once, fixing the cause, not the symptom: a fresh implementer ("continue from
   the uncommitted changes"), one tier up where the host can pick. If the plan itself
   is wrong, rule on it, record the ruling, and redispatch. Then check as step 3.
3. Second failure: stop and report the cause, the sha, and what you tried.
On a usage or rate limit, append `paused: limit` and stop; resume picks up there.

## Final review, once

After the last task, one fresh reviewer, one tier up, reads `start..HEAD`, the plan, and
the Low list, writes the full review to `<P>/reviews/final.md`, and replies with the
short list, each with a failure scenario checked against the code. Ask for behavior
defects still left (the step 4 list) and what per-task review cannot see: duplicated
helpers, state shared across tasks, contract drift between layers (server types, API
schema, client types, mocks), money and counts on failure paths, config needed at
startup and deploy order, queries at real scale (N+1), dead code, tests that assert
nothing. Send High and Medium to one implementer in one batch, test-first, under step
5's overrule and plan-name rules; Lows go in the report. Then, if guide.md says how to
start the app, that implementer starts it, walks the changed flows on real data, not
fixtures, fixes what it finds test-first in the same batch, and stops what it started.
No second review. Run the full suite once more (red: retry once, then stop) and append
`final: done <sha7> reviewer=<m/e> fixed=K walk=<ok|none> tests=<summary>`.

## Models

Implementers and per-task reviewers run on the same model and effort as this session.
Never switch to a cheaper model or lower effort. Go one tier up in exactly two places:
the final reviewer, and the retry after a failure. At the top tier, or when the host
cannot pick, use your own. No subagent spawns subagents of its own or leaves a process
running; say so in every brief, reviewers' included.

- Claude Code: name the model in every dispatch; tiers are sonnet, opus, fable.
- Codex: `fork_turns: "none"`, `model` and `reasoning_effort` unset so the child inherits
  yours; do not guess your model name. One tier up sets only `reasoning_effort: "xhigh"`.
- Grok Build: `spawn_subagent` with `run_in_background: false`, no `model`, no effort.
- Cursor Agent: `Task` with no model, so the child uses yours.

## Report

At most 15 lines: tasks and commits, findings fixed or overruled, the final suite
result, rulings, and anything you did not verify. Claim nothing you did not run.
Beyond the code, write only under `$P`; never edit CLAUDE.md or AGENTS.md.
