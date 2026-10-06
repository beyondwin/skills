# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 0.4.0 - 2026-10-07

### Added

- `agents/waygent-final-reviewer.md`, a Claude Code agent definition (opus, effort
  xhigh). Linked into `~/.claude/agents/`, it becomes the final reviewer when the
  controller runs below opus at xhigh, dispatched with no `model`; without the link the
  final reviewer is fable as before. In the 2026-10 routing cells (app2, 6 runs each)
  opus/xhigh cut final-review cost from $1.69 to $1.08 per run with no hidden or trap
  loss and valid final findings inside fable's range. The progress line records
  `reviewer=opus/xhigh`.

## 0.3.3 - 2026-10-03

### Changed

- The description says only when to use the skill and when not to; the sentence that
  summarized the loop is gone. A contract test keeps every sentence a "Use" or
  "Do not use" sentence, as in the other five products.

## 0.3.2 - 2026-10-02

### Changed

- The implementer brief is about 2,000 characters, not at most: recorded rulings and
  dependencies stay in even when that runs longer. In the 2026-10-01 live runs every
  Task 3 brief ran 2,275-2,319 characters because of rulings the task needed, with no
  harm.

### Fixed

- Reviewers leave the tree as they found it, and a tree left dirty by any review is
  stashed (`git stash push -u -m "waygent: review leftovers"`, so nothing is lost)
  before the fix. In a 2026-10-02 sddx run a
  task reviewer left a test mutant in the code although its ask said not to edit; the
  next worker found it by chance.

## 0.3.1 - 2026-10-01

### Fixed

- Resume is scoped to this run: it starts only when the plan's `progress.md` exists or on
  `/waygent` alone, a task counts as done only if its trailer commit is in `start..HEAD`,
  and the step 3 check searches `$BASE..HEAD`. Older `Waygent-Task:` commits on a reused
  branch no longer mark a new plan's tasks done.
- A rebuild after the records are lost takes `start` from the merge-base with the
  branch's upstream or the remote default branch (else `main`/`master`), and asks which
  run when a `Waygent-Task: N` repeats in that range. With no folder at all, the slug
  comes from the branch name, else waygent asks once.
- `/waygent` alone resumes the one folder whose progress has no `final: done` and asks
  once when there are several. A finished folder is reported and nothing starts. If
  `start` is no longer an ancestor of HEAD (say, after a squash), the run stops and says
  the history changed.
- The final phase can resume: it opens with `final: start`, its fix commits carry
  `Waygent-Task: final`, and a resume goes to the full suite run when a
  `Waygent-Task: final` commit is already in `start..HEAD`, else to the fixes when
  `reviews/final.md` exists, else to the review.
- One subagent at a time, reviewers included; the controller waits for each to report
  before the next dispatch or message. Claude Code sets `run_in_background: false` when
  the Agent tool offers it; a dispatch that still returns in the background ends the turn
  with only that dispatch outstanding, a subagent lost with the session is re-dispatched
  fresh, and a fresh implementer is preferred over SendMessage when the session may not
  stay open. Codex waits with `wait_agent` and a long timeout instead of polling.
- The fast check includes the build or typecheck step when the repo has one; `guide.md`
  lists test, lint, and build or typecheck commands. A production build break passed
  two task checks without it.
- A subagent's transient 429 is redispatched once; only the controller's own usage limit
  writes `paused: limit` and stops.
- Per-task and final reviewer asks carry a short quoted line the controller pastes (spawn
  nothing, stop every process you start, write the full review to its path, reply only
  High / Medium / Low), so the stop line is no longer dropped in paraphrase.
- The final app walk can no longer be skipped silently: `guide.md` holds
  `app: <how to start>` or `app: none (<why>)`, and the final line records
  `walk=<ok|none (<why>)>`.

### Changed

- Progress records: one review-status set,
  `review=<clean|fixed K|overruled K|skipped (<why>)|unknown>`; the final line adds
  `impl=<m/e>`; a retry appends `task N: retry impl=<m/e>`; the `model:` header records
  the session's model and its effort as set, else the model alone; `reviewer=none` only
  when no reviewer ran.
- Size rules match real plans: the brief is at most ~2,000 characters; `guide.md` at most
  ~60 lines, names the plan's global rules by section (verbatim only if they fit), gets
  traps found later appended, and names generated paths to exclude locally in
  `.git/info/exclude`, never committed.
- Resume continues at the next task in the recorded order (default: lowest).
- README (both languages): `inherit` means the controller set no value, and a one-tier-up
  subagent may run at its own configured effort; findings the repo cannot settle (deploy
  order, policy) come back as notes in the report; the progress example shows the new
  lines.

## 0.3.0 - 2026-09-30

### Changed

Fixes from a three-model review (Fable, Opus, Sonnet) and from reading the 0.2.0 run
logs:

- `progress.md` records who did the work: `impl=` and `reviewer=` on each task line and
  `reviewer=` on the final line, as `model/effort`. A value the controller did not set
  is written `inherit`, never guessed. Low, done, and final lines have fixed formats.
- A "ruling" can no longer cancel a High or Medium. The controller must run the
  reviewer's reproduction first, so per-task reviewers now include a one-line
  reproduction. In a measured 0.2.0 run a correct High was dropped by a ruling.
- Resume: a task that has its commit but no `done` line picks up at its review or fix
  instead of being marked done. After `git clean -fdx`, `start` is the merge-base and
  guide.md is written again. `/waygent` alone resumes.
- Checks: after each task the tree must be clean and the trailer found with
  `git log --grep`. A red check at step 3 or 5, or a red full suite after the final
  fixes, goes through the failure path (one retry, then stop).
- Implementers run the full suite before the trailer commit only, and start the app
  only when their task changes how it starts (0.2.0 implementers started it 3-5 times
  per task and left it running). The brief and the reviewer ask now say not to leave
  a process running.
- Lows go in the report instead of the final fix batch.
- Cursor Agent has its own Models line (`Task` with no model). The retry after a
  failure is always a fresh implementer.

### Added

- First version. `/waygent [plan-file|request]` runs a plan one task at a
  time: one fresh implementer subagent per task, test first, one review per
  task, fixes without re-review, one final review, and resume from a progress
  file checked against `Waygent-Task: N` commit trailers.
- Fix rules from the 2026-09 evaluation: overrule a High or Medium finding only
  after running its reproduction; when a fix seems to need a plan-fixed name or
  signature, first send the smallest fix that keeps them; only then leave a
  `note for user:`. The final review also looks for behavior defects left.
- Records move to `.waygent/<plan-slug>/` at the repository top level, kept out
  of git by `.waygent/.gitignore` (`*`). Reviewers write their full findings to
  `reviews/task-N.md` and `reviews/final.md` and return only the short list.
  Progress is rebuilt from trailer commits when the records are gone.
- Models: implementers and per-task reviewers keep the session model, never a
  cheaper one or lower effort. When the host can pick, the final reviewer and
  the retry after a failure go one tier up.
- Grok Build is a supported host: `/waygent`, subagents through `spawn_subagent`
  with no model named, found through any of the three skill links.
- Hosts: Claude Code, Codex, and Cursor Agent. Codex calls it with `$waygent`,
  finds it through `~/.agents/skills/waygent`, and needs `multi_agent = true`
  under `[features]` in `~/.codex/config.toml`. On Codex the controller names no
  model, so children inherit the session's (a measured Codex controller misnamed
  its own model); one tier up sets only `reasoning_effort` to `xhigh`. No subagent starts
  subagents of its own.
- Changes from the 2026-09-28 won-sec-ai run (13 tasks, about 14 hours), whose
  final review missed two Highs and live defects that later checks found:
  the final review now also asks for contract drift between layers, money and
  counts on failure paths, startup config and deploy order, and queries at real
  scale, each with a checked failure scenario; after the final fixes, when
  `guide.md` says how to start the app, one implementer walks the changed flows
  on real data and fixes what it finds in the same batch.
- Every brief, reviewers' included, says not to spawn subagents (the final
  reviewer had forked five).
- `guide.md` splits a fast check from slow suites; the controller reruns only
  the fast check per task (it spent about 47 minutes rerunning slow e2e).
- A task may take several commits in the repository's message format; only the
  last carries `Waygent-Task: N`. Cut-off work goes back to the same implementer
  when it can still be reached.
- A gap that keeps the changed code from starting or deploying, such as a config
  file the plan did not list, is fixed inside the task instead of left as
  `note for user:` (a measured 0.1.0 run shipped a prod config that could not
  start). No subagent leaves a process it started running; every brief says so
  (implementers and reviewers left test servers running in measured runs).
- Docs are English-first: `README.md` is English and `README.ko.md` is the
  Korean user guide.
