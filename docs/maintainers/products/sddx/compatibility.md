# sddx compatibility

This document records which programs run SDDx and where it hands off the coding.
A host is the program that runs the skill; a worker is the outside CLI that only
does the implementation.

The supported hosts are `claude-code` and `codex`, as listed in the product
registry. Cursor CLI and Grok CLI are implementation workers, not hosts. What is
supported and what has been measured are separate questions. Claude.ai, Cowork,
Skills API upload, marketplace publication, and cloud sync are not supported.

## What is in this document

- Supported OS and install links: "Supported OS", "Discovery paths", "Invocation"
- What the offline checks prove: "Evidence without a provider"
- What access a Grok worker gets: "Grok worker boundary"
- What 8.0.0 has been run on: "8.0.0 measurement state"
- Older measurements, kept as history: "2.0.0 measurement state",
  "1.0.x observations", "2026-09-14: how the MCP tool filter came in"
- How far live runs count as evidence: "Live evidence boundary"
- Adding a host: "Supporting a new host"

## Supported OS

The supported OS is macOS only. Windows and Linux are unsupported. CI can run the
full check on Ubuntu. That pass is not Linux support and is not macOS support
evidence.

## Discovery paths

```text
skills/sddx/                 repository source
├─ ~/.agents/skills/sddx    ─→ Codex
└─ ~/.claude/skills/sddx    ─→ Claude Code
skills/waygent/              required base loop, linked the same way
├─ ~/.agents/skills/waygent
└─ ~/.claude/skills/waygent
```

SDDx reads `<skill-root>/../waygent/SKILL.md`, so waygent must sit next to sddx
in the same skills folder. Do not create copies in `~/.codex` or `~/.grok`. Do
not add Cursor or Grok to `supported_hosts`.

## Invocation

| Host | Explicit call | Discovery path |
| --- | --- | --- |
| Codex | `$sddx` | `~/.agents/skills/sddx` |
| Claude Code | `/sddx` | `~/.claude/skills/sddx` |

`agents/openai.yaml` is optional Codex display metadata, not a required runtime
file. Since 8.0.0 there is no Claude Code agent definition or plugin file.

## Evidence without a provider

The required evidence is `python3 scripts/verify.py --skill sddx`. It checks
package identity, resolver fixtures, and sandbox prepare and restore. It does not
prove live model quality or runtime parity across the supported hosts.

## Grok worker boundary

Grok's sandbox setup needs Python 3.11+. The temporary profile inherits
`workspace` and adds write access to the Git directory (and, in a linked
worktree, the shared Git directory) so the worker can commit. That also means it
can write the repository's Git metadata. The settings and restore state are not
committed and are cleaned up after the worker ends.

Keeping the worker away from outside skills and the full plan is an instruction
in the worker prompt. Grok also drops the MCP call tools at the CLI and passes an
MCP permission deny rule. This is not isolation that blocks every
initialization, shell, or file access, and it does not guarantee the worker
cannot leave its role.

## 8.0.0 measurement state

8.0.0 changed the base loop, so earlier end-to-end results do not carry over.
The runner, resolver, and sandbox helpers are unchanged apart from the
`.waygent/` path and `reported_model`.

| Host | Worker | State |
| --- | --- | --- |
| Claude Code | Grok CLI | see "8.0.0 live check" in [Testing](testing.md) |
| Claude Code | Cursor Agent | `not_measured` |
| Codex | Grok CLI | `not_measured` |
| Codex | Cursor Agent | `not_measured` |

## 2.0.0 measurement state

History: these rows were measured on the Superpowers-based loop with
`2.0.0`-era CLIs. They are not evidence for 8.0.0.

- 7.0.2, 7.0.1, 7.0.0, and 6.0.0 do not change the worker model contract.
- 5.0.0 pinned workers to Grok 4.7 and dropped the `-fast` variants, but did not
  change the worker columns in the table.
- 4.0.3 re-ran the `run_worker.py` smoke with current Cursor
  `2026.09.15-d2fe57e` and Grok `1.0.34`. That smoke does not change the quality
  table for the four host x worker pairs.

All four pairs called real providers with the product owner's approval. Every
run was on macOS 26.6.2 arm64. Cursor was `cursor-agent 2026.09.10-fd3934a` with
model `cursor-grok-4.6-high`. Grok was `grok 1.0.30 (04b7ffed98c6)`, which takes
no model argument; Grok picks its own model, and the init event reported
`grok-4.6`.

Attempts split into before the MCP tool filter (up to `bfd1cda`) and after it.
Before: on the Claude Code host, Cursor three times and Grok twice; on the Codex
host, Cursor twice and Grok twice. After: on the Claude Code host, Cursor twice
and Grok twice; on the Codex host, Grok twice and one Cursor resume. Each row
says which side it observed and does not extend its result to the others.

| Controller host | Implementation worker | `2.0.0` live run | Basis |
| --- | --- | --- | --- |
| Claude Code | Cursor CLI | `measured` | Three worker attempts before the fix and two after (new and resumed) each implemented the briefed task, ran the brief's tests, committed, and wrote `report.md` themselves. The two after the fix reported the same `session_id`, and the reports read contained the items the contract requires (status, changed files, worker checks with RED and GREEN exit codes, commit SHA, scope departures) |
| Claude Code | Grok CLI | `measured` | One full `prepare_grok_sandbox.py prepare` → `run_worker.py run` → `--resume` → `cleanup` cycle in a plain checkout before the fix and one in a linked worktree after. All four attempts finished implementation, tests, commit, and `report.md`, and the two attempts in each cycle reported the same `session_id`. The reports read contained the items the contract requires |
| Codex | Cursor CLI | `measured` | A Codex session as controller ran new and resumed attempts that implemented the task, went RED exit 1 → GREEN exit 0, and committed from the worker (`6c244d5`, `bffd2f9`); one more resume ran on the fixed runner. The repository maintainer did not observe this directly: it was confirmed by reading the `trace-audit.json` and per-attempt `run.json` files Codex left, and the originals are only in a local evidence directory |
| Codex | Grok CLI | `measured` | The same way: new and resumed attempts (`033cb04`, `85ade8f`), then new and resumed attempts again with the final filter. Also confirmed from the records Codex left |

Items are also split into measured and not measured. A `measured` row is what was
observed in the pair that row names, and nothing more.

| Item | `2.0.0` state | Basis |
| --- | --- | --- |
| Real Cursor approval behavior | `measured` | With the resolver's argv (`--print --trust --auto-review --sandbox enabled`), 22 tool calls including file writes, test runs, and `git commit` ran with stdin `DEVNULL` and no interactive prompt. The stream's init event had `permissionMode: "default"` |
| Model ID acceptance and `configured_effort` record | `measured` | For `--effort high` and `--model cursor-grok-4.6-high`, the init event showed the display name `"model": "Cursor Grok 4.6 High"`, so the model ID was accepted; `configured_effort` `high` in `run.json` is what the runner read from that same ID. This observes which ID the provider accepted, not the effort the model applied |
| Session ID capture and `--resume` | `measured` | On both Cursor and Grok, passing the `session_id` captured from the real stream back through `--resume` returned an attempt reporting the same `session_id`, and the worker continued the task |
| Timeout on a real worker | `measured` | A real worker with `--timeout 5` gave wrapper exit 124, `state: timed_out`, `exit_code: 143`, and a recorded `session_id`; the attempt left no processes |
| Refusal before an attempt exists | `measured` | An effort and model ID that contradict each other, and `--timeout inf`, were each refused with exit 2 and a `BLOCKED:` line before the attempt directory was created |
| Real Cursor OS isolation | `not_measured` | `--sandbox enabled` is a declaration check; the real isolation scope was not measured |
| Effort the model actually applied | `not_measured` | Only the requested and configured effort are recorded; there is no way to see the applied value. These live runs did not create one either, and model ID acceptance is not evidence of the applied value |
| Grok stream shape | `measured` | Two `streaming-messages-json` streams (19 and 17 lines) were observed. In both, every line parsed as a JSON object and had a `session_id` key, with no other spelling of the session key. Both first lines were `system`/`init`, spelled the same as the first line of the Cursor stream observed in the same place |
| Grok sandbox profile round trip | `measured` | `prepare` created the `sddx-worktree` profile (`extends = "workspace"`) in `.grok/sandbox.toml`, and `cleanup` removed the `.grok` it created. In a plain checkout `read_write` was an empty list; in a linked worktree it held the real Git directory and the shared Git directory. The write-access path described in "Grok worker boundary" above worked in that run, and the worker committed from inside the linked worktree. The commits held only task files; no evidence or sandbox files were committed |
| Real isolation of the Grok sandbox | `not_measured` | Only that the profile was created and passed as an argument was checked; what it actually blocked was not measured |
| Grok's real effort argument | `measured` | The resolver's `--reasoning-effort high` was really on the command line, and `configured_effort` in `run.json` was `high`. This observes the requested value on the command line, not the effort the model applied |
| Grok MCP call tools removed | `measured` | After the fix, the init event's 23-tool list had no `search_tool` or `use_tool`. Checked on both new and resumed attempts. The CLI removed the tools, so this is enforced, not an instruction |
| Whether the Grok subagent boundary is enforced | `not_measured` | The same init event still lists `spawn_subagent` after `--no-subagents`, and reports every host skill and three MCP servers (`context7`, `x-docs`, `playwright-sandboxed`) as connected. Excluding the `Agent`/`task` groups was not adopted because it also removes the tools that read and end command output. No subagent calls in the observed attempts means the model followed instructions, not that the CLI blocked them |
| MCP server list shown | `measured` | With the tool filter in place, the init event still reports the three servers as connected. That list is not evidence of a real connection or call, and does not contradict the call tools being gone |
| Effect of the MCP discovery environment variables | `not_measured` | The runner sets `GROK_CURSOR_MCPS_ENABLED=0` and `GROK_CLAUDE_MCPS_ENABLED=0` only for the Grok child. Offline checks confirm they are passed, but every Grok attempt observed in this repository, before and after the fix, had 0 bytes of stderr, so the effect could not be told apart. The drop from 4 handshake failures to 0 comes from a Codex cause-isolation probe record and was not reproduced here. The names are a provider-internal convention: if Grok renames them, they silently stop working with no error |
| Required Grok tool filter options | `measured` | The resolver requires `--disallowed-tools` and `--deny` declared as taking values, and refuses with `missing_flags` otherwise. The installed `grok 1.0.30` help declares `--deny <RULE>` and `--disallowed-tools <TOOLS>`, and resolution gave `available: true`. The check matches only that help spelling, so a build that writes the same options differently is refused even though it would work |
| Fallback key spellings in `read_session_id` | `not_measured` | Both providers gave the session ID as `session_id`, and the Grok stream had no other spelling. That key is checked first, so the `sessionId`, `chatId`, and `chat_id` branches have never run |
| Claude Code agent definition loading | `measured` | Claude Code `2.1.258`. With the file at `agents/sddx-reviewer-xhigh.md` and no `agents` key in `plugin.json`, `claude plugin details sddx@skills-dir` reports Agents (1) `sddx-reviewer-xhigh`, listed as `sddx:sddx-reviewer-xhigh`. The bare Task name spawned 0, the registered name spawned 1. `--agent sddx-reviewer-xhigh` is a CLI alias |
| Claude Code `disallowedTools` | `measured` | The `--agent sddx-reviewer-xhigh` session's init tool list has no Write, Edit, or NotebookEdit, and has Read. Asked to create probe.txt with Write, no file appeared and the reply was `BLOCKED Write`. permission_denials was an empty list (the tools were removed from the list) |
| Effort applied to the Claude Code reviewer | `measured` | The parent session effort was high. The assistant events in the Task `sddx:sddx-reviewer-xhigh` child transcript record `effort: xhigh` |
| Current Cursor/Grok `run_worker.py` smoke | `measured` | Cursor `2026.09.15-d2fe57e` with model `cursor-grok-4.6-high`, and Grok `1.0.34` prepare → run → cleanup. Both gave `state: exited`, `exit_code: 0`, `report.md` `DONE`, and a captured session_id. This smoke does not change the quality of the four host x worker pairs |
| New-session switching and general role compliance | `not_measured` | Role compliance and session switching outside the attempts counted above were not observed. In the observed attempts, the worker ran a wrong check command from the brief, saw it fail, wrote that in the report, and then produced RED and GREEN again a valid way |

## Known platform and evidence limits

Windows is unsupported, and the product CLIs refuse it.

Grok's `--rules` are not kept in the attempt directory. The rule text goes only on
the command line, and the spec fixes the attempt directory at exactly six files,
so after `skills/sddx/references/worker-prompt.md` changes, a past Grok attempt
cannot be reproduced exactly from the saved evidence alone. This is a result of
the six-file contract, not an omission.

## 1.0.x observations

Everything below records `1.0.x` installed files and is not evidence for
`2.0.0`. At the time, `Codex × Grok CLI` in 1.0.3 was confirmed with two real
calls, 10/8 tests, "none" reports for file name and config lookups, and
path-scoped search. `Codex × Cursor` and `Claude Code × Cursor or Grok` were
`not_measured` then as well.

The first 1.0.1 fixture confirmed three calls, 14 final tests, and no observed
role violation. Two later independent fixtures were each measured again with
three calls; final 15/14 tests, commits, and restore succeeded, but a new session
reading the full plan was reproduced. The existing sandbox config's bytes and
0640 mode were also restored after every later real call. Do not read earlier
successful samples as a full pass today or a guarantee of role compliance.

1.0.2 tightened the brief boundary, reporting, tool-record rulings, and review
model inheritance. Reviewers run host-native on the current controller model and
set High/XHigh separately. When the host does not support that control, the
limit is reported. Three new calls on the final wording passed 15 tests and
direct commit, resume, and restore, with no plan content exposed. The last
worker's DONE_WITH_CONCERNS about checking file names and ignore rules was
accepted under an existing ruling based on the real record and an independent
review. The early candidate that exposed search results stays as a separate
failure record.
1.0.3 spells out that listing file names and directly reading config needed for
the task are allowed, and when to report "none". Two new sessions actually did
those lookups together with native and shell content search, and confirmed 10 and
8 tests and config restore. Both original reports disclosed the allowed lookups
and still said DONE/none with no needless scope concern. This is what those
fixtures showed; it does not prove a general compliance rate or enforced file
access blocking.
Claude Code's model and effort mapping and the Cursor event trace were still not
measured in a live run then. Reproduction steps and per-version observations are
in [Testing](testing.md).

## Live evidence boundary

Live runs are local, explicit, optional, and may cost money. CI does not require
them. Do not describe a passing payload contract as evidence of a live call.

## Supporting a new host

Adding support to the registry and public guides needs real observed evidence and
a separate support decision. Only after deciding to change support, update
`products.toml`, the public guides, and the tests together. The shared user
guide is [Compatibility](../../../users/en/compatibility.md).

## 2026-09-14: how the MCP tool filter came in

The tables above are the 2.0.0-era record. This section keeps how that record came
about and the options dropped along the way.

The runs used a real Codex controller on macOS, with a separate synthetic
repository and a linked worktree. Before the fix, at `d7e16ca`, two Cursor runs
(new and resumed) and two Grok runs (new and resumed) all finished
implementation, tests, a direct worker commit, and the report. The final
independent tests were 10 for Cursor and 11 for Grok, plus extra checks for 29
whitespace characters and 6 wrong types.

The warning came from Grok importing the Cursor MCP config and trying to start
`playwright-sandboxed`. Instead of changing global settings, the fix turns off two
compatibility variables in the child environment. Model names, auth, and session
stores stay as they are.

Excluding the `Agent`/`task` tool groups was not adopted because it also removed
the tools that read and end command output. Excluding only the real tool name
`spawn_subagent` did not remove the spawn tool either. The final filter excludes
only `search_tool,use_tool` and passes a `MCPTool(*)` deny rule. Enforced
blocking of subagents and scheduled jobs is not a promise of this change.

A new Grok session started with the final tool filter ran 13 tests and a real
background shell. `get_command_or_subagent_output` returned the `BG_PROBE_OK`
output, `completed`, and exit 0, and tool calls matched results 9/9. The tool
list kept the tools that read and end command output and had no MCP search or
call tools. Do not confuse the successful implementation and resume calls from
the `Agent`-exclusion candidate with evidence for this final filter.

A follow-up request resuming the same session also went RED exit 1 → GREEN 13
tests/exit 0, with a direct worker commit and DONE. Tool calls and results were
11/11, and the two calls' session IDs matched. Both final Grok calls had 0 MCP
handshake warnings, and the sandbox config and journal were cleaned up after
exit. The last independent checks passed 11 Cursor and 13 Grok tests and
`diff --check` over all commits, and both fixtures were clean.

A resume of an existing Cursor session on the fixed runner also finished
implementation, RED exit 1, GREEN 11 tests/exit 0, and a direct commit, with 14/14
real tool calls and results. The Cursor environment and the approval and sandbox
arguments were not changed.

Grok's own managed-config permission warning, plugin name clash, and compatibility
hook parse warning remain. Global settings were not deleted and warning output
was not hidden. The existing MCP server list shown in init/inspect is not
evidence of a real connection or call. Full OS isolation, the effort actually
applied, and long-run stability on large projects are not proven by these
observations. Original provider records are kept only locally.

Runtime SHA-256 checked (same before and after the runs):

- `resolve_backend.py`: `780adfee9042bf4be6ecc0e6104adc70024c265b50827bee828182eb3971f797`
- `run_worker.py`: `3bda36903eabfa53c9ca97f35f3b349cba52b2c8ddaa387d8090fc694001302b`

### Two calls left open

The check that `--disallowed-tools` and `--deny` are declared with a value
spelling, and refuses otherwise, is kept narrow so an option name that merely
appears in a description sentence does not pass. The cost is that a build writing
the same options differently is refused even though it would work. This product
was once made unusable by exactly that kind of defect: fixing one spelling as the
rule instead of reading real CLI output. The narrow side is the choice for now,
because the refusal shows up as `missing_flags` instead of quietly falling back
to a weaker run. If a real refusal case appears, loosening it with `_declares` is
the right move.

The MCP discovery environment variables, by contrast, have no check at all. In
the Codex cause-isolation probe, these variables were what actually removed the
handshake failures, but if the provider renames them they silently stop working
with no error. The provider docs give no way to confirm the names, so no check was
added; the table above records them as `not_measured` instead.
