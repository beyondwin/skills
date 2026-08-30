# pre-sdd-review 계약

이 문서는 Pre-SDD Review의 활성화 조건, 권위 순서, 리뷰어 격리,
문서 수정 경계, finding, freshness, verdict, SDD handoff를 소유합니다.

## Activation and input resolution

승인된 설계 명세와 구현 계획이 모두 있고, SDD 또는 계획 실행 직전의
준비 상태를 검토할 때만 활성화합니다. 최초 설계·계획 작성, source diff
review, release readiness, 교정, 일반 문서 작업에는 활성화하지 않습니다.

구현 계획 경로 하나를 먼저 확정합니다. 그 계획의 `**Spec:**` 필드로
resolved design specification을 찾고, 명시적으로 binding인 참조, 저장소
루트, 현재 Git 상태를 차례로 확인합니다. `**Spec:**` 경로가 없거나 해석할
수 없으면 `BLOCKED`이며, 주변 파일을 추측해 선택하지 않습니다.

한 호출은 구현 계획 하나만 검토합니다. 여러 계획 중 어느 것인지 분명하지
않으면 정확한 계획 경로를 다시 받아야 하며, 받을 수 없으면 `BLOCKED`입니다.
계획을 나눠 여러 번 호출해도 전체를 묶은 `READY`는 만들지 않습니다. 공유
설계가 나중 호출에서 바뀌면, 이전 설계 지문에 의존한 계획 판정을 다시
검토합니다.

## Authority order

충돌은 아래의 machine-readable 순서로 해석합니다.

### Authority order

1. User-approved direction and referenced visual authority.
2. Accepted ADRs and other explicitly binding decision records.
3. The approved design specification.
4. The implementation plan.
5. Current repository reality.

저장소 현실은 feasibility와 blast radius의 증거일 뿐, 승인된 제품 결정을
대체할 권위가 아닙니다. 수리에 새 제품 결정이 필요하면 충돌을 보존하고
`BLOCKED`를 반환합니다.

## Reviewer isolation and repair allowlist

기본 리뷰어는 fresh, independent, `read-only`입니다. 리뷰어는 증거와 가장
작은 authority-preserving correction만 보고하고, controlling agent만 문서를
고칩니다. 아래 bounded list만 수정 권위를 가지며 기능, dependency, host
claim, 제품 결정을 추가하지 않습니다.

### Editable paths

1. resolved design specification.
2. resolved implementation plan.

### Excluded surfaces

- `accepted ADRs`
- `approved visual authority`
- `application code`
- `tests`
- `configuration`
- `generated artifacts`
- `unrelated documentation`

## Review passes and findings

프로토콜은 정확히 `five passes`를 실행합니다.

### Review passes

1. authority trace;
2. repository grounding;
3. cross-artifact consistency;
4. verification falsification;
5. readiness verdict.

Use only two severities: `BLOCKER` and `IMPORTANT`. Use only five finding
classes: `authority-drift`, `repo-reality`, `coverage`, `ordering`, and
`verification-gap`. A finding records its ID, severity, class, exact document
location, evidence, concrete consequence, and smallest document fix. Zero
findings is valid.

### Severities

- `BLOCKER`
- `IMPORTANT`

### Finding classes

- `authority-drift`
- `repo-reality`
- `coverage`
- `ordering`
- `verification-gap`

아래 목록이 두 번째 리뷰어의 유일한 trigger 집합입니다.

### Conditional risk triggers

A second reviewer is conditional only, never routine.

- `framework or runtime removal`
- `schema migration or data deletion`
- `authentication, authorization, or security boundaries`
- `public/private data-boundary changes`
- `external side effects such as publishing, billing, messaging, or production mutations`

## Default flow, verdicts, and freshness

기본 모드는 review, repair documents, scoped re-review입니다. 수리가 스키마,
타입, 인터페이스, 상태 전이, 조건부 수정 면, 작업 간 계약, 검증 의미,
공개/비공개 경계를 바꾸면 제어 에이전트가 짧은 영향 범위 표를 만듭니다. 표에는
바뀐 주장, 바뀐 심볼·상태·경로·명령, 직접 소비자, 이웃 작업 인터페이스,
`modify | verified-no-change | unresolved` 처리, 검증 반례를 적습니다. 이
조건에 해당하지 않는 단순 값·문구 수정은 표를 만들지 않습니다.

새 검토자는 수리된 최종 문서, 원래 발견, 영향 범위 표를 받아 원래 발견의
해결과 제한된 영향 회귀를 순서대로 수행합니다. 수정 패스는 최대 두 번이며,
두 번째 패스 뒤에도 중요한 문제가 남으면 심각도를 낮추지 않습니다.
`review-only`는 파일을 바꾸지 않고 첫 검토 판정만 반환합니다.

### Verdicts

- `READY`: no unresolved finding requires invention or permits a materially wrong implementation to pass planned evidence.
- `REVISE`: a repairable material document defect remains.
- `BLOCKED`: required input, authority, or repository evidence is unavailable or would require a new product decision.

아래 freshness 목록과 invalidation 규칙을 최종 보고에 그대로 기록합니다.

### Freshness

- repository-relative design path and SHA-256
- repository-relative plan path and SHA-256
- Git `HEAD` (or `unborn`)
- worktree was clean or dirty
- review timestamp
- final verdict
- Any content change to either resolved document invalidates `READY`.

최종 보고는 입력·최종 문서 해시, 패스 번호, 발견 ID/분류, 영향 범위 트리거,
바뀐 문서 해시, 판정을 담은 짧은 패스 영수증을 포함합니다. `REVISE`와
`BLOCKED`는 미해결 발견과 다음 범위를 담은 인계 묶음을 반환합니다. 새 권위가
필요하면 판정은 `BLOCKED`입니다.

## Optional evidence contract

Evidence recording is a separate optional contract and does not change the
authority order, reviewer protocol, repair allowlist, or verdict rules. The
controller checks canonical `pre-sdd-review-evidence --version` output, calls
`start` before semantic review only when CLI major 1/schema 1 matches this
product, and calls `finish-review` only after the verdict and repairs are
final. It prints exactly one `Evidence:` line. Any unavailable, malformed,
incompatible, or permission-failing recorder remains visible as
`not_recorded` and cannot change `READY`, `REVISE`, or `BLOCKED`.

`run_id` stays controller-local and outside the reviewed documents. It is
given only to an explicitly requested combined SDD worker; a separate worker
must resolve the exact current repository and plan hash. Downstream recording
uses the current repository locator and occurs only at a terminal status.
The CLI owns deterministic paths, hashes, Git facts, identity, validation,
create-only persistence, matching, and aggregation. The reviewer and
controller remain the only owners of semantic findings, repairs, protocol
observations, and verdicts.

Receipts contain bounded paraphrases, never source or document text, absolute
paths, prompts, provider transcripts, command output, environment values, or
credentials. Bounded reason/finding fields do not make raw input safe; the
controller must paraphrase them. The CLI does not add automatic secret
detection. Local atomic storage is not a signed audit log, and observer-entered
assessment labels or confidence are self-improvement evidence rather than
objective proof. Schema 1 has no outcome amendment; disputes stay in
`disputed_findings`, uncertainty stays `inconclusive`, and candidate thresholds
remain human-inspection heuristics with no automatic mutation or ranking.

## Handoff

`READY`이면 resolved design과 plan의 정확한 경로와 final fingerprints를
출력합니다. review와 implementation이 결합된 흐름에서는 수리 전 복사본이
아니라 최종 문서를 SDD worker에게 전달합니다.

### SDD handoff

Do not start SDD unless the outer request explicitly asks for implementation.
