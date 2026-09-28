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
- Docs are English-first: `README.md` is English and `README.ko.md` is the
  Korean user guide.
