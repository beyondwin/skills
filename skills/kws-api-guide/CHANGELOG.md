# Changelog

All notable changes to this product are documented in this file.

## Unreleased

- First version: explicit `/kws-api-guide` invocation in Claude Code writes an API
  integration guide checked against the server code and publishes it as a Claude
  artifact.
- Page sentences follow `references/writing.md`: at most two sentences per table cell, one
  parenthetical per sentence, the reader's words instead of the skill's, one register on
  Korean pages. Common rules split into Handle in code and Formats.
- The page, progress updates, and report use the language of the invocation text.
- Without the Artifact tool, save the page as an HTML file and report its path.
- List a shared auth or error library code only after tracing that it fires for the endpoint.
- Two headless runs on the same new endpoint (app readers). The first, about 11 minutes,
  found a wrong auth code in an earlier hand-written guide. The second, with the writing
  rules, kept the compared facts and had no table cell of three or more sentences (11
  before). Page accuracy was spot-checked by hand, not measured.
