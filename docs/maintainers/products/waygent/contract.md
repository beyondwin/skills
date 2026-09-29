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
| Review records | The `reviews/` files. Each reviewer writes its own findings there; they are the only extra files beyond the progress and guide files. |

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
  `progress.md`, `guide.md`, and `reviews/`. `.waygent/.gitignore` (`*`) keeps it out
  of commits, and the user's `.gitignore` is not edited. If the progress file is
  missing, it is rebuilt from the trailer commits.
- One fresh implementer subagent per task. Never two at once.
- Write the test first, watch it fail, then implement (TDD).
- The last commit of each task carries a `Waygent-Task: N` trailer. On resume, only
  tasks with a trailer commit reachable from HEAD count as done, and the progress file
  is brought in line with that.
- One review per task and one fix, with no re-review.
- One final review of the whole change, only once. It also asks for contract drift
  between layers, money and counts on failure paths, startup config and deploy order,
  and queries at real scale. After its fixes, when `guide.md` says how to start the
  app, one implementer walks the changed flows on real data and fixes what it finds in
  the same batch, with no second review.
- `guide.md` splits a fast check from slow suites; the controller reruns only the fast
  check after each task, and the full suite once at the end.
- A task may take several commits; only its last carries the trailer.
- A gap that keeps the changed code from starting or deploying is fixed inside the
  task, never left as a note for the user. The app check stops what it started.
- No subagent spawns subagents or leaves a process it started running; every brief,
  reviewers' included, says so.
- On failure, write down the cause first and retry once. Stop on the second failure.
- Implementer subagents and per-task reviewers use the controller's model. Do not swap
  in a cheaper model or lower effort. When the host can pick models, only the final
  reviewer and the post-failure retry implementer use a model one tier up. On Codex, no
  model name is written, so children inherit the session model; one tier up sets only
  `reasoning_effort` to `xhigh`. This is because in the 2026-09-27 measurement the Codex
  controller misidentified its own model and wrote a different one.
- Do not commit to `main` or `master`. Do not push, merge, or open a PR unless asked.
- `SKILL.md` stays under 140 lines. Lightness is part of the contract.

## Deliberately left out

Brainstorming, spec, and design stages; per-task brief, diff, and report files (the
reviewers' own `reviews/` files are the only extra files); re-review loops; parallel
implementer subagents and worktree pools; human confirmation on every task. The basis
for these choices is the harness comparison in [`docs/research/`](../../../research/README.md)
and the finished evaluation in
[waygent design and evaluation](../../../research/2026-09-waygent-eval/README.md).

## Files to change together

- `sddx` reads `skills/waygent/SKILL.md` as its base loop and names its sections
  `Start or resume`, `Per task`, `When a task fails`, `Final review, once`, and
  `Models`, plus `.waygent/`, `guide.md`, and the `Waygent-Task:` trailer. Renaming
  any of them breaks sddx; `tests/products/sddx/test_contract.py` checks they exist.
- `skills/waygent/SKILL.md`, `release.toml`, `CHANGELOG.md`, `README.md`, `README.ko.md`
- `tests/products/waygent/test_contract.py`
- `testing.md`, `compatibility.md`, and `release.md` in this directory
- When hosts change: `products.toml`, the shared compatibility docs, and repository tests
