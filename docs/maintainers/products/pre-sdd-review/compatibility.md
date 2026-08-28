# pre-sdd-review compatibility

This document owns the measured-host boundary for Pre-SDD Review.

## Supported host

Codex is supported because the measured contract requires a local Git
repository, readable design and plan files, repository inspection, and an
isolated read-only reviewer. Every other host is `not_measured`, including a
host that can parse the Markdown package but has not demonstrated the same
reviewer isolation and repository behavior.

Do not infer support from an installer path, a similar subagent feature, or a
provider-free fixture run. Add a host to the registry and public documents only
after a recorded fresh-session smoke establishes the required behavior.

### Host matrix

| Host | Status |
| --- | --- |
| `claude-code` | `not_measured` |
| `codex` | `supported` |

## Evidence limit

The required provider-free command is documented in [testing](testing.md). It
proves deterministic package and instruction contracts, not live review quality
or cross-host equivalence. Optional live checks remain explicit, local, and
non-sensitive.
