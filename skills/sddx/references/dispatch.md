# Implementer dispatch

From the loaded skill root:

    python3 "<skill-root>/scripts/resolve_backend.py" --backend <cursor|grok|c|g> --json

Do not launch a worker from the resolver. Parse one JSON object.

If `available` is false, stop. Do not fail over.

Compose the worker command from `argv_prefix` plus controller flags:

- Grok: immediately before starting the worker, prepare its worktree profile:

      python3 "<skill-root>/scripts/prepare_grok_sandbox.py" prepare --worktree "<worktree>" --state "<evidence-dir>/grok-sandbox.json"

  `<skill-root>`, `<worktree>`, and `<evidence-dir>` are absolute paths already
  established by SDD, not requests for more user input. If preparation fails,
  do not start the worker. Read the successful JSON as `prepared`, then replace
  the existing sandbox value in the resolved prefix without adding a second
  `--sandbox`:

      argv = list(resolved["argv_prefix"])
      sandbox_index = argv.index("--sandbox")
      argv[sandbox_index + 1] = prepared["profile"]
      argv.extend(["--cwd", str(worktree), "--rules", worker_rules])

  `resolved` is the resolver JSON and `worker_rules` is the full text of
  `worker-prompt.md`. Then append `--reasoning-effort high|xhigh` (or `--effort`
  if local help supports that alias), `--prompt-file <dispatch-file>` or `-p`,
  and `--resume <id>` for fix rounds 1-3. `--disable-web-search` is already in
  `argv_prefix`.
  Do not pass `--worktree`. Do not pass `--continue`. Do not paste host
  credentials into the prompt file.
- Cursor: `--workspace <worktree>` (or `--cwd` if that is what help
  showed), `--model` a grok id from `models`/`--list-models`, headless
  already in `argv_prefix`. Resume with `--resume <id>` when the previous
  JSON/output gave an id. If no id, SDD fallback: fresh worker plus the
  report file.

For Grok, confirm the worker and any work it started have exited, then clean up
after every success or failure:

    python3 "<skill-root>/scripts/prepare_grok_sandbox.py" cleanup --worktree "<worktree>" --state "<evidence-dir>/grok-sandbox.json"

Do not clean up while a process is still running or overlap it with a new
worker. New tasks and resumed fix rounds use the same prepare, launch, exit,
and cleanup order. If cleanup fails, do not overwrite other files to repair
it; record the remaining difference and state path in the ledger.

Wait on the shell job without short polls. Codex `wait_agent` is only for
native reviewers.

Do not pass `--plugin-dir`. Do not approve extra MCP servers.
