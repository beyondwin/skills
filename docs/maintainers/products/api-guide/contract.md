# api-guide contract

This document sets api-guide's activation, inputs, page shape, checks, and the files that
change together. When behavior changes, update `SKILL.md`, its references, the tests in
`tests/products/api-guide/`, and both product READMEs in the same change.

## Activation

Only `/api-guide` in Claude Code activates the skill (`disable-model-invocation: true`).
Codex is not a supported host; `agents/openai.yaml` exists because every payload carries
one, and it keeps implicit invocation off.

## Inputs

Scope, reader, optional consumer repository, optional existing artifact URL, and
language. The default scope is the current branch against its merge base with the default
branch. A missing slot that would change the page gets one question.

## Output

One page published as a Claude artifact, plus a short chat report.

- `SKILL.md` "Page skeleton" owns the section order and the card order (Request,
  Response, Errors, Handling). `references/page.html` follows the same order, and a test
  keeps the two aligned.
- `references/page.html` is the visual template. Its API is invented; a test rejects any
  `/api/` path other than the template's own.
- The page contract (title, theme tokens, allowed hosts for scripts and fonts) belongs to
  the host's artifact design skill. The template follows it and does not restate it.
- Server facts are read from code at a recorded commit (`references/facts.md`).
  Contract files are a map, not the source.
- The to-do section exists only with a consumer repository and stays at behavior level:
  no consumer file paths, line numbers, or class names (`references/consumer.md`).

## Checks before publishing

`SKILL.md` "Verify" lists them: a code location for every fact, a counterexample search
before any universal claim, per-card definitions for shared field names, appendix and
examples agreeing with field tables, per-endpoint error tables from throw sites, config
defaults named as defaults, and examples labeled captured or composed.

## Safety

The payload carries no company or product data. Pages the skill writes may contain the
user's private API facts; they are published private and shared only by the user.
