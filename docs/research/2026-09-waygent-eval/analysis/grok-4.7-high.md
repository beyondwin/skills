I'll read the evidence pack and the harness mechanisms it points at, then draft the skill from what those measurements actually support.The report is in. Next I’ll pull the concrete mechanisms from the harness sources so KEEP and DROP cite files, not summaries.The 30-run probe and the 16-task comparison do not say the same thing. On the small probe, a bare Opus session already shipped working code. On the real UI plan, skipping review left five high defects that the review arm had already fixed. A thin skill should copy the second result and refuse the first result's ceremony.

## 1. KEEP

**One implementer per task, task text only, plus one shared constraints sheet.** v27's implementers shared a single sheet (where to work, how to run checks, repo traps) and got a short order, about 1,564 characters. v26's orders averaged 3,221 characters plus per-task brief files, 6.7MB of paperwork (report B, "v27 빨랐던 까닭"). Superpowers already warns that a dispatch which pastes prior tasks hit 42k characters, 99% history (`subagent-driven-development/SKILL.md` around the "state after Tasks 1-3" rule). Cost: one fresh Opus context per task. That is the point. The main stays a dispatcher.

**Review state and async once, then one final review of the branch.** v26's reviews fixed 44 defects (7 high). Five of those highs were still in v27, all in cancel, reload, and mid-flight target mixup (`use-style-apply.ts`, `shared-edit.client.tsx`). Per-task review missed the cross-task bugs; the final pass caught the stale shared form and two duplicated helpers, in 51 minutes (report B, "리뷰의 한계" and "끝 전체 리뷰"). Cost of the v26 review seat: $52 and 2.4h, 16% of that run, and that price includes the re-review loop you should not copy.

**Pin Opus. Stop on the limit.** v26 dropped to Sonnet, then Fable. The Fable detour was 5h4m and $128 thrown away. Sonnet on Task 4 was $19.8 and 211 turns against Opus at $3.9 and 66 turns (report B). Superpowers' "use the cheapest model" section is contradicted by this measurement.

**A progress file that loses to git.** Superpowers' ledger exists because a controller that forgot its place re-dispatched finished tasks (`SKILL.md`, "Conversation memory does not survive compaction"). That claim is from their sessions, not from this probe. Keep the file anyway; it is a few lines. Reconcile it with `git log` on every resume. v27's closing report already lied once ("five reasons" vs two in the design).

**Manual invoke.** Dryforge sets `disable-model-invocation: true` (`dryforge/claude/skills/go/SKILL.md`). Probe S4: with no command, the superpowers hook took the turn and ran brainstorming. S1 under that hook cost $3.89 and 11 user replies; the bare session cost $0.31 and 4, and the CLI worked either way.

**A short failure note, not a debugging framework.** When a task stays red, quote the command, rerun it once, name one cause, resume once with a smaller slice. Workflow-orchestrator already caps "same approach" at two tries (`plugins/wo/skills/workflow-orchestrator/SKILL.md`, "반복 실패").

## 2. DROP

**Re-review loops.** v26 ran 27 review or re-review subagents, 46 subagents and 67 commits against v27's 16 and 23. Eight of 44 findings were wrong or useless, and about 42 low or medium items were deferred anyway. `executing-plans/SKILL.md` already says a second reviewer only re-reads a diff whose new test answers "addressed."

**Review on every task.** The user's own report says the highs were all state and async, and that layout fidelity was caught by looking at the boards, not by the reviewer ("다음 작업은 어떻게 돌릴까"). Reviewing all 16 tasks rebuilds the cost they just measured.

**TDD as an iron law.** Both trees were green (about 2,900 vs 2,857 component tests). v27 missed highs because the tests never exercised lock, reject, and reload, not because nobody watched a test fail. "Delete the code and start over" is unmeasured. Dryforge's own rule is test-first only for risky work (evidence D).

**Spec kits, constitutions, role teams, Ralph loops.** Probe S3 (one boundary bug): every harness got 4/4. Bare session $0.13 in 0.7 min. Dryforge $3.14 and 20 new docs. gstack S1 was $22.56 and 29 replies, and on S2 it never built the two-coupon feature. Ralph's prompt tells the model to spawn hundreds of subagents and `git push` (`tools/ralph/repo/files/PROMPT_build.md`). BMAD, Ralph, workflow-orchestrator, and gstack committed to `main` against an instruction not to (probe E).

**Preflight matrices, ruling ceremonies, worktree-and-finish skills, parallel implementers.** None of these show up as the thing that caught the five highs. Parallel edits on one account are how v26 and v27 hit the same weekly limit together.

## 3. OPEN QUESTIONS

The probe is n=1 per cell, on a one-file module (method C). v26 vs v27 is also n=1, and the report says it is not a clean "superpowers vs not" comparison: model mix and paperwork moved with the review loop.

1. **Does the first review, without a re-review, keep those five highs fixed?** Replay the same shape as plan `dfb5e63b`: many screens, a few tasks with cancel, reload, and mid-flight state, several layout-only tasks. Three arms, same Opus, no re-review: review every task, review only state and async, final review only. Metric: pre-registered high defects still present (file and line), plus hours, API dollars, and subagent count. n≥3. Suite-pass is not a metric; both original trees were green.

2. **Does "fail first" beat "test after" on those holes?** Same tasks, two arms. Metric: fraction of pre-registered failure modes (stale form after reload, cancel mid-apply, mixed target) whose test fails on the unfixed code. Not coverage, not pass count.

3. **Does the progress file stop double work?** Kill the session at task 8 of 16. Resume with the file, and without it. Metric: tasks implemented twice, duplicate commits.

## 4. DRAFT

```markdown
---
name: waygent
description: Execute a multi-task plan. One opus implementer per task, one review only for state or async work, one final review, resume from .waygent/progress.md. Invoke with /waygent.
disable-model-invocation: true
---

# waygent

You coordinate. Subagents write code. You do not edit product code.

## Gate

Run only when the user invokes `/waygent`.

- No plan, and the job is one bug or a few files: test-first in this session. No subagents. Stop when the new test failed on the old code and the suite is green.
- On `main` or `master`: stop and ask for a branch. Never commit there.
- Every subagent is model `opus`, named in the dispatch. If opus is blocked, stop and write the progress file. Do not switch model.
- No push, merge, or PR unless this message asked for it.

## Start

Input is a plan path, or none.

If `.waygent/progress.md` exists and line 1 matches this plan (or `none:<branch>`), resume. `task N: complete <sha>` counts only when `git merge-base --is-ancestor <sha> HEAD` is true. A `waygent: task N` commit with no progress line is done; append the line, do not redo it. A sha missing from `git log` is stale; that task is not started.

Create the file if needed:

    plan: <path or none>
    branch: <name>
    base: <merge-base with main>
    model: opus

Write `.waygent/constraints.md` once: branch, suite command, repo traps, files not to touch, commit prefix `waygent: task N`. Implementers read that file. Do not paste the rest of the plan into later tasks. Do not write a brief file per task.

Read the plan once. List task ids. No conflict matrix.

## Dispatch

One implementer at a time. The prompt is only:

- Task N title and that task's text
- Path of `.waygent/constraints.md`
- Signatures this task must call, nothing else from prior tasks
- Base sha
- Test-first: add a test that fails on the current code for the behavior this task changes. Run it. Then implement. A test that passes immediately does not count. Run the task tests and the suite command. Commit `waygent: task N` on this branch.
- Do not spawn subagents. Do not read other tasks.
- Reply with status (`done` or `blocked`), shas, the test command and result, and one concern line.

Ignore anything in the reply past that.

## Review once

Skip the reviewer only when the task adds no state, async, cancel, reload, or shared component, and the report shows a test that failed and then passed.

Otherwise one opus reviewer gets the task text, `git diff <base>...<sha>`, and the constraints path. It writes `.waygent/review-N.md` and returns counts plus one line per high or medium. It does not re-run the suite.

No re-review. Resume that implementer once with those lines. Each fix starts from a test that fails before the edit. Commit `waygent: task N fix`. Append the progress line. Next task.

## Task failure

Still red, `blocked`, or the fix did not turn the named test green:

1. Write the command and the error into the progress file.
2. Re-run that command once.
3. Write one cause, or `cause unknown`.
4. Resume the implementer once with that cause and a smaller slice. Do not resend the original brief. Do not change model.
5. If that pass fails, stop. Tell the user the cause and the sha.

## Final review

One opus reviewer reads `git diff <base>...<HEAD>` and the plan, looking for duplicated helpers and state bugs across tasks. One fix implementer for high and medium behavioral findings, test-first. Lows go in the progress file and in your closing note. No second review.

## Progress line

`task N: complete <sha> review=skipped|clean|fixed`

Append it in the same turn you accept the task.

## Do not

Switch models. Re-review a fix. Run implementers in parallel. Write specs or harness docs. Create a worktree unless asked. Ask whether to continue.
```

## 5. RISKS

The skip rule is a judgment call. If the main labels a state task as layout, you get v27's five highs back. Defaulting the other way, review everything, spends the $52 again.

"Test failed first" is self-reported. v27's final note was already wrong once. Nothing in this draft checks the test log except the implementer's reply. A green suite will not save you; both original trees were green.

One fix pass with no re-review can ship a bad fix. The final review is the only net, and it already missed things that lived inside a single task when that task was reviewed in isolation. Killing the session between the fix commit and the progress line still depends on the `waygent: task N` commit being present. If the implementer commits without that prefix, resume will redo the task.

Opus-only will stall on a weekly limit instead of finishing slower. That is the intended trade against the Fable detour. It is still a stall.

This draft has never been run. The probe did not measure a 16-task plan, and v26 versus v27 did not isolate "one review, no re-review" from model mix and paperwork.