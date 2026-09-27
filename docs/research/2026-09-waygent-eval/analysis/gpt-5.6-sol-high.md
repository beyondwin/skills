## 1. KEEP

- **Fresh implementer per task with a narrow brief.** v27 used 16 implementers, short prompts, and one shared instruction sheet; it cost $207 versus $331 and finished 16% faster than v26. The Superpowers brief mechanism also prevents accumulated-history bloat ([evidence.md §B](<evidence-pack>/evidence.md:6); `subagent-driven-development/SKILL.md:248-279`). Cost: one cold context per task and some repeated repository discovery.

- **TDD for behavioral changes and bugs.** Every S3 run found the bug and added a regression test, but v26/v27 also prove that green suites do not imply good coverage: five high-severity v27 defects survived. Require observed RED→GREEN, not “tests added.” Cost: test-writing and suite runtime.

- **One selective task review.** v26 reviews found 44 defects, including seven high-severity ones; five of those remained in v27. All high defects clustered around state, async, cancellation, reload, and ordering. Cost: measured $52 and 2.4 hours—15–16%—so reviewing every mechanical task is not justified.

- **One whole-change review.** Only the final review found cross-task stale state and duplicate components/helpers; it cost about $16 and 51 minutes. Cost is one fresh whole-branch context.

- **Durable progress reconciled with Git.** Superpowers’ ledger records task commit ranges and trusts `git log` after compaction (`executing-plans/SKILL.md:116-137`). Ralph similarly carries state through `IMPLEMENTATION_PLAN.md`. Cost: a few concise records per task.

- **Explicit strong-model pinning.** The v26 fallback wasted five hours and $128; Sonnet sometimes used 2–3× more turns and cost more. Cost: execution stops when the pinned model is unavailable.

## 2. DROP

- **Re-review loops.** v26 launched 27 review/re-review agents. Fix once, verify with a reproducing test, and move on.
- **Mandatory review of trivial diffs.** Visual fidelity was caught better by v27’s direct comparison than by reviewers. Skip review for deterministic mechanical, documentation, generated, or visually verified changes.
- **Spec pipelines, personas, approval checkpoints, and repository scaffolding.** In probe S3, baseline cost $0.13/0.7 minutes; Dryforge cost $3.14/8.6 minutes and created 20 files; Spec Kit/OpenSpec left 4–5 specification files ([evidence.md §E, S3](<evidence-pack>/evidence.md:487)).
- **Automatic model downgrades, parallel implementers in one checkout, automatic push/merge/PR, and nested subagents.** The report observed expensive fallback, shared-resource contention, 130-file merge conflict potential, and several probe harnesses violating Git intent.

## 3. OPEN QUESTIONS

- **Which tasks deserve review?** Run ten repetitions of a 12-task benchmark containing four async/state, four API/data, and four mechanical/UI tasks. Compare review-all, risk-selected, and final-only using escaped weighted defects, dollars, and elapsed time.
- **Does the ledger actually improve recovery?** On a two-day, 15-task repository change, force termination during tasks 4, 9, and final review. Measure resume latency, duplicated edits/tokens, lost decisions, and incorrect “complete” tasks.
- **Does strict TDD beat test-after with current models?** Use paired bug and feature tasks with hidden boundary, mutation, race, and compatibility checks. Measure escaped defects and total tokens—not test count.

## 4. DRAFT

```markdown
---
name: waygent
description: Execute multi-task coding work with narrow implementer contexts, TDD, bounded review, and interruption recovery.
disable-model-invocation: true
---

# Waygent

Run only when the user explicitly invokes `/waygent`.
This is an execution wrapper, not a planning framework.

## Input

Accept either a plan-file path or the user's request.
If given a plan, treat it as authoritative and extract its tasks.
Otherwise inspect the repository and derive the smallest executable task list.
Ask only about an ambiguity that materially changes the result.

Use the explicitly configured model for every implementer and reviewer.
Default to `opus`. Never silently downgrade or omit the model argument.
If unavailable, record the stop and return control to the user.

## Setup and recovery

Resolve the progress file with:
`git rev-parse --git-path waygent/progress.md`.

Record:
- request or plan identity and start commit
- current branch and user Git constraints
- tasks and dependencies
- per task: status, base/head, changed files, test evidence, review result
- rulings, failures, and final-review status

On start or resume, inspect `git status`, `git log`, and recorded SHAs.
Git is authoritative for committed state; progress is authoritative for intent.
If progress says complete but its commit is absent, reopen the task.
If Git contains unrecorded work, inspect its diff and tests before repairing
progress; never redo or discard it blindly.

Preserve existing changes. Do not reset, clean, stash, switch branches,
create worktrees, commit, push, merge, or open a PR unless authorized.
When commits are authorized, prefer one coherent commit per task.
Otherwise record changed files and `git diff --stat`.

## Task loop

Run implementation tasks serially. Give each fresh implementer only:

- objective and acceptance criteria
- allowed scope/files and working directory
- required interfaces and decisions from earlier tasks
- focused and relevant-suite test commands
- base SHA and Git constraints
- report contract: status, changes, RED/GREEN evidence, tests, concerns

Never send the full conversation or unrelated task history.
The implementer must not spawn subagents.

For behavior changes, use TDD:
1. add one meaningful failing test and observe the expected failure;
2. implement the minimum change;
3. observe the focused test pass;
4. refactor while green and run the relevant suite.

A bug fix requires a regression test.
Docs, generated files, pure configuration, or presentation-only changes may
replace TDD with a concrete validation; record why RED was inapplicable.
Passing tests are insufficient if they do not exercise the claimed behavior.

## Failure analysis

When implementation or verification fails, do not blind-retry.
Record the exact command, error, reproduction, recent diff, and last good SHA.
Have the implementer state one root-cause hypothesis and test it minimally.
Allow one corrected attempt. If it still fails, split the task, supply missing
context, or stop with the evidence; do not change models silently.

## Task review

Review a completed behavioral task exactly once using a fresh reviewer.
Give it the task brief, implementer report, and `base..head` diff.
Ask for requirement gaps, behavioral defects, error handling, and test quality.

Skip task review only for documentation/generated changes, deterministic
mechanical edits, or presentation-only work with direct rendered/fidelity
evidence, and only when there is no state, async, persistence, API, security,
concurrency, or compatibility risk. Record the skip reason.

Send all accepted findings back in one fix batch. Fix with tests and run the
relevant suite. Do not re-review the fixes.

## Final review

After all tasks, dispatch one fresh full review over start commit through HEAD.
Check cross-task behavior, interfaces, duplication, stale state, missing
requirements, and tests that claim more than they measure.

Apply important findings in one fix batch with regression tests, then run the
full applicable verification once. Do not dispatch another review.
Report unresolved findings honestly.

Update progress after every task, failure, fix batch, and final verification.
Finish with changed commits/files, commands and results, skipped reviews,
rulings, unresolved risks, and whether external validation remains.
```

## 5. RISKS

The skip rule can be gamed by misclassifying risky work as “mechanical.” One-shot fixes can leave reviewer findings incorrectly addressed. Serial agents may rediscover substantial context. Git-less or heavily dirty repositories weaken resume reconciliation. Finally, `opus` is an alias rather than an immutable model version unless the host supports version pinning.