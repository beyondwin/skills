# pre-sdd-review compatibility

This document records which hosts Pre-SDD Review has actually been checked on.

## Supported hosts

Only Codex is supported today. The contract needs a local Git repository,
readable design and plan files, repository inspection, and an isolated
read-only reviewer, and that has been measured only on Codex. Every other host
is `not_measured`.

The same folder layout does not mean the same reviewer isolation or repository
behavior. Never infer support from an install path, a similar subagent
feature, or passing provider-free fixtures. Add a host to the registry and the
public docs only after a fresh-session smoke check records the needed behavior.

### Host matrix

| Host | Status |
| --- | --- |
| `claude-code` | `not_measured` |
| `codex` | `supported` |
| `cursor` | `not_measured` |
| `grok` | `not_measured` |

## Supported OS

macOS is the only supported OS. Windows and Linux are not supported. CI may run
the full verification on Ubuntu; that pass is neither Linux support nor
evidence of macOS support.

## Recorder compatibility

Recorder compatibility is separate from the host matrix above, which covers
review behavior. Codex, Claude Code, Cursor, and Grok use the same
`evidence/evidence.py` from the loaded skill root and share one data root,
`~/.pre-sdd-review/`. A working recorder does not prove that host's
independent read-only review or its review quality.

### CLI matrix

| Runtime | Status | Evidence boundary |
| --- | --- | --- |
| macOS / Python 3.11+ | `verified` | provider-free evidence suite |
| Linux / Python 3.11+ | `unsupported` | product not supported; a CI POSIX check is not Linux product support |
| Windows / Python 3.11+ | `unsupported` | Windows is not supported |

Mutation commands take OS file locks on `.identity.lock` and
`locks/<run-id>.lock`. `show`, `summary`, and `--version` are read-only and do
not take those locks.

## Evidence limits

The required provider-free commands are in [Testing](testing.md). They prove
only the deterministic package and instruction contracts, not live review
quality or equality across hosts. Optional live checks run only explicitly,
locally, and with non-sensitive input.
