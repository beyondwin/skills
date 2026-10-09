# Verification record

## Executed

- Frozen resource/protocol assertions before every live phase. The 0.3.0 source
  tree and first experiment were not changed to incorporate later fixes.
- Skill Creator quick validation passed for 0.3.0, 0.3.1 and 0.3.2.
- Four offline study tests passed: exact tail arithmetic, label-independent pair
  mapping, invalid scorer-choice rejection, and archive-prefix-only masking.
- New Python files compile under stock macOS `/usr/bin/python3` 3.9.
- All three generation runners were dry-run before dispatch; no live calls in dry-run.
- Main export verifies 62 dispatch IDs, 61 complete answers, prompt/response hashes,
  actual runtime metadata, evaluator JSON, tool isolation, and removed auth copies.
  Both evaluator controls pass; one 480-second judge timeout is retained as missing.
- Main native audit verifies 12 unchanged workspaces and successful entrypoint and
  reference reads in all 8 skill-bearing native generations. The four baseline
  native homes have no technical-writing skill.
- 0.3.1 export verifies 9 responses, author grades 7/9, five unchanged native
  workspaces, native reads and exact JSON null/false preservation. Staged-only
  commit and gitlink interpretation were inspected against their fixture states.
- 0.3.2 export verifies 7 responses, author grades 7/7, three unchanged native
  workspaces and native reads. Exact four-key JSON with null/false preserved.
- Installed personal skill remains byte-for-byte equal to frozen 0.2.2, all six files.
- The private three-pair reading sheet was loaded in the in-app browser. A JavaScript
  string-escaping error found on the first interaction was fixed. The final UI
  visibly collected synthetic A / no-difference / B selections; reload cleared them.
  These clicks are not human judgments. The agent-created browser tab and preview
  server were closed; an unrelated listener on the same port was left untouched.
- Repository public-document tests: 65 passed. Local research Markdown targets and
  cross-document anchors were checked separately, plus diff/whitespace checks.

## Not executed or not established

No candidate installation or installed smoke: the adoption gate failed. The
rejected 0.3.0's conditional native regressions were skipped; the corrections have
separate actual regression runs. No full product suite or merge, supported-host
change, Claude/Cursor native-skill discovery test, controlled human comparison, comprehension
speed measurement, or population-wide superiority claim. No additional runtime
model calls were added to the skill. No superpowers skill or subagent was used.

Author semantic checks and model judgments are different evidence sources. The
export scripts verify records and declared grades, not the truth of a prose grade.
Repeated developmental corrections are not extra independent confirmation samples.

## Subsequent reader response

The user submitted B / B / A for the three pairs. The local displayed sheet and
archived sheet both match the mapping manifest SHA-256; all six source responses
match that manifest. Original decoding gives one 0.2.2 selection and two no-skill
selections. A subsequent direct clarification says all pairs were hard to distinguish
and terminology across all texts felt unnatural. The clear-preference interpretation
is withdrawn; original labels remain intact. No agent UI clicks or inferred itemwise
reasons are counted. This post-hoc feedback does not measure comprehension or 0.3.2.
The author inspected all six drafts for concrete terminology examples; those examples
are hypotheses, not terms individually identified by the user. No new model calls or
skill changes were made in response to this clarification.
