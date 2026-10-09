# Documents, procedures and handoffs

Use the reader's immediate purpose to decide which information belongs together.

## Explanation

Answer the question, then trace the behavior that makes the answer true. For a
multi-component flow, follow one input from arrival to outcome and explain each
component's responsibility. Put a consequential exception beside the behavior it
limits. Separate the intended design from current code. A list of components or
statuses is not a substitute for how one causes the next. Once the requested
mechanism and its consequential boundaries are explained, stop. Other lifecycle
operations belong here only if they change the answer to this question.

## Procedure

Arrange steps in execution order. At each decision, put the observed value,
actual threshold and resulting action together. The operator should not need to
return to an earlier conditions table to execute the step. Keep success and failure
branches distinct. Put failure handling in its branch rather than repeating a full
warning at every step. Include only source-supported commands, stop conditions,
retries and recovery actions. If failure handling is unspecified, say so where it
matters; do not invent a recovery command or authorization.

## Handoff

Lead with the present state and what the successor should do next. Attach the
necessary check, unresolved condition, path or command to that action. Keep history
only when it explains the current state or affects rollback. A phase table, state
list and final summary often repeat the same answer; choose the useful location.

Distinguish observed results from plans. A local test pass and an older deployment
failure may both be true. A file change makes the earlier test historical evidence,
not validation of the new state. Missing test details do not mean tests were absent.

## Interpretation and terminology

Retain domain distinctions even when a broad synonym is shorter. Explain unfamiliar
terms by their role in this system. Keep user-provided schemas and templates exact.
A higher p95 describes a changed percentile boundary, not proof that every request
in the slowest five percent became slower. Preserve the measured population and
avoid unsupported causal explanations or group-wide claims.

These rules adapt clarity and evidence-preservation principles. Do not call Korean
output ASD-STE100 compliant or apply its English vocabulary and word limits.
Keep provenance that enables verification. Fixture labels and drafting narration
usually do not belong in the deliverable.
