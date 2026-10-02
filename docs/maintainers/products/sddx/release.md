# sddx release

This document owns how SDDx is packaged on its own. The version source is
`skills/sddx/release.toml`. `SKILL.md` `metadata.version` is a checked copy. The
human-facing history is `CHANGELOG.md` in the same directory.

## What is in this document

- The current version and whether it is public: "Current state"
- What each MAJOR and doc-fix version changed: "Version history"
- Pre-release checks and manual confirmation: "Check, build, download"
- When something fails: "Recovering from failure"

## Current state

There is no public sddx release yet. The current standalone version is
`8.2.0`, and `release.toml` is the source. There are no tags or artifacts.

`release.toml` and `SKILL.md` `metadata.version` must always hold the same value.

## Version history

Newest first. Details are in each CHANGELOG section.

- `8.2.0` (unreleased): `run.json` records the worker's reported token counts
  as `usage` (Cursor's `result` event; null for Grok). SKILL.md drops restated
  red flags and gains a Gotchas section of recorded failures. CHANGELOG
  `Unreleased`.
- `8.1.1`: only a prohibited read (the plan, credentials, secrets) makes role
  compliance FAIL; any other read outside the brief is a scope deviation for the
  reviewer. CHANGELOG `## 8.1.1 - 2026-10-02`.
- `8.1.0`: fixes from the 2026-10-01 log audit. An interrupt while the backend
  resolves is recorded, and `wait` sees a dead runner (`runner_pid`); per-host
  waiting; `wait --start-grace`; `extract_task.py --constraints-heading` for plans
  whose run-wide rules have their own title; bare worker test commands; the
  stopped-runner check. CHANGELOG `## 8.1.0 - 2026-10-01`.
- `8.0.0`: a breaking change to the base loop. SDDx runs on waygent instead of
  Superpowers SDD: state in `.waygent/<plan-slug>/`, one review and one fix per
  task, reviewers per waygent's Models section, and the XHigh reviewer agent and
  Claude plugin file removed. It also records the models and efforts that
  actually ran. CHANGELOG `## 8.0.0 - 2026-09-30`.
- `7.0.2`: docs only, no behavior change. The docs are English-first:
  `README.md` is English and the Korean copy moves to `README.ko.md`. It was never
  tagged; the change is listed under CHANGELOG `## 8.0.0 - 2026-09-30`.
- `7.0.1`: a doc fix with no behavior change. In the 7.0.0 live check, Grok wrote
  nothing while it waited on a backgrounded command and hit the idle timeout, so
  the background advice was removed and replaced by one rule: when a long command
  is expected, raise `--idle-timeout` above that command's expected duration
  before launch. The change is in the CHANGELOG `## 7.0.1 - 2026-09-24`.
- `7.0.0`: a breaking change to the runner contract. Instead of a 300-second
  first-output deadline, the attempt ends when neither log grows for
  `--idle-timeout` (default 900 seconds), and `error` is
  `the worker wrote no output for <N> seconds`. The default `--timeout` is 0
  (off) instead of 7200. The change is in the CHANGELOG `## 7.0.0 - 2026-09-24`.
- `6.0.0`: a breaking change to the runner contract. When the runner is
  interrupted it ends the worker it started, it ends an attempt with no output
  for 300 seconds, and the default timeout is 7200 seconds. The change is in the
  CHANGELOG `## 6.0.0 - 2026-09-24`.
- `5.0.0`: a breaking change to the worker model contract. Grok Build and Cursor
  Agent use only Grok 4.7, never a `-fast` variant. Grok requires
  `--model grok-4.7`. The change is in the CHANGELOG `## 5.0.0 - 2026-09-22`.
  There is no public tag yet.
- `4.0.3`: the change is kept in `## 4.0.3 - 2026-09-19`.
- `2.0.0`: the MAJOR before that. The Cursor backend's required CLI features and
  default run contract changed. An older Cursor CLI that does not declare
  `--auto-review`, `--sandbox`, and a structured output format is blocked with
  `available: false`, `reason: missing_flags` instead of falling back to blanket
  `--force`/`--yolo` approval.
- `1.0.2` and `1.0.3`: development versions pushed only to main, with no tags or
  artifacts, never released. Their changes are included in `1.1.0`. The `1.0.2`
  and `1.0.3` sections in the maintainer docs are measurement records from that
  time, so they keep those numbers.

A product with no public tag yet still does not hide contract changes in its
development versions. The rule is the skill SemVer table in
[`docs/maintainers/repository/versioning.md`](../../repository/versioning.md).

## Check, build, download

The shared check / build / verify-download commands are in
[`docs/maintainers/repository/release.md`](../../repository/release.md). The
product check is `python3 scripts/release.py check --product sddx`. It passes only
when the product's owned paths and the shared release code are clean in the
worktree, so run it after committing.

`python3 scripts/release.py check --product sddx` is offline, so it cannot
confirm a real run. Before a public tag, run the live check in
[`testing.md`](testing.md) ("Live check") on macOS and stop the release if it
fails.

The product tag is `sddx-v<version>`. Tags and Drafts are explicit release work,
not a side effect of a local build.

When installed files change, the `release.toml` and `SKILL.md` version decision
and the product CHANGELOG entry must be in the same change. The first release
does not create a tag.

## Recovering from failure

- Local check fails: fix the files, version, CHANGELOG, or tests, and check again.
- Packaging fails: rebuild into a new output directory. Do not reuse partial
  output.
- This product fails: do not change other products' versions, tags, or Releases.

These commands do not create a tag or a GitHub Release.
