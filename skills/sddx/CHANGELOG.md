# Changelog

All notable changes to this product are documented in this file.

## Unreleased

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
