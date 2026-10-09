# Personal Korean technical-writing pilot

2026-10-09. [한국어](README.ko.md).

This follow-up turns the [earlier study](../2026-10-ko-clear-writing-eval/README.md)
into a personal Codex candidate. It does not register a new supported repository
product or modify a global writing policy. The frozen 0.1.0 candidate passed the
bounded acceptance gate and was installed at `~/.codex/skills/ko-technical-writing`.
All six installed files match the evaluated hashes. Start a new Codex conversation
to refresh discovery; the current desktop conversation was not used as an install
smoke. [Installation receipt](installation.json).

## What is being built

[ko-technical-writing](candidate/ko-technical-writing/SKILL.md) drafts technical
documents, runbooks, commit messages, PR descriptions and engineering handoffs from
evidence. Two references cover change messages and documents. The active model does
the work; there is no required extra model, hook or literal checker. Existing
source-text proofreading retains its separate scope.

The short candidate specifically distinguishes missing evidence from non-execution,
staged changes from working-tree context, committed PR scope from local edits, and
historical test results from validation of the present revision. It does not impose
an English controlled vocabulary or claim ASD-STE100 compliance.

## Evaluation contract

[protocol.json](protocol.json) freezes the candidate tree, competing editor,
[cases](cases.json), harness and acceptance criteria before generation. Eight new
synthetic cases compare ordinary execution with native skill availability; four
near misses test unwanted activation. Both arms can discover the existing Korean
editor. Task prompts do not name the candidate or paste its instructions.

[harness.py](harness.py) builds isolated Git fixtures and separate HOME/CODEX_HOME
directories. It disables memories and uses read-only execution. A staged retry
change coexists with an unstaged timeout; a committed PR coexists with local edits;
a staged gitlink is hidden by `diff.ignoreSubmodules=all`. The fixtures and expected
boundaries were checked offline before generation. No superpowers resources load.

The planned batch has 20 dispatches, with four held in reserve under a 24-call cap.
Each case has one repetition. Live invocations use the requested Astra/high model;
actual identity must come from each rollout's `turn_context`. Completion, identity,
commands, workspace hashes, latency and usage are retained in a private local run
directory. Auth copies are removed after every call.

The author reviews every output against the frozen invariants and observes actual
file reads. This is not an independent semantic review or a human comprehension
experiment. JSON shape and workspace integrity are checked deterministically.
All material candidate invariants, source scope, formats and the discovery gate must
pass before installation. A passing baseline blocks any quality-superiority claim.

## Reproduce

Offline planning only, no credentials needed:

```sh
/usr/bin/python3 docs/research/2026-10-personal-writing-pilot/harness.py /tmp/writing-pilot-dry-run
```

After separately authorizing live calls, use a new private output directory and add
`--execute --auth <path-to-codex-auth.json>`. The output ledger rejects duplicate job
IDs and more than 24 reserved dispatches within that directory. It is not an
account-wide billing guard. A new experiment needs its own authorization and frozen
record. Do not run against private work as an accidental substitute for the fixtures.

## Observed results and adoption

Twenty-one dispatches produced 20 answers. One initial casual near-miss request
failed with HTTP 503 / model capacity before generation. A single unchanged retry
used one reserved call and completed. The original failure remains in
[results.json](results.json); [followup.json](followup.json) records the retry.
No candidate text changed during or after generation.

All completed calls reported `gpt-6-astra` / `high` in rollout `turn_context`.
Runtime: Codex CLI 0.160.1 on macOS. Both JSON responses parsed with exact keys and
preserved null/false values. Every one of the 21 workspace snapshots was unchanged.

| Measure | Ordinary execution | Personal skill |
| --- | ---: | ---: |
| Material meaning, scope and format | 8/8 | 8/8 |
| Native entrypoint and relevant reference read | Not applicable | 8/8 |
| Unwanted activation on completed near misses | Not tested | 0/4 |
| Median positive-case duration | 26.26 s | 23.47 s |
| Total output characters, eight cases | 1,836 | 2,179 |
| Reported input tokens, eight cases | 213,336 | 301,675 |
| Reported cached input tokens | 106,112 | 187,776 |
| Reported output tokens | 1,775 | 3,367 |

Input and output usage include tool-turn overhead and host accounting; they are
not just final-response size or a bill. Concurrent execution and caching prevent
interpreting these medians as a stable latency improvement. Candidate answers were
longer in aggregate. The baseline also recovered the hidden gitlink and handled
missing verification evidence. **There is no demonstrated quality advantage.**

The decision is to install a focused personal pilot for the requested repeatable
workflow, not mandate it for every answer. Semantic grading is by the author,
against frozen material invariants; [grades.json](grades.json) preserves rationales.
It establishes a bounded usable candidate, not general reliability, superior prose
or human reading comprehension. Longer field use may justify simplifying or removing
it. No extra evaluation was run merely to turn a tie into a gain.

## Verification and audit limits

- Twelve fixture setups built under stock macOS Python 3.9.6. Staged/unstaged,
  committed/local, and hidden-gitlink boundaries were independently checked offline.
- Skill frontmatter validation passed for the candidate and installed copy.
- Research code compiled under Python 3.9.6; the harness dry run made zero calls.
- [summarize.py](summarize.py) verifies frozen hashes, unique dispatches, original
  prompts, response hashes, manual-grade coverage, runtime identities, JSON shape,
  and the acceptance gate while rebuilding public aggregates from the private
  archive. Its semantic inputs are author judgments, not a second model evaluation.
- The public-document suite passed 65 tests before final report updates; final
  link, diff and report checks are recorded in [verification](verification.md).

The compact CLI stream omitted the final failing compound shell command from one
baseline run even though the rollout contained its result, including the correct
gitlink diff. The author inspected **all rollout tool calls** before grading. Public
results distinguish stream command counts from rollout tool-call counts. The former
are not a complete execution audit. The command's later `git -C` probes failed
because the fixture intentionally contains a gitlink, not an initialized submodule;
this does not erase the valid diff in the earlier part of that command.

Only the candidate and existing Korean editor were added as user skills in isolated
homes. Other personal plugins, hosts, file-writing actions and production documents
were not tested. Read-only execution limits this study to drafting and evidence
retrieval; it is not an authorization-safety test under write permissions.

## Decision record

[Learning case](../../learning/cases/2026-10-09-personal-technical-writing.md)
records the personal scope, alternatives and final decision. The source attachment
and raw provider records remain outside Git. The candidate is freshly authored;
no private attachment text or raw model output is incorporated into its payload.
