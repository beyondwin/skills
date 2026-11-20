# api-guide testing

Activation is explicit-only. One headless live run is recorded below; artifact publishing
and page quality beyond spot checks are `not_measured`.

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

### 2026-11-20, headless Claude Code, opus

- Scope: one endpoint added that day in a private server repository, app developers as
  readers, with the app repository for the to-do section. Not the scope the skill was
  written from. Server and app contents stay out of this repository.
- Launch: `claude -p "/api-guide ..." --permission-mode bypassPermissions --model opus` with
  user settings, so the linked skill loaded. 46 tool calls, about 11 minutes.
- The skill loaded and followed the steps: pinned both commits, read code rather than the
  contract file, wrote the to-do section at behavior level, and reported four gaps between
  the contract file and the code.
- The session had no Artifact tool; it saved an HTML file. `SKILL.md` now says so.
- Spot checks by the maintainer against the code: three claims held (a 403 code that cannot
  fire, a limit shared by two kinds of rows, a 500 without the envelope). The 403 finding
  also corrected an earlier hand-written guide.
- Not measured: artifact publishing, a full review of the page by someone who owns the
  server, other hosts.
