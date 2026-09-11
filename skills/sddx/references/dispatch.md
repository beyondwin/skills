# Implementer dispatch

From the loaded skill root:

    python3 "<skill-root>/scripts/resolve_backend.py" --backend <cursor|grok|c|g> --json

Do not launch a worker from the resolver. Parse one JSON object.

If `available` is false, stop. Do not fail over.

Before dispatch, use SDD's task-brief output and supply all decisions and
task reference paths needed for this task. Include relevant constraints from
the plan in the brief; do not send the plan itself as a reference. Source and
test inspection remains available. When the brief lacks a required decision,
complete it in the controller rather than ask the worker to recover it from
the plan. Add `Search paths:` with concrete source/test file or directory
paths to the brief. Keep planning documents out of that list. The worker
starts with direct reads of named files and targets content searches at these paths;
a glob without a target path can still search the whole repository.
`Search paths` limits content searches. Filename-only listings inside the
current worktree, including its root, and direct reads of repository
ignore/build/test configuration needed for this task are allowed inspection.
These actions alone are not scope deviations. They never permit reading
full-plan content, credentials, or secrets.

Put this boundary directly in each new or resumed dispatch prompt, alongside
the brief and report paths (it also remains in the worker rules):

> Read the brief first. Use its requirements and explicitly listed task
> references. The controller owns the full plan; do not read it or follow
> links to it, including through shell/search tools. Missing decisions go
> back as NEEDS_CONTEXT. Read named source/test files directly first; content
> searches must target the brief's Search paths, not the whole workspace.
> Within this worktree, filename-only listings and direct reads of repository
> ignore/build/test configuration needed for this task are allowed and are
> not scope deviations. Never read full-plan content, credentials, or secrets
> through these inspections. Report actual scope deviations even if tests pass.

Capture the CLI's tool-call/results stream in local, uncommitted evidence.
For Grok, use `--output-format streaming-messages-json`; for Cursor, use the
local help's supported structured event output. Preserve test commands and
their actual exits. If the trace is unavailable or incomplete, record role
compliance as UNVERIFIED. A final message alone is not a tool trace.

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
