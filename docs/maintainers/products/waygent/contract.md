# waygent contract

This document is the normative contract for what waygent owns, when it turns on, and
how it runs tasks. The runtime source is `skills/waygent/SKILL.md`; this document
records only the promises that tests lock. Before changing behavior, check this
document and "Files to change together" at the end.

## Terms

| Term | Meaning |
| --- | --- |
| Host | The program that runs the skill: `claude-code`, `codex`, `cursor` (Cursor Agent), or `grok` (Grok Build). |
| Controller | The host session that received `/waygent` or `$waygent`. It writes no code; it dispatches tasks, checks them, and writes the progress file. |
| Implementer subagent | A fresh subagent that owns one task. |
| Guide file | `guide.md`. Commands and plan-wide rules, written once and read by every implementer subagent. |
| Progress file | `progress.md`. Per-task status. Never committed. |
| Review records | The `reviews/` files. Each reviewer writes its own findings there. The controller may also keep helper files under the same folder; nothing goes outside it. |

## Product identity

The product ID, skill `name`, and directory name are `waygent`. The display name is
`Waygent`. The call is `/waygent [plan-file|request]` (Codex: `$waygent [plan-file|request]`).
It does not turn on unless the message contains `/waygent` or `$waygent`.
`agents/openai.yaml` sets `allow_implicit_invocation: false`.

The description must say that it turns on with `/waygent` or `$waygent` and that it
excludes nearby requests (`/sddx`, Superpowers `subagent-driven-development`,
brainstorming, writing a spec or plan, a single small fix).

## Execution promises

- State lives under `.waygent/<plan-slug>/` at the repository top level, in
  `progress.md`, `guide.md`, `reviews/`, and any helper files the controller needs.
  `.waygent/.gitignore` (`*`) keeps it out of commits, and the user's `.gitignore` is
  not edited.
- Resume is scoped to one run. It starts when `$P/progress.md` exists or on `/waygent`
  alone; trailer commits on the branch alone never start it. `/waygent` alone resumes
  the one folder whose progress has no `final: done`, asks once when there are several,
  and rebuilds from the branch's trailers when there is no folder. The rebuild takes
  `start` from the merge-base with the branch's upstream or the remote default branch,
  else `main`/`master`, and asks which run when a `Waygent-Task: N` repeats in that
  range. A folder with `final: done` is finished: it is reported and nothing starts.
  If `start` is not an ancestor of HEAD, the run stops and says the history changed.
- One subagent at a time, reviewers included: the controller waits for each to report
  before the next dispatch or message. On Claude Code it sets `run_in_background:
  false` when the Agent tool offers it; a dispatch that still returns in the background
  ends the turn with only that dispatch outstanding, and a subagent lost with the
  session is re-dispatched fresh. On Codex it waits with `wait_agent` and a long timeout.
- Write the test first, watch it fail, then implement (TDD).
- The last commit of each task carries a `Waygent-Task: N` trailer. On resume, only
  tasks with a trailer commit in `start..HEAD` count as done, and resume continues at
  the next task in the recorded order. A task with its commit but no `done` line
  resumes at its review or fix, not as done.
- After each task the controller checks that the trailer commit is in `BASE..HEAD`,
  the tree is clean, and the fast check passes. A failed check goes through the
  failure path. A retry appends `task N: retry impl=<m/e>`.
- One review per task and one fix, with no re-review. Each finding comes with a
  one-line reproduction. A ruling never cancels a High or Medium: the controller may
  overrule one only after running its reproduction.
- Low findings are recorded and passed to the final review; they are not fixed in the
  final batch.
- `progress.md` records who did each step as `model/effort` (`impl=`, `reviewer=`):
  the values the controller set in the dispatch, `inherit` for any it left unset;
  a dispatch by agent type records the definition's values (`reviewer=opus/xhigh`).
  Values are never guessed; `reviewer=none` only when no reviewer ran (a skipped
  review). The `model:` header holds the session's model and its
  effort as set, else the model alone. Review status uses one set of values:
  `clean`, `fixed K`, `overruled K`, `skipped (<why>)`, `unknown`.
- One final review of the whole change, only once. It also asks for contract drift
  between layers, money and counts on failure paths, startup config and deploy order,
  and queries at real scale. After its fixes, unless `guide.md` says `app: none
  (<why>)`, one implementer walks the changed flows on real data and fixes what it
  finds in the same batch, with no second review. The phase opens with `final: start`;
  its commits carry `Waygent-Task: final`; the closing line records `impl=`,
  `reviewer=`, and `walk=<ok|none (<why>)>`. A resume after `final: start` with no
  `final: done` goes to the full suite run when a `Waygent-Task: final` commit is in
  `start..HEAD`, else to the fixes when `reviews/final.md` exists, else to the review.
- `guide.md` (about 60 lines at most) lists the test, lint, and build or typecheck
  commands and splits a fast check from slow suites; the fast check includes the build
  step when the repo has one. The controller reruns only the fast check after each
  task, and the full suite once at the end. `guide.md` holds `app: <how to start>` or
  `app: none (<why>)`, names generated paths to exclude locally, and gets traps found
  later appended.
- Reviewer asks carry a quoted line the controller pastes: spawn nothing, stop every
  process started, leave the tree as found, write the full review to its path, reply
  only High / Medium / Low. A tree left dirty by a reviewer is stashed (recoverable) before the fix.
- A task may take several commits; only its last carries the trailer.
- A gap that keeps the changed code from starting or deploying is fixed inside the
  task, never left as a note for the user. Implementers start the app only when their
  task changes how it starts. The app check stops what it started.
- A red full suite after the final fixes goes through the failure path too.
- No subagent spawns subagents or leaves a process it started running; every brief,
  reviewers' included, says so.
- On failure, write down the cause first and retry once. Stop on the second failure.
  A subagent's transient 429 is redispatched once; the controller's own usage limit
  appends `paused: limit` and stops.
- Implementer subagents and per-task reviewers use the controller's model. Do not swap
  in a cheaper model or lower effort. When the host can pick models, only the final
  reviewer and the post-failure retry implementer use a model one tier up. On Codex, no
  model name is written, so children inherit the session model; one tier up sets only
  `reasoning_effort` to `xhigh`. On Claude Code the final reviewer is the
  `waygent-final-reviewer` agent definition (`agents/waygent-final-reviewer.md`: opus,
  effort xhigh) when the Agent tool offers that type and the controller runs below opus at
  xhigh; it is dispatched with no `model`, since a per-dispatch model overrides the
  definition's. Without the type the final reviewer goes one tier up by model as before.
  The definition is installed by an optional link into `~/.claude/agents/`, because a
  skill cannot define agents and the Agent tool takes no effort. This is because in the 2026-09-27 measurement the Codex
  controller misidentified its own model and wrote a different one. On Grok Build
  (`spawn_subagent`) and Cursor Agent (`Task`) no model is named, so children use the
  session model. Every registry host has its own line in the Models section.
- Do not commit to `main` or `master`. Do not push, merge, or open a PR unless asked.
- `SKILL.md` stays under 170 lines. Lightness is part of the contract.

## Deliberately left out

Brainstorming, spec, and design stages; per-task brief, diff, and report files (the
reviewers' `reviews/` files and the controller's own helper files under the plan folder
are the only extra files); re-review loops; parallel subagents and worktree pools;
human confirmation on every task. The basis
for these choices is the harness comparison in [`docs/research/`](../../../research/README.md)
and the finished evaluation in
[waygent design and evaluation](../../../research/2026-09-waygent-eval/README.md).

## Files to change together

- `sddx` reads `skills/waygent/SKILL.md` as its base loop and names its sections
  `Start or resume`, `Per task`, `When a task fails`, `Final review, once`, and
  `Models`, plus `.waygent/`, `guide.md`, and the `Waygent-Task:` trailer. Renaming
  any of them breaks sddx; `tests/products/sddx/test_contract.py` checks they exist.
  sddx also quotes the implementer brief's test-first and trailer paragraph verbatim
  (`skills/sddx/references/dispatch.md`), copies the progress line formats, and refers
  to waygent's per-task step numbers ("waygent step 3"), so keep those stable too.
- `skills/waygent/SKILL.md`, `release.toml`, `CHANGELOG.md`, `README.md`, `README.ko.md`
- `skills/waygent/agents/waygent-final-reviewer.md`, its link line (marker
  `<!-- waygent-agent-link -->`, a copy of `tests/products/waygent/fixtures/link-agent.py`)
  in both READMEs and both `docs/users/*/install-local.md`,
  and the `CLAUDE.md` tier line
- `tests/products/waygent/test_contract.py`
- `testing.md`, `compatibility.md`, and `release.md` in this directory
- When hosts change: `products.toml`, the shared compatibility docs, and repository tests
