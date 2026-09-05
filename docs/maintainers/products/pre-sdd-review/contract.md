# pre-sdd-review 계약

이 문서는 Pre-SDD Review의 활성화 조건, 권위 순서, 리뷰어 격리,
문서 수정 경계, finding, freshness, verdict, SDD handoff를 소유합니다.

## Activation and input resolution

승인된 설계 명세와 구현 계획이 모두 있을 때만 씁니다. SDD나 계획 실행
직전 준비 상태를 볼 때 활성화합니다. 처음 설계나 계획을 쓸 때는 쓰지
않습니다. 코드 검토, 출시 준비, 교정, 일반 문서 작업에도 쓰지 않습니다.

구현 계획 경로 하나를 먼저 정합니다. 그 계획의 `**Spec:**` 필드로
resolved design specification을 찾습니다. 그다음 명시적으로 binding인
참조, 저장소 루트, 현재 Git 상태를 확인합니다. `**Spec:**` 경로가 없거나
해석할 수 없으면 `BLOCKED`입니다. 주변 파일을 추측해 고르지 않습니다.

한 호출은 구현 계획 하나만 검토합니다. 여러 계획 중 어느 것인지 분명하지
않으면 정확한 계획 경로를 다시 받습니다. 받을 수 없으면 `BLOCKED`입니다.
계획을 나눠 여러 번 호출해도 전체를 묶은 `READY`는 만들지 않습니다. 공유
설계가 나중 호출에서 바뀌면, 이전 설계 지문에 의존한 계획 판정을 다시
검토합니다.

계획이 필수 구현 베이스(`branch`, `ref`, 또는 `commit`)를 적으면,
검토자를 부르기 전에, 필수 베이스가 `HEAD`의 조상인지
`git merge-base --is-ancestor <required-base> HEAD`로 확인합니다. 베이스를
해석할 수 없거나 `HEAD`의 조상이 아니면 불일치를 남기고 `BLOCKED`를 반환합니다.
다른 checkout을 임의로 검토하거나 고치지 않습니다.

## Authority order

충돌은 아래 순서로 해석합니다.

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

기본 검토자는 새로 오고, 독립적이며 `read-only`입니다. 검토자는 증거와
가장 작은 권위 보존 수정만 보고합니다. 문서를 고치는 것은 controlling
agent만 합니다. 아래 목록만 수정할 수 있습니다. 기능, dependency, host
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

Across the entire invocation, use at most two review roles: one primary role
and one focused risk role when triggered. A fresh re-review may replace an
agent, but it does not add a review role or broaden the triggered risk class.
Evidence `reviewer_count` records logical roles, not cumulative agent calls.

## Default flow, verdicts, and freshness

한 호출은 발견 단계 한 번과 수정 최대 두 번, 범위 제한 재검토로
끝납니다. 수정이 스키마, 타입, 인터페이스, 상태 전이, 조건부 수정 면,
작업 간 계약, 검증 의미, 공개/비공개 경계를 바꾸면 제어 에이전트가 짧은
영향 범위 표를 만듭니다. 표에는 바뀐 주장, 바뀐 심볼·상태·경로·명령,
직접 소비자, 이웃 작업 인터페이스, `modify | verified-no-change | unresolved`
처리, 검증 반례를 적습니다. 이 조건에 해당하지 않는 단순 값·문구 수정은
표를 만들지 않습니다.

새 검토자는 고친 최종 문서, 원래 발견, 영향 범위 표를 받습니다. 원래
발견의 해결과 제한된 영향 회귀를 순서대로 합니다. 수정 패스는 최대 두
번입니다. 두 번째 패스 뒤에도 중요한 문제가 남으면 심각도를 낮추지
않습니다. `review-only`는 파일을 바꾸지 않고 첫 검토 판정만 반환합니다.

범위 제한 재검토의 현재 수정 대상은 원래 발견이거나 직접 대응된 수정 영향뿐입니다.
최종 문서에서 찾은 대응되지 않은 중요 발견은 버리지 않습니다.
지금 수정에는 넣지 않습니다. 호출을 끝내고 인계에 기록한 뒤
기존 판정 규칙을 따릅니다.

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

Authority-preserving repair에는 승인 질문을 하지 않습니다. 사용자 권위가
필요하면 exact decisions를 one consolidated user checkpoint로 묶습니다. Do not
automatically start another invocation after `REVISE` or `BLOCKED`. 문서, 권위,
저장소 증거가 바뀌지 않았다면 이전 handoff를 재사용합니다.

## Optional evidence contract

Evidence recording is a separate optional contract and does not change the
authority order, reviewer protocol, repair allowlist, or verdict rules. The
controller runs `python3 "<skill-root>/evidence/evidence.py" --version` from
the loaded skill root, calls `start` before semantic review only when `schema`
is 2 and `skill_name` is `pre-sdd-review`, and calls `finish` once after the
verdict and repairs are final. It prints exactly one `Evidence:` line. Any
unavailable, malformed, incompatible, or permission-failing recorder remains
visible as `not_recorded` and cannot change `READY`, `REVISE`, or `BLOCKED`.

The controller resolves the design path from the plan's `**Spec:**` field and
passes it as `--design`; when it cannot, it omits `--design` and returns
`BLOCKED`. The recorder never parses `**Spec:**`. An invocation that ends
before `finish` calls `abandon` with one of `user-cancelled`, `input-changed`,
`scope-changed`, `input-format-fixed`, or `other`. `run_id` stays
controller-local and outside the reviewed documents.

The recorder owns paths, hashes, Git facts, validation, atomic file
replacement, and aggregation under `~/.pre-sdd-review/runs/`. The reviewer and
controller remain the only owners of semantic findings, repairs, protocol
observations, and verdicts. Records hold repository-relative paths, a
directory name, hashes, enum values, integers, timestamps, and bounded
paraphrases; never source text, absolute paths, prompts, provider
transcripts, command output, environment values, or credentials. Local files
are not a signed audit log.

`outcome` is not a controller duty. After SDD or implementation ends, the user
or the SDD worker records one label (`good`, `false-ready`, `noisy`,
`abandoned`) with an optional note; `false-ready` requires a `READY` verdict
and a label may be re-recorded. `summary` is JSON for agents: counts, cost,
per-plan chains, repeated finding patterns, and anomalies, each carrying
`run_id` values. No automatic skill mutation, fixture export, or client/model
ranking follows from it.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- 권위 순서, 판정, repair 한도, reviewer role: `skills/pre-sdd-review/SKILL.md`,
  `references/reviewer-protocol.md`, 이 계약, `tests/products/pre-sdd-review/cases.json`,
  제품 README
- 기록기 명령·schema 2: `skills/pre-sdd-review/evidence/evidence.py`,
  `evidence/README.md`, `tests/products/pre-sdd-review/evidence/`
- 호스트 지원: `products.toml`, `compatibility.md`, 공개 안내, 해당 테스트.
  이 작업에서 호스트 지원을 넓히지 않습니다.

## 하지 않는 것

아래는 명시적으로 추가하지 않습니다.

- closure-only input schema
- shared-design invalidation map
- program ledger
- evidence probe cache

## Handoff

`READY`이면 해결된 설계와 계획의 정확한 경로와 final fingerprints를
출력합니다. 검토와 구현이 이어지는 흐름에서는 고치기 전 복사본이 아니라
최종 문서를 SDD worker에게 넘깁니다.

### SDD handoff

Do not start SDD unless the outer request explicitly asks for implementation.
