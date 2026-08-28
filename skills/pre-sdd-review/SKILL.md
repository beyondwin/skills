---
name: pre-sdd-review
description: Use when an approved design spec and implementation plan already exist and must be reviewed, automatically improved, and re-reviewed against repository reality immediately before SDD. Do not use for creating specs or plans, reviewing code, implementing changes, proofreading, or release readiness.
license: Apache-2.0
compatibility: Requires a local Git repository, readable design and plan files, and Codex subagent support for independent review.
metadata:
  version: "1.0.0"
  updated_at: "2026-08-29"
---

# Pre-SDD Review

Review an approved design and implementation plan against repository reality,
repair the documents when authorized, and review them again. The skill never
starts SDD itself.

## Default

The default flow is review, repair, and re-review. `review-only` is explicit.

## Reference

- [Reviewer protocol](references/reviewer-protocol.md)
