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

판정을 내는 호출 하나는 구현 계획 하나만 검토합니다. 여러 계획 중 어느
것인지 분명하지 않으면 정확한 계획 경로를 다시 받습니다. 받을 수 없으면
`BLOCKED`입니다. 계획을 나눠 여러 번 판정을 내는 호출로 쪼개도 전체를 묶은
`READY`는 만들지 않습니다. 발견은 겹칠 수 있고 수리는 겹치지 않습니다.
앞 계획이 `BLOCKED`여도 뒤 계획의 발견은 진행합니다. 뒤 계획 `READY`를 앞
계획에 묶지 않습니다. 앞 계획의 수리가 공유 설계를 바꾸면 의존하는 모든 계획을
이번 캠페인에서 dirty로 표시합니다. 그 무효화로 새 캠페인을 열지 않습니다.

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
5. Repository reality at this plan's turn.

저장소 현실은 실행 가능 여부와 영향 범위의 증거일 뿐, 승인된 제품 결정을
대체할 권위가 아닙니다. 계획의 turn은 저장소에 이 계획보다 앞선 모든 계획을
고정된 실행 순서로 더한 것이며, 그때그때의 `HEAD`가 아닙니다. 수리에 새
제품 결정이 필요하면 충돌을 보존하고 `BLOCKED`를 반환합니다.

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
3. resolved shared-file ledger.

원장은 유도된 증거이지 권위가 아닙니다. 권위 순서 다섯은 그대로입니다. 원장이
계획의 `Files:`와 어긋나면 계획이 이기고 원장을 다시 만듭니다.

### Excluded surfaces

- `accepted ADRs`
- `approved visual authority`
- `application code`
- `tests`
- `configuration`
- `generated artifacts`
- `unrelated documentation`

## 선행 원장 패스

외부 요청이 계획을 둘 이상 이름 대거나 명시적으로 요청하면, 판정을 내는 첫 호출 앞에 한 번 돕니다.
이 패스는 판정을 내지 않습니다. 출력은 원장, 확정된 실행 순서, 저장소로 확인된
결함 후보입니다. 컨트롤러가 전부 하고 검토자를 부르지 않습니다. 확인된 후보는
검토자 파견 전에 고칩니다. 그 수리는 검토 이전이므로 수리 패스를 먹지 않고
`repair_pass: 0`으로 기록합니다. `review-only`에서는 원장을 파일로 쓰지 않고
반입 수리도 하지 않습니다. 이 패스는 run으로 기록하지 않습니다.

계획에 `Files:` 절이 없으면 멈추고 묻습니다. Task의 edit surface에서 유도하지
않습니다.

### Ledger shape

- 머리: 생성 시각, 대상 계획 목록과 각 계획의 SHA-256, 확정된 실행 순서
- 본문: 한 행이 한 경로. `| path | 이 경로를 만지는 계획 (실행 순서대로) |`
- 만지는 계획이 하나인 경로도 전부 적습니다. 스윕 대상은 둘 이상인 행입니다.
- 기본 위치는 `docs/superpowers/ledgers/YYYY-MM-DD-<campaign>.md`이고 사용자
  선호가 우선합니다.

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

### Degraded reasons

- `primary-role-not-obtained`
- `focused-role-not-obtained`
- `agent-reused-within-invocation`
- `agent-reused-across-plans`
- `other`

독립 1차 검토자를 구할 수 없으면 `BLOCKED`입니다. 짧은 degraded 회차로 대신하지
않습니다. 집중 위험 역할만 못 구하면 `degraded`이고 그 인계는 재사용하지
않습니다. 한 에이전트를 계획이 다른 호출에 돌려 쓰지 않습니다.

## 기본 흐름, 판정, freshness

한 호출은 발견 단계 한 번과 수정 최대 두 번, 범위 제한 재검토로
끝납니다. 첫 검토에서 발견이 없으면, 계획이 dirty가 아닐 때만 수리와
종료 재검토를 건너뛰고 `READY`입니다. dirty인 계획은 발견이 0건이어도
범위 제한 종결을 합니다. 종결에는 설계·계획·원장의 수리 diff가
필수입니다. HEAD 동결이 깨지면 그 동결에 대해 `READY`를 내지 않습니다.
앞 계획이 `BLOCKED`여도 뒤 계획의 발견은 진행합니다.

dirty는 컨트롤러 로컬 캠페인 상태이며, record 필드가 아니고 worktree dirty도
아닙니다. 계획 i를 수리한 뒤 Δ는 바뀐 해결 설계·계획·원장 지문, 영향 표의
심벌·경로·명령·소비자, 수리한 finding이 인용한 경로의 합집합입니다. 계획 j는
i가 앞이고 Δ가 j의 읽기집합과 겹치거나, j가 의존하는 공유 설계가 바뀐 때
dirty입니다. j의 읽기집합은 해결된 설계·계획·원장 경로와 해시, `Files:` 경로,
선행 계획 경로, 발견 기록 `evidence` 경로입니다. `Files:`에 없는 경로는 이
dirty 집합에 없습니다. 그 구멍은 기계점검이 잡습니다.

`repair_passes`는 실제로 `repaired` 발견이 나온 패스만
셉니다. `partially-closed`로 남은 발견은 판정에서 미해결로 계산되어
`REVISE`를 강제합니다. 새 호출은 이전 발견의 `repair_pass`를 복사하지 않습니다. 수정이
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
- `BLOCKED`: 필요한 입력·권위·저장소 증거가 없거나, 새 제품 결정이 필요하거나,
  독립 1차 검토자를 구할 수 없습니다.

아래 freshness 목록과 invalidation 규칙을 최종 보고에 그대로 기록합니다.

### Freshness

- repository-relative design path and SHA-256
- repository-relative plan path and SHA-256
- Git `HEAD` (or `unborn`)
- worktree was clean or dirty
- review timestamp
- final verdict
- baseline: `HEAD`, 또는 `HEAD`와 선행 계획 목록
- ledger: 저장소 상대 경로와 SHA-256 (없으면 생략)
- Any content change to either resolved document invalidates `READY`.

최종 보고는 입력·최종 문서 해시, 패스 번호, 발견 ID/분류, 영향 범위 트리거,
바뀐 문서 해시, 판정을 담은 짧은 패스 영수증을 포함합니다. `finish`가 돌려준
관찰 이상(`anomalies`)을 `Anomalies:` 줄로 그대로 적습니다. 비어 있으면 `none`, 기록기를
쓰지 않았거나 `finish`가 실패했으면 `not_recorded`입니다. 이 run을 윈도우가
있는 `summary`에서 찾지 않습니다. 이상이 판정을 바꾸지는 않습니다. `REVISE`와
`BLOCKED`는 미해결 발견과 다음 범위를 담은 인계 묶음을 반환합니다. 새 권위가
필요하면 판정은 `BLOCKED`입니다.

검토자가 완전한 PSDR 기록 없이 요약만 내면 그 검토자에게 한 번, 빠진 필드
이름만 들어 완전한 기록을 다시 받습니다. 의심되는 발견·경로·심볼·수정을
답을 넣어 재질의하지 않습니다. 요약을 발견으로 받지 않습니다.

권위를 보존하는 수정에는 승인 질문을 하지 않습니다. 사용자 권위가
필요하면 필요한 결정을 승인 요청 하나로 묶습니다. `REVISE`나
`BLOCKED` 뒤에 자동으로 다시 호출하지 않습니다. 문서, `HEAD`, 요청이 모두
바뀌지 않은 `full` run의 인계만 재사용합니다. `execution`이 `degraded` 또는
`blocked`인 run의 인계는 재사용하지 않습니다.

## 선택 기록기 계약

기록기는 선택 계약입니다. 권위 순서, 리뷰어 프로토콜, 수정 허용 목록, 판정
규칙을 바꾸지 않습니다. 컨트롤러는 로드된 스킬 루트에서
`python3 "<skill-root>/evidence/evidence.py" --version`을 실행하고,
handshake가 정확히 `skill_name=pre-sdd-review`와 `schema=4`일 때만
기록합니다. 정규 한 줄은
`{"cli_version":"5.0.0","schema":4,"skill_name":"pre-sdd-review"}` 뒤에
LF 하나입니다. 호환되면 `start` 전에 `summary --repo <표시 이름>`을 실행해
`runs`와 `chains`에서 그 계획을 찾습니다. 같은 `repo` 표시 이름과 계획 경로가
`pending`이면 그 run을 `abandon`합니다. 그 계획의 마지막 완료 판정이 `REVISE`
또는 `BLOCKED`이면 `show`합니다. `execution`이 `blocked`이면 인계를 재사용하지
않고 입력 게이트를 다시 확인한 뒤 `start`합니다. `execution`이 `degraded`이면
인계를 재사용하지 않고 새 전체 검토로 `start`합니다. `full`이면 문서 해시,
`git.head_end`, 요청이 모두 같을 때만 이전 인계를 재사용합니다. 아니면
의미 검토 전에 `start`하고, 판정과
수정이 끝난 뒤 `finish`를 한 번 호출합니다. `Evidence:` 줄은 정확히
하나입니다. 기록기가 없거나 실패하면
`Evidence: not_recorded; reason=<code>`를 보고하며, 이 실패가
`READY`, `REVISE`, `BLOCKED`를 바꾸지는 않습니다.

schema 2와 schema 3 record는 계속 읽습니다. 변경은 schema 4만 받습니다.
예외로 schema 3 pending은 `abandon`만 허용해 업그레이드 시점의 진행 중 run을
닫을 수 있게 합니다. schema 2는 `historical-unbound`이며 읽기 전용입니다.
`start`는 schema 4 checkout 결속 run을 만듭니다.

컨트롤러는 계획의 `**Spec:**`에서 설계 경로를 해석해 `--design`으로 넘깁니다.
해석할 수 없으면 `--design`을 생략하고 `BLOCKED`를 반환합니다. 기록기는
`**Spec:**`를 파싱하지 않습니다. `finish` 전에 끝나면 `abandon` 이유는
`user-cancelled`, `input-changed`, `scope-changed`, `input-format-fixed`,
`other` 중 하나입니다. `run_id`는 컨트롤러 로컬이며 검토 문서 밖에 둡니다.

schema 4 finding에는 `source`(`reviewer`, `ledger-pass`, `machine-check`)와
`repair_pass`(`null` 또는 0..3, `0`은 사전 패스의 원장·기계 점검 수리이고 `null`은
이 호출이 수리하지 않은 발견입니다)가 들어갑니다. `source`는 schema 4가 더한 키입니다. schema
2·3 finding에는 없고, 없는 채로 계속 읽힙니다. `source`를 가진 legacy finding은
`schema-invalid`입니다. schema 2·3의 `degraded_reasons`도 schema 4 어휘가 아니라
자유 문자열로 읽습니다.
`finding.evidence`는 산문이 아니라 저장소 상대 경로의 목록입니다.

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
`summary`, `--version`은 locking이 필요 없습니다. Windows는 지원하지 않습니다.

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
- 기록기 명령·schema 4: `skills/pre-sdd-review/evidence/evidence.py`,
  `evidence/README.md`, `tests/products/pre-sdd-review/evidence/`
- 호스트 지원: `products.toml`, `compatibility.md`, 공개 안내, 해당 테스트.
  이 작업에서 호스트 지원을 넓히지 않습니다.

## 하지 않는 것

아래는 명시적으로 추가하지 않습니다.

- closure-only input schema
- evidence probe cache

컨트롤러 로컬 dirty 집합이 이번 판의 무효화입니다.

## 인계

`READY`이면 해결된 설계와 계획의 정확한 경로와 final fingerprints를
출력합니다. 검토와 구현이 이어지는 흐름에서는 고치기 전 복사본이 아니라
최종 문서를 SDD worker에게 넘깁니다.

### SDD handoff

바깥 요청이 구현을 명시하지 않으면 SDD를 시작하지 않습니다.

### Contract

- `primary-input`: `plan-primary`, `spec-resolves-design`
- `plan-cardinality`: `one-plan-per-verdict-bearing-invocation`, `no-aggregate-ready`
- `editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`, `resolved-shared-file-ledger`
- `ledger`: `pre-pass-no-verdict`, `derived-not-authority`
- `baseline`: `plan-turn-reality`
- `review-only`: `no-mutation`
- `repair-flow`: `review-repair-bounded-impact-re-review`
- `repair-impact`: `structural-trigger-only`, `direct-consumers`
- `repair-passes`: `at-most-two`, `costless-repairs-uncounted`
- `verdicts`: `READY`, `REVISE`, `BLOCKED`
- `second-reviewer`: `conditional-only`, `no-cross-plan-reuse`
- `risk-triggers`: `framework-runtime-removal`, `schema-data-deletion`, `auth-security-boundary`, `data-boundary-change`, `external-side-effects`
- `freshness`: `fingerprints`, `content-change-invalidates`
- `required-base`: `pre-dispatch-ancestor-check`
- `handoff`: `unresolved-packet`, `full-execution-only`
- `sdd`: `outer-request-implementation-only`
- `evidence`: `optional`, `non-blocking`, `controller-local-run-id`
- `campaign-scheduler`: `discoveries-may-overlap`, `repairs-do-not-overlap`
