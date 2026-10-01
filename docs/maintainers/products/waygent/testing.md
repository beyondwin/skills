# waygent testing

This document records what checks waygent. Every required check runs without provider
calls or credentials. An offline pass is not stretched into evidence of real model
quality or host execution.

The fixture path is `tests/products/waygent/`.

## Provider-free evidence

The required evidence is `python3 scripts/verify.py --skill waygent`. Its stages are
`product-contract`, `waygent-contract`, and `python-compile`.

`tests/products/waygent/test_contract.py` locks the following:

- `validate_product` passes, and frontmatter `name`, `license`, and `metadata.version`
  match `release.toml`
- the description's `/waygent` gate and its exclusion of nearby requests (`/sddx`,
  `subagent-driven-development`, brainstorming or spec, a single small fix)
- the `.waygent/` record location, `.gitignore` `*`, and the `Waygent-Task:` trailer
- no re-review, one final review, no commits to `main` or `master`, the same model and
  no cheaper model, and one tier up (`one tier up`) only for the final review and the retry
- the Codex rules: `$waygent` in the description, `fork_turns: "none"`, "do not guess
  your model name", and "no subagent spawns subagents of its own"
- the final-review blind spots (contract drift, failure paths, startup config), the
  app check on real data (stopping what it started), the fast check, the no-spawn line
  in every brief, and that a start or deploy gap is never outside the task
- the Grok rule (`spawn_subagent` with `run_in_background: false`, no `model`) and a
  Models line for every host in the registry
- the review rules: a ruling never cancels a High or Medium, a one-line reproduction
  per finding, and Lows go in the report
- resume and checks: a trailer commit with no `done` line, a clean tree, a failed check
  at step 3 or 5, and a red final suite handled as a failure
- the progress lines record `impl=<m/e>` and `reviewer=<m/e>`, `inherit` when unset,
  `reviewer=none` only when no reviewer ran;
  one review-status set (`clean|fixed K|overruled K|skipped (<why>)|unknown`) stated
  once; the `model:` header omits effort when none was set
- run scoping: resume starts on `$P/progress.md` or `/waygent` alone, done means a
  trailer commit in `start..HEAD`, step 3 searches `$BASE..HEAD`, the rebuild uses the
  upstream or remote default branch and asks when a task number repeats, and resume
  follows the recorded task order
- finished and several folders: `/waygent` alone picks the folder with no
  `final: done` or asks once, a finished folder starts nothing, and a `start` that is
  not an ancestor of HEAD stops the run
- the final phase: `final: start`, `Waygent-Task: final` commits, its resume rule (a
  `Waygent-Task: final` commit in `start..HEAD` goes to the full suite run), and
  `impl=` on the `final: done` line; a retry line `task N: retry impl=<m/e>`
- one subagent at a time, reviewers included; the Claude Code line
  (`run_in_background: false` when offered, end the turn on a background dispatch,
  re-dispatch a lost subagent fresh, prefer a fresh implementer over SendMessage) and
  the Codex `wait_agent` line with a long timeout
- `guide.md`: test, lint, and build or typecheck commands, the build step in the fast
  check, `app: <how to start>` or `app: none (<why>)`, generated paths in
  `.git/info/exclude`, at most ~60 lines, global rules verbatim only if they fit, traps
  appended later; the brief at most ~2,000 characters; `walk=<ok|none (<why>)>`
- limits: a subagent's transient 429 is redispatched once, the controller's own usage
  limit appends `paused: limit`; the reviewer asks carry a pasted stop line
- `SKILL.md` under 165 lines

`validate_product` also checks that `agents/openai.yaml` sets
`allow_implicit_invocation: false`.

The checks look at a few phrases only. `SKILL.md` is still changing, so no digest or
full sentence is pinned.

## Commands

```bash
python3 scripts/verify.py --skill waygent
python3 -m unittest discover -s tests/products/waygent -p 'test_*.py'
```

## Live measurement

Live measurement is not part of the default verification. The tasks, hidden tests, and
driver are in [waygent design and evaluation](../../../research/2026-09-waygent-eval/README.md),
and per-host records go in [compatibility](compatibility.md). When the installed
files' behavior rules change, measure again with that harness.

The harness drives `claude -p`, where controllers set `run_in_background: false` and
every dispatch returns inline. Interactive Claude Code sessions may not offer that
flag, and then every dispatch returns in the background. The harness has not measured
that mode, the one-subagent-at-a-time wait in it, a resume inside the final phase, or
two runs on one branch; these need an interactive or purpose-built run. The harness
also runs without `--effort`, so its Claude Code controllers and same-model subagents
ran at medium effort.
