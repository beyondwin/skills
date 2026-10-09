# Documents, procedures and handoffs

Use the reader's immediate purpose to decide which information belongs together.

## Korean prose example

This synthetic example illustrates phrasing and selection, not facts to reuse in
other tasks. Assume these source facts: POST /bundles stores a job and returns202;
a worker later creates the file and can wait for capacity; GET /bundles/{id} reports
finished when creation completes. Storage is encrypted and logs are kept30days.
The reader asks why a202 response does not mean the file is ready.

A useful answer is:

> `202` 응답을 받아도 파일은 아직 준비되지 않았을 수 있습니다. 서버는 요청을
> 저장하면 먼저 이 응답을 보냅니다. 실제 파일은 뒤에서 작업을 처리하는 프로그램인
> 워커가 만들기 때문에, 처리할 워커가 없으면 기다려야 합니다.
>
> `GET /bundles/{id}`에서 `finished`를 확인해야 파일 생성이 끝났다고 볼 수
> 있습니다. 요청 접수와 파일 생성 완료는 서로 다른 단계입니다.

The answer connects the behavior rather than listing “비동기 처리 / 워커 용량 /
완료 상태”. It leaves encryption and log retention out because they do not answer
this question. It does not invent a wait-time guarantee or a retry command. Use
this level of ordinary Korean prose, not these sentences as a template.

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

Keep user-provided schemas and templates exact.
A higher p95 describes a changed percentile boundary, not proof that every request
in the slowest five percent became slower. Preserve the measured population and
avoid unsupported causal explanations or group-wide claims.

These rules adapt clarity and evidence-preservation principles. Do not call Korean
output ASD-STE100 compliant or apply its English vocabulary and word limits.
Keep provenance that enables verification. Fixture labels and drafting narration
usually do not belong in the deliverable.
