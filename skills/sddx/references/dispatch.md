# Implementer dispatch

From the loaded skill root:

    python3 "<skill-root>/scripts/resolve_backend.py" --backend <cursor|grok|c|g> --json

Do not launch a worker from the resolver. Parse one JSON object.

If `available` is false, stop. Do not fail over.

Compose the worker command from `argv_prefix` plus controller flags:

- Grok: `--cwd <worktree>`, `--disable-web-search` (already in
  `argv_prefix`), `--reasoning-effort high|xhigh` (or `--effort`
  if that is the flag the help showed), `--prompt-file <dispatch-file>` or
  `-p`, and for fix rounds 1-3 `--resume <id>`. Do not pass `--worktree`.
  Do not pass `--continue`. Do not paste host credentials into the prompt
  file.
- Cursor: `--workspace <worktree>` (or `--cwd` if that is what help
  showed), `--model` a grok id from `models`/`--list-models`, headless
  already in `argv_prefix`. Resume with `--resume <id>` when the previous
  JSON/output gave an id. If no id, SDD fallback: fresh worker plus the
  report file.

Wait on the shell job without short polls. Codex `wait_agent` is only for
native reviewers.

Do not pass `--plugin-dir`. Do not approve extra MCP servers.
