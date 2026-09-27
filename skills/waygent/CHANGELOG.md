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
