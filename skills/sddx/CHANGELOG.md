# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 1.1.0 - 2026-09-11

### Added

- A bundled Claude Code reviewer agent raises review effort to XHigh without a new install step; the existing skill link carries it.

### Changed

- Native reviewers follow the active orchestrator model, and effort is High unless a named trigger in the diff calls for XHigh. This overrides generic SDD model selection.

### Fixed

- Worker dispatch supplies complete task context and repeats the boundary against retrieving the full plan, including through shell and search tools.
- Completion checks compare tool-call and results evidence with the worker's required scope-deviations report; missing evidence cannot count as verified compliance.
- Test reports preserve full wrapper commands and distinguish test exits from wrapper exits.
- Define Search paths as content-search boundaries; allow filename-only inspection within the worktree and direct reads of task-needed repository ignore/build/test configuration.
- Align worker, dispatch and reviewer rules so permitted inspection alone is reported without a scope concern; full-plan content and secrets remain prohibited.

## 1.0.1 - 2026-09-11

### Fixed

- Grok dispatch prepares a temporary worktree Git write profile so the worker can commit, then restores or removes the generated configuration after exit.
- Worker exit code 0 no longer counts as task completion when the report is blocked, missing, or unclear.

### Changed

- Grok backend resolution now requires the sandbox, rules, and disabled web-search flags.

## 1.0.0 - 2026-09-11

### Changed

- Resolver treats Grok identity as Grok Build, xAI Grok, or a line that starts with `grok `, not any substring `grok `.

### Notes

- First standalone release. Superpowers SDD stays the workflow owner; this skill overrides implementer dispatch only.
- No GitHub tag or GitHub Release is created.
