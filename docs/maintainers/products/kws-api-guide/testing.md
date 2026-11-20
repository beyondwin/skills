# kws-api-guide testing

Activation is explicit-only. Three headless live runs are recorded below; artifact publishing
and page quality beyond spot checks are `not_measured`.

## Provider-free evidence

The required evidence is `python3 scripts/verify.py --skill kws-api-guide`.
`tests/products/kws-api-guide/test_contract.py` checks:

- frontmatter: name, explicit-only invocation, the "Use when" and "Do not use for"
  description, and the Artifact tool requirement
- every reference named in `SKILL.md` exists
- the page skeleton and card order in `SKILL.md`
- Common rules split into Handle in code and Formats, in `SKILL.md` and the template
- `references/writing.md` keeps the measured rules, and Verify rereads the page against it
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
- Launch: `claude -p "/kws-api-guide ..." --permission-mode bypassPermissions --model opus` with
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

### 2026-11-20, headless Claude Code, opus high, writing rules

- Same scope and reader as the first run. The server and app commits were pinned by SHA
  in the prompt instead of "origin/dev" and "latest main", so a fetch could not move the
  scope. Fresh clones at a fixed path. User settings, as in the first run, so the linked
  skill loaded. Skill file list SHA-256 starts `93a09f018f4c4af6`. One example row in
  `references/writing.md` was replaced after the run, so the current text differs from it.
- Transcript: `claude-opus-5-5`, effort `high`. 58 tool calls in the main session and 70 in
  two subagents, about 7 minutes, `total_cost_usd` 12.65. The first run's cost was not
  recorded.
- The run read `references/writing.md` and wrote Common rules as two tables.
- Facts, within what was compared: the set of paths and upper-case codes (28) and of field
  names (21) matched the first run's. The three spot-checked claims held, as did the limit
  range and default, ordering, and date rules. The page was not re-checked against the
  code in full.
- The server repository's style file loaded in both runs. It bans decorative symbols, not
  ASCII parentheses, so it does not explain the drop in parentheticals.
- Counts, first run → this run: table cells with three or more sentences 11 → 0 (of about
  80), parentheticals 24 → 0, skill words copied onto the page 6 → 0, hedged "can be"
  endings 4 → 0, lede sentences 4 → 3, plain-form endings in table cells 6 (some false hits
  of the counter) → 0 on reading. Korean characters 2,853 → 2,568.
- The chat report came back in English for a Korean prompt; the first run answered in
  Korean. One run cannot say why.
- n=1 against one earlier run. It does not separate the rules from run-to-run variance.

### 2026-11-20, headless Claude Code, opus high, language rule

- Same scope, Korean prompt, pinned commits, fresh clones, and launch as the run above.
  Skill at commit `dac5510`; skill file list SHA-256 starts `d38327ec9ba33b60`.
- Transcript: `claude-opus-5-5`, effort `high`. 55 tool calls in the main session and 26 in
  subagents, about 12 minutes, `total_cost_usd` 7.79.
- Language: the final report and 10 of 11 progress updates were Korean. One short update
  after a failed script edit was English.
- Facts, within what was compared: field names (21) matched both earlier pages; paths and
  codes matched except that this page left out a related retry endpoint the earlier pages
  mentioned, and added the detail endpoints. The three spot-checked claims, the limit range
  and default, ordering, and date rules held.
- Counts: table cells with three or more sentences 1 (of about 100), parentheticals 3, skill
  words copied onto the page 0, hedged "can be" endings 0, lede 3 sentences, plain-form
  endings in cells 0 on reading. Common rules came as two tables.
- With the run above, two runs under the writing rules both stayed far below the first
  run's counts. Still two runs against one, on one API.
