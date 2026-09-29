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
  app check on real data, the fast check, and the no-spawn line in every brief
- `SKILL.md` under 140 lines

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
