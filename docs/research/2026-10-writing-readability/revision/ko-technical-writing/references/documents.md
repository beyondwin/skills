# Documents, runbooks and engineering handoffs

Choose the structure from what the reader must understand or do.

- **Technical explanation:** state the behavior and boundary, then the mechanism
  and evidence needed to understand it. Explain the necessary causal chain before
  introducing exceptions. For a multi-component flow, follow one input from arrival
  to outcome and state each component's responsibility. Preserve exceptions next
  to the behavior they limit. Separate intended design from current code.
- **Runbook:** put prerequisites and decision conditions before the affected steps.
  Keep success and failure branches separate. Keep a step executable: say what to inspect, how to decide, and what to do next.
  Put failure actions in the failure branch instead of repeating the whole rule at
  every step. Include a stop condition or recovery action when the source specifies one; do not invent a safe retry or rollback.
- **Handoff:** distinguish completed work, checks actually observed, unresolved
  issues, and the next executable action. Include paths or commands that a successor
  needs. A task list or old success log alone is not evidence of current completion.

When multiple sources disagree, distinguish environments, times and source types
before deciding whether they conflict. For example, a local test pass and an older
deployment failure can both be true. A changed file makes an older test result
historical evidence; do not present it as validation of the changed state.

Use one stable term per concept when that helps the reader, but retain domain terms
whose distinction matters. Do not replace a precise term with a broad synonym merely
to make a sentence shorter. Preserve a requested code block, JSON schema or document
template; prose preferences do not override a machine-readable output contract.

Do not label a Korean adaptation as ASD-STE100 compliance or use an English word
list as a Korean correctness test. This skill uses clarity and evidence-preservation
principles without imposing that standard's vocabulary or numerical limits.

## Gotchas observed in model runs

- **Repetition instead of orientation:** an overview, phase table, current-state list
  and closing summary can repeat the same decision. Give each fact one useful home.
  In a handoff, keep phase history only when it explains the next action or rollback.
- **A procedure that sends the reader backward:** a step such as “compare with the
  conditions above” makes the operator reconstruct the branch. Put the actual
  threshold and resulting action together at that decision step. Do not duplicate
  the entire procedure in an upfront overview.
- **A simple explanation that strengthens the claim:** a higher p95 does not establish
  that every request in the slowest 5% became slower. Explain what an aggregate or
  threshold measures without extending it to every member of the group. Preserve
  the measured population and avoid adding unmeasured causal explanations.

Fixture labels and narration of your drafting process do not usually help the
intended reader. Keep provenance when it enables verification, but do not turn
“synthetic notes” into a product name or start with a report of what you did not run.
