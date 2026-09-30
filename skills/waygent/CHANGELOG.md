# Changelog

All notable changes to this product are documented in this file.

## Unreleased

### Changed (0.3.0)

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
