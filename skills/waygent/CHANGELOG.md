# Changelog

All notable changes to this product are documented in this file.

## Unreleased

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
  start). The app check stops the processes it started.
- Docs are English-first: `README.md` is English and `README.ko.md` is the
  Korean user guide.
