# waygent compatibility

This document sets which hosts and OS waygent supports, and on what evidence. The
supported hosts are the three in the product registry, `claude-code`, `codex`, and
`cursor`, for local or repository-linked use only. Support scope and measurement status
are separate. Measurements are in the record below; installed files changed after that
are `not_measured` until measured again.

- Claude Code: implementation and review run as subagents (the Agent tool).
- Codex: called with `$waygent`. Subagents run through the `spawn_agent` tool, and
  `~/.codex/config.toml` must have `[features]` `multi_agent = true`.
- Cursor Agent: a host for this product. In `sddx` it is still a worker, not a host.
  Subagents run through the `Task` tool and use the main model even when no model is given.
- Grok: not supported.
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
