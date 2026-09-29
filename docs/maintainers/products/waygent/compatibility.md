# waygent compatibility

This document sets which hosts and OS waygent supports, and on what evidence. The
supported hosts are the four in the product registry, `claude-code`, `codex`,
`cursor`, and `grok`, for local or repository-linked use only. Support scope and measurement status
are separate. Measurements are in the record below; installed files changed after that
are `not_measured` until measured again.

- Claude Code: implementation and review run as subagents (the Agent tool).
- Codex: called with `$waygent`. Subagents run through the `spawn_agent` tool, and
  `~/.codex/config.toml` must have `[features]` `multi_agent = true`.
- Cursor Agent: a host for this product. In `sddx` it is still a worker, not a host.
  Subagents run through the `Task` tool and use the main model even when no model is given.
- Grok Build: called with `/waygent`. It reads skills from `~/.agents/skills`,
  `~/.claude/skills`, and `~/.cursor/skills`, so any of the links above works.
  Subagents run through `spawn_subagent`; with no `model` the child inherits the
  session model, and a subagent cannot spawn its own (depth limit 1).
- Claude.ai, Cowork, Skills API upload, and marketplace publication are not supported.

## Supported OS

The supported OS is macOS only. Windows and Linux are unsupported. A passing Ubuntu CI
run is not macOS support evidence.

## Discovery paths

```text
skills/waygent/              repository source
├─ ~/.claude/skills/waygent ─→ Claude Code
├─ ~/.agents/skills/waygent ─→ Codex
└─ ~/.cursor/skills/waygent ─→ Cursor Agent
```

Grok Build reads all three folders and deduplicates by skill name.

On 2026-09-27, Cursor Agent 2026.09.23 was confirmed to read both the project path
`.cursor/skills/<name>/SKILL.md` and the user path `~/.cursor/skills/<name>/SKILL.md`
(by calling a test skill).

The link block is in the product README and in [local links](../../../users/en/install-local.md).
It does not automatically replace a different link, file, or directory.

## Measurement record

Detailed tasks and numbers are in [waygent design and evaluation](../../../research/2026-09-waygent-eval/README.md).
This record is execution evidence at that point in time and does not vouch for later versions.

| Host | Version | Model | Date | waygent | Result |
| --- | --- | --- | --- | --- | --- |
| Claude Code | 2.1.280 | opus (Opus 5.5) | 2026-09-27 | 0.1.0 working copy | 5 runs completed (64/63/64 of 64 hidden tests; 64/58 after the rule fix). 1 interrupt-and-resume run 64/64. 1 run alongside superpowers 64/64 |
| Claude Code | 2.1.280 | fable (Fable 5.1) | 2026-09-27 | 0.1.0 working copy | 1 run completed (64/64), $25.95 |
| Cursor Agent | 2026.09.23 | grok-4.7-high | 2026-09-27 | 0.1.0 working copy | 2 runs. Both committed all 10 Tasks (63/64, 64/64). Run 1 was cut off by the harness turn cap before the final review. Very slow, 291 minutes on average |
| Codex | 0.154.0 | gpt-5.6-sol (high) | 2026-09-27 | 0.1.0 working copy | 2 runs completed, both committed all 10 Tasks (63/64, 62/64). In run 1 the controller misidentified its own model and spawned children on a different model. In run 2, fixed to inherit the model, all 22 children used the session model. The final wording that pins one tier up to `xhigh` was not measured. Under `codex exec` an explicit-only skill is not loaded by `$waygent`, so `agents/openai.yaml` was removed from the measured copy |
| Claude Code | 2.1.284 | opus (Opus 5.5), final review fable | 2026-09-29 | 0.2.0 working copy (SKILL.md sha256 `1e26a14a`…) | 1 run on the 10-Task fixture: 64/64 hidden tests, re-create defect fixed, $11.38, 47.5 minutes (v2 run: 64/64, $10.82, 44.5 minutes). All 21 briefs, reviewers included, carried the no-spawn line; no subagent spawned one. `guide.md` named the fast check and "no app to start", and the app check was skipped for that reason. Final review 0 High, 0 Medium. Review-fix commits also carried the task trailer. The app check, cross-layer drift, and startup config were not exercisable on this one-layer library. Same day, 3 runs on the 3-Task multi-layer app task (1 with the rules in the design, 2 with them left out): 12/12 each, the app walked on dev and prod configs; rerun with 4 more runs per condition on the rules-left-out variant: across 6 runs each, vanilla missed a trap in 3, 0.1.0 in 1, 0.2.0 in 0 ([results, section 12](../../../research/2026-09-waygent-eval/results.md)) |
| Grok Build | 1.0.41 | grok-4.7 (default effort xhigh) | 2026-09-28 | 0.1.0 working copy (with the Grok line) | 1 smoke run on a 2-Task plan, completed: both Tasks committed with trailers, Task 1 review found 1 issue fixed by resuming the implementer (`resume_from`), final review High/Medium none, 14 tests pass, `.waygent/` records and `.gitignore` written. 6 subagents, none named a model. 29 minutes, $0.88. Not run on the 10-Task fixture |
