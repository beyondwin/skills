# api-guide testing

Activation is explicit-only. No live run of the current payload has been made; host
behavior and page quality are `not_measured`.

## Provider-free evidence

The required evidence is `python3 scripts/verify.py --skill api-guide`.
`tests/products/api-guide/test_contract.py` checks:

- frontmatter: name, explicit-only invocation, the "Use when" and "Do not use for"
  description, and the Artifact tool requirement
- every reference named in `SKILL.md` exists
- the page skeleton and card order in `SKILL.md`
- the Verify rules that came from the first real use
- the consumer reference keeps file paths and line numbers off the page
- `references/page.html` sections and card blocks follow the skeleton, the dark theme
  tokens exist, it has no script, and it uses only the invented `/api/v1/exports` API

These prove file shape only. They do not prove that a run reads the code correctly or
that a published page is accurate.

## Live runs

None yet. A useful first run is a scope the author did not see while writing the skill,
checked by a developer who knows that server, with the result recorded here.
