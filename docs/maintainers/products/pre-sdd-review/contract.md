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

기본 모드는 review, repair documents, scoped re-review입니다. 수정 패스는
최대 두 번이며, 두 번째 패스 뒤에도 material issue가 남으면 severity를
낮추지 않고 `REVISE`로 유지합니다. `review-only`는 파일을 바꾸지 않고 첫
검토 verdict만 반환합니다.

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

## Handoff

`READY`이면 resolved design과 plan의 정확한 경로와 final fingerprints를
출력합니다. review와 implementation이 결합된 흐름에서는 수리 전 복사본이
아니라 최종 문서를 SDD worker에게 전달합니다.

### SDD handoff

Do not start SDD unless the outer request explicitly asks for implementation.
