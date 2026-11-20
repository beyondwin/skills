# Changelog

All notable changes to this product are documented in this file.

## Unreleased

- First version: explicit `/api-guide` invocation in Claude Code writes an API
  integration guide checked against the server code and publishes it as a Claude
  artifact.
- Without the Artifact tool, save the page as an HTML file and report its path.
- List a shared auth or error library code only after tracing that it fires for the endpoint.
- One headless run on a new endpoint (app readers) finished in about 11 minutes. It found a
  wrong auth code in an earlier hand-written guide. Page accuracy was spot-checked by hand,
  not measured.
