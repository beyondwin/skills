# pre-sdd-review 계약

이 문서는 Pre-SDD Review의 활성화 조건, 권위 순서, 리뷰어 격리,
문서 수정 경계, finding, freshness, verdict, SDD handoff를 소유합니다.

## 활성화와 입력 해석

승인된 설계 명세와 구현 계획이 모두 있을 때만 씁니다. SDD나 계획 실행
직전 준비 상태를 볼 때 활성화합니다. 처음 설계나 계획을 쓸 때는 쓰지
않습니다. 코드 검토, 출시 준비, 교정, 일반 문서 작업에도 쓰지 않습니다.

구현 계획 경로 하나를 먼저 정합니다. 그 계획의 `**Spec:**` 필드로
해결된 설계 명세를 찾습니다. 그다음 명시적으로 묶인 참조, 저장소 루트,
현재 Git 상태를 확인합니다. `**Spec:**` 경로가 없거나 해석할 수 없으면
`BLOCKED`입니다. 주변 파일을 추측해 고르지 않습니다.

한 호출은 구현 계획 하나만 검토합니다. 여러 계획 중 어느 것인지 분명하지
않으면 정확한 계획 경로를 다시 받습니다. 받을 수 없으면 `BLOCKED`입니다.
계획을 나눠 여러 번 호출해도 전체를 묶은 `READY`는 만들지 않습니다. 같은
호스트에서는 나눈 호출을 겹치지 않고 하나씩 실행합니다. 공유
설계가 나중 호출에서 바뀌면, 이전 설계 지문에 의존한 계획 판정을 다시
검토합니다.

계획이 필수 구현 베이스(`branch`, `ref`, 또는 `commit`)를 적으면,
검토자를 부르기 전에, 필수 베이스가 `HEAD`의 조상인지
`git merge-base --is-ancestor <required-base> HEAD`로 확인합니다. 베이스를
해석할 수 없거나 `HEAD`의 조상이 아니면 불일치를 남기고 `BLOCKED`를 반환합니다.
다른 checkout을 임의로 검토하거나 고치지 않습니다.

## 권위 순서

충돌은 아래 순서로 해석합니다.

### Authority order

1. User-approved direction and referenced visual authority.
2. Accepted ADRs and other explicitly binding decision records.
3. The approved design specification.
4. The implementation plan.
5. Current repository reality.

저장소 현실은 실행 가능 여부와 영향 범위의 증거일 뿐, 승인된 제품 결정을
대체할 권위가 아닙니다. 수리에 새 제품 결정이 필요하면 충돌을 보존하고
`BLOCKED`를 반환합니다.

## 검토자 격리와 수정 허용 목록

기본 검토자는 새로 오고, 독립적이며 `read-only`입니다. 검토자는 증거와
가장 작은 권위 보존 수정만 보고합니다. 문서를 고치는 것은 제어 에이전트만
합니다. 아래 목록만 수정할 수 있습니다. 기능, 의존성, 호스트 주장, 제품
결정을 추가하지 않습니다. 독립된 새 검토자를 구할 수 없으면, 제어
에이전트를 독립 1차 검토자로 대신 쓰지 않습니다. Evidence `reviewers`는
의도한 역할이 아니라, 논리 역할에 실제로 얻은 에이전트 수를 셉니다.

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

## 검토 패스와 발견

프로토콜은 정확히 `five passes`를 실행합니다.

### Review passes

1. authority trace;
2. repository grounding;
3. cross-artifact consistency;
4. verification falsification;
5. readiness verdict.

심각도는 `BLOCKER`와 `IMPORTANT` 둘뿐입니다. 발견 분류는
`authority-drift`, `repo-reality`, `coverage`, `ordering`,
`verification-gap` 다섯입니다. 발견에는 ID, 심각도, 분류, 정확한 문서
위치, 증거, 구체적 결과, 가장 작은 문서 수정을 적습니다. 발견이 0개인
것도 유효합니다.

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

두 번째 검토자는 `conditional only`이며 매번 부르지 않습니다.

- `framework or runtime removal`
- `schema migration or data deletion`
- `authentication, authorization, or security boundaries`
- `public/private data-boundary changes`
- `external side effects such as publishing, billing, messaging, or production mutations`

호출 전체에서 검토 역할은 최대 둘입니다. 기본 역할 하나와, 조건이 있을
때의 집중 위험 역할 하나입니다. 새 재검토는 에이전트를 바꿀 수 있지만
역할을 추가하거나 위험 분류를 넓히지 않습니다. Evidence
`reviewer_count`는 누적 호출이 아니라 논리 역할을 셉니다.

## 기본 흐름, 판정, freshness

한 호출은 발견 단계 한 번과 수정 최대 두 번, 범위 제한 재검토로
끝납니다. 첫 검토에서 발견이 없으면 수리와 종료 재검토를 건너뛰고
`READY`입니다. `repair_passes`는 실제로 `repaired` 발견이 나온 패스만
셉니다. 새 호출은 이전 발견의 `repair_pass`를 복사하지 않습니다. 수정이
스키마, 타입, 인터페이스, 상태 전이, 조건부 수정 면, 작업 간 계약, 검증
의미, 공개/비공개 경계를 바꾸면 제어 에이전트가 짧은 영향 범위 표를
만듭니다. 표에는 바뀐 주장, 바뀐 심볼·상태·경로·명령, 직접 소비자, 이웃
작업 인터페이스, `modify | verified-no-change | unresolved` 처리, 검증
반례를 적습니다. 이 조건에 해당하지 않는 단순 값·문구 수정은 표를 만들지
않습니다.

새 검토자는 고친 최종 문서, 원래 발견, 영향 범위 표를 받습니다. 원래
발견의 해결과 제한된 영향 회귀를 순서대로 합니다. 수정 패스는 최대 두
번입니다. 두 번째 패스 뒤에도 중요한 문제가 남으면 심각도를 낮추지
않습니다. `review-only`는 파일을 바꾸지 않고 첫 검토 판정만 반환합니다.

범위 제한 재검토의 현재 수정 대상은 원래 발견이거나 직접 대응된 수정 영향뿐입니다.
최종 문서에서 찾은 대응되지 않은 중요 발견은 버리지 않습니다.
지금 수정에는 넣지 않습니다. 호출을 끝내고 인계에 기록한 뒤
기존 판정 규칙을 따릅니다.

### Verdicts

- `READY`: 남은 문제를 추측하지 않고, 계획된 증거가 잘못된 구현을 통과시키지 않습니다.
- `REVISE`: 고칠 수 있는 중요한 문서 결함이 남았습니다.
- `BLOCKED`: 필요한 입력·권위·저장소 증거가 없거나 새 제품 결정이 필요합니다.

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

권위를 보존하는 수정에는 승인 질문을 하지 않습니다. 사용자 권위가
필요하면 필요한 결정을 승인 요청 하나로 묶습니다. `REVISE`나
`BLOCKED` 뒤에 자동으로 다시 호출하지 않습니다. 문서, 권위,
저장소 증거가 바뀌지 않았다면 이전 인계를 재사용합니다.

## 선택 기록기 계약

기록기는 선택 계약입니다. 권위 순서, 리뷰어 프로토콜, 수정 허용 목록, 판정
규칙을 바꾸지 않습니다. 컨트롤러는 로드된 스킬 루트에서
`python3 "<skill-root>/evidence/evidence.py" --version`을 실행하고,
handshake가 정확히 `skill_name=pre-sdd-review`와 `schema=3`일 때만
기록합니다. 정규 한 줄은
`{"cli_version":"3.0.0","schema":3,"skill_name":"pre-sdd-review"}` 뒤에
LF 하나입니다. 호환되면 `start` 전에 `summary --last 20`을 실행합니다. 같은
`repo` 표시 이름과 계획 경로가 `pending`이면 그 run을 `abandon`합니다. 그
계획의 마지막 완료 판정이 `REVISE` 또는 `BLOCKED`이고 문서 해시가 같으면
이전 인계를 재사용합니다. 아니면 의미 검토 전에 `start`하고, 판정과
수정이 끝난 뒤 `finish`를 한 번 호출합니다. `Evidence:` 줄은 정확히
하나입니다. 기록기가 없거나 실패하면
`Evidence: not_recorded; reason=<code>`를 보고하며, 이 실패가
`READY`, `REVISE`, `BLOCKED`를 바꾸지는 않습니다.

schema 2 pending run은 `historical-unbound`이며 읽기 전용입니다. 보존하고,
기록을 이어가려면 새 run을 시작합니다. 과거 기록의 checkout 결속을 추정하지
않습니다. `start`는 schema 3 checkout 결속 run을 만듭니다. `finish`,
`abandon`, `outcome`은 schema 3만 바꿀 수 있습니다.

컨트롤러는 계획의 `**Spec:**`에서 설계 경로를 해석해 `--design`으로 넘깁니다.
해석할 수 없으면 `--design`을 생략하고 `BLOCKED`를 반환합니다. 기록기는
`**Spec:**`를 파싱하지 않습니다. `finish` 전에 끝나면 `abandon` 이유는
`user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`,
`other` 중 하나입니다. `run_id`는 컨트롤러 로컬이며 검토 문서 밖에 둡니다.

기록기는 `~/.pre-sdd-review/runs/` 아래의 경로, 해시, Git 사실, 검증, 원자적
파일 교체, 집계를 소유합니다. 의미 발견, 수정, 프로토콜 관찰, 판정은 리뷰어와
컨트롤러만 소유합니다. record에는 저장소 상대 경로, 디렉터리 이름,
`repo_key`, 해시, 열거값, 정수, 시각, 짧은 paraphrase만 넣습니다. 원문,
절대 경로, 프롬프트, 공급자 대화, 명령 출력, 환경 값, 자격 증명, salt,
신원 경로 재료는 넣지 않습니다. 로컬 파일은
서명된 audit log가 아닙니다.

evidence home은 `.identity-salt`를 로컬 비공개 32-byte 상태로 두고,
변경에는 `.identity.lock`과 `locks/<run-id>.lock`을 씁니다. 명령이 lock을
풀면 그 lock 파일을 지웁니다. 정규화한 checkout 루트와 Git 디렉터리는 HMAC에만
들어가고, record에는 유도한 `repo_key`와 `repo` 표시 이름만 남습니다. 옮긴
checkout, clone, 다른 worktree, 잃어버린 salt, 다른 evidence home은 원래
결속이 아닙니다. lock은 지원되는 OS locking이 필요합니다. 읽기 전용 `show`,
`summary`, `--version`은 그것이 필요 없고, native Windows 변경 지원을
주장하지 않습니다.

`show`는 record를 검증하고 원본 바이트를 돌려줍니다. `summary`는 필터 전에
전체 scan의 `invalid_records`를 보고합니다. `--repo`는 `repo` 표시 이름만
거르고, `--last`는 유효한 순서 있는 기록을 고릅니다. `counts.verdict`는 본
완료 판정을 모두 포함하고, `normal_verdict`와 `anomalous_verdict`는 관찰로
나누며, 결속 수는 `checkout-bound`와 `historical-unbound`를 구분합니다. 이
값은 로컬 관찰이지 모델 품질 측정이나 서명된 감사 주장이 아닙니다.

입력 형태, 열거·개수 범위, record 크기, 필수 필드, 경로 제한은 계속
검증합니다. 의미 검토는 기존 판정, 리뷰어, 발견, 수정 규칙을 따릅니다. 구조가
맞는 이탈은 관찰 값으로 `anomalies`에 남고, evidence가 판정을 다시 쓰거나
변경 권위가 되지는 않습니다.

`outcome`은 컨트롤러 일이 아닙니다. SDD나 구현이 끝난 뒤 사람이나 SDD
워커가 라벨 하나(`good`, `false-ready`, `noisy`, `abandoned`)와 선택 메모를
남깁니다. `false-ready`는 `READY` 판정이 있어야 하고, 라벨은 다시 기록할 수
있습니다. `summary`는 에이전트용 JSON입니다. counts, cost, 계획별 chains,
반복 발견 패턴, anomalies에 각각 `run_id`가 붙습니다. 이 값으로 스킬을
자동 수정하거나, 픽스처를 내보내거나, client/model 순위를 매기지 않습니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- 권위 순서, 판정, repair 한도, reviewer role: `skills/pre-sdd-review/SKILL.md`,
  `references/reviewer-protocol.md`, 이 계약, `tests/products/pre-sdd-review/cases.json`,
  제품 README
- 기록기 명령·schema 3: `skills/pre-sdd-review/evidence/evidence.py`,
  `evidence/README.md`, `tests/products/pre-sdd-review/evidence/`
- 호스트 지원: `products.toml`, `compatibility.md`, 공개 안내, 해당 테스트.
  이 작업에서 호스트 지원을 넓히지 않습니다.

## 하지 않는 것

아래는 명시적으로 추가하지 않습니다.

- closure-only input schema
- shared-design invalidation map
- program ledger
- evidence probe cache

## 인계

`READY`이면 해결된 설계와 계획의 정확한 경로와 final fingerprints를
출력합니다. 검토와 구현이 이어지는 흐름에서는 고치기 전 복사본이 아니라
최종 문서를 SDD worker에게 넘깁니다.

### SDD handoff

바깥 요청이 구현을 명시하지 않으면 SDD를 시작하지 않습니다.

### Contract

- `primary-input`: `plan-primary`, `spec-resolves-design`
- `plan-cardinality`: `one-plan-per-invocation`, `no-aggregate-ready`
- `editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`
- `review-only`: `no-mutation`
- `repair-flow`: `review-repair-bounded-impact-re-review`
- `repair-impact`: `structural-trigger-only`, `direct-consumers`
- `repair-passes`: `at-most-two`
- `verdicts`: `READY`, `REVISE`, `BLOCKED`
- `second-reviewer`: `conditional-only`
- `risk-triggers`: `framework-runtime-removal`, `schema-data-deletion`, `auth-security-boundary`, `data-boundary-change`, `external-side-effects`
- `freshness`: `fingerprints`, `content-change-invalidates`
- `required-base`: `pre-dispatch-ancestor-check`
- `handoff`: `unresolved-packet`
- `sdd`: `outer-request-implementation-only`
- `evidence`: `optional`, `non-blocking`, `controller-local-run-id`
