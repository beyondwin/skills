# pre-sdd-review 테스트

이 문서는 provider-free contract evidence, 제한된 합성 픽스처, 선택적
live-check 경계를 소유합니다. 모델의 실제 리뷰 품질을 측정했다고 주장하지
않습니다.

공급자 없는 픽스처 경로는 `tests/products/pre-sdd-review/`입니다.

## 공급자 없는 증거

공급자 자격 증명과 모델 호출 없이 제품 계약을 실행합니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_c*.py' -v
```

이 명령은 `test_contract.py`(패키지 정체, 지시문, 픽스처, 활성화 경계)와
`test_campaign_schedule.py`(발견 웨이브, 수리 직렬, dirty 전파)를 함께
돌립니다. evidence 하위 스위트는 포함하지 않습니다. 라이브 검토, 의미 품질,
다른 호스트의 동등 지원은 증명하지 않습니다.

`evidence/evidence.py` 기록기의 schema 4 checkout 결속, schema 2 read-only
legacy 처리, mutation lock, 손상 record 격리, 여섯 명령, summary 관찰 집계
계약은 별도 공급자 없는 단계로 실행합니다. 기록기는
`python3 skills/pre-sdd-review/evidence/evidence.py`로 돌리며 설치하지
않습니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
```

이 단계는 네트워크나 공급자를 호출하지 않습니다. DB나 index도 추가하지
않습니다.

`test_contract.py`의 schema 4 문서 assertion은 설치 지시문, 기록기 안내,
maintainer contract가 같은 lifecycle을 설명하는지 확인하는 일관성 증거입니다.
실제 recorder 동작 증거는 evidence suite가 소유합니다. 이 승인 범위에서는
provider나 실제 모델을 호출하지 않으므로 실제 모델 리뷰 품질은
`not_measured`입니다.

## 픽스처 경계

`cases.json`은 활성화, 기본 흐름, review-only, 판정, 위험, freshness,
evidence, near-miss 사례를 정확히 마흔하나 개 소유합니다. `fixtures/`는 정확히
`ready`, `missing-coverage`, `false-verification`, `runtime-removal`,
`repair-induced-schema-consumer`, `state-machine-vacuous-pass`,
`conditional-edit-surface` 일곱 합성 저장소를 소유합니다. 각 저장소에는
`design.md`, `plan.md`, `repository.json`, `expected.json`만 둡니다.

픽스처는 제한된 합성 계약이지 말뭉치가 아닙니다. 사용자 문서, 비공개
프롬프트, 자격 증명, 대화 기록, 모델 응답 전체를 픽스처,
테스트 로그, 커밋된 live record에 저장하지 않습니다.

### Case inventory

- `default-auto-improve`
- `explicit-review-only`
- `ready-zero-findings`
- `missing-spec-coverage`
- `nonexistent-command`
- `extension-collision`
- `false-positive-smoke`
- `task-interface-order`
- `runtime-removal-risk-review`
- `third-review-role`
- `unmapped-repairable-finding`
- `unmapped-authority-finding`
- `stale-document-hash`
- `required-base-not-in-head`
- `ambiguous-multiple-plans`
- `evidence-cli-recorded`
- `evidence-cli-unavailable`
- `evidence-review-only`
- `evidence-resolution-blocked`
- `evidence-outcome-optional`
- `summary-before-start`
- `serialize-split-plans`
- `zero-findings-skip-closure`
- `repair-pass-accounting`
- `red-flag-seeded-retry`
- `red-flag-anomalous-ready`
- `blocked-execution-restarts`
- `near-miss-write-spec`
- `near-miss-write-plan`
- `near-miss-code-review`
- `near-miss-release-review`
- `ledger-required-for-multiple-plans`
- `baseline-reconstruction-required`
- `partial-closure-not-a-new-finding`
- `degraded-handoff-not-reused`
- `zero-findings-but-dirty`
- `closure-requires-repair-diff`
- `host-limit-waves-not-reuse`
- `head-break-no-ready`
- `no-automatic-second-campaign`
- `residual-pass-closes-small-remainder`
- `open-blocker-forces-blocked`
- `repair-last-no-ready`
- `unanswered-decision-no-redispatch`
- `three-new-decisions-return-to-design`

### Fixture inventory

- `conditional-edit-surface`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `false-verification`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `missing-coverage`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `ready`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `repair-induced-schema-consumer`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `runtime-removal`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `state-machine-vacuous-pass`: `design.md`, `expected.json`, `plan.md`, `repository.json`

## 선택적 라이브 검사

라이브 검사는 로컬이고, 명시적이며, 선택적입니다. 비용이 들 수 있습니다.
CI는 요구하지 않습니다. 새 Codex 세션과 민감하지 않은 합성 설계·계획만
사용합니다. 기록은 호스트, 클라이언트 버전, 날짜, 사례 식별자, 판정만 남깁니다.
공급자 없는 결과를 라이브 품질 주장으로 바꾸지 않습니다. 사용자 문서나
모델 응답 전체를 저장하지 않습니다.

v1.1 전진 확인은 정답을 숨긴 채 `repair-induced-schema-consumer`,
`state-machine-vacuous-pass`, `conditional-edit-surface`를 각각 따로 호출합니다.
각 호출은 그 계획만의 판정을 유지합니다. 잘못된 `READY`, 관련 없는 수정,
권위 이탈이 없어야 합니다. 기존 `ready` 픽스처는 공급자 없는 긍정 대조입니다.
이 점검은 반복 평가나 일반 품질 측정을 대신하지 않습니다.

컨트롤러 경계 프로브는 실제 모델에 정해진 중간 상태를 주입해 SKILL.md의
분기 하나를 확인합니다. 합성 Git 저장소와 비어 있는 evidence home을 만들고,
모든 `evidence.py` 호출에 `PRE_SDD_REVIEW_HOME`을 그 home으로 고정합니다.
기본 home `~/.pre-sdd-review/`에 프로브 기록을 남기지 않습니다. 컨트롤러에는
SKILL.md와 스킬 루트만 주고 정답이나 기대 결과는 주지 않습니다. 결과는
컨트롤러가 쓴 결정 파일이나 보고 파일로 채점합니다.

- 변경된 저장소 근거 재검토: 계획에 required base를 적고, 그 ref가 없는
  상태로 `execution=blocked`, `reviewers=0`인 `BLOCKED` 기록을 만든 뒤 ref를
  `HEAD`에 만듭니다. 문서 해시는 그대로입니다. 컨트롤러가 `start`에 이르면
  통과입니다. 이전 인계를 재사용하면 실패입니다.
- 불완전 기록 재질의: 리뷰어가 요약과 판정만 돌려준 상황을 주고 다음
  메시지를 파일로 받습니다. 빠진 필드만 요청하고 발견·경로·심볼·수정을
  넣지 않으면 통과입니다.
- 이상 있는 READY 보고: `reviewers=2`, trigger 없음으로 `finish`한 기록을
  주고 최종 보고를 받습니다. `Anomalies:` 줄에
  `full_reviewer_count_mismatch`가 있고 `READY`가 유지되면 통과입니다.
- 윈도우 밖 run 보고: 위와 같되 그 run이 시작된 뒤 다른 저장소의 run 스무
  개를 시작하고 끝낸 다음 그 run을 `finish`합니다. `Anomalies:` 줄이 그
  run의 이상을 보이면 통과입니다. `finish` 출력이 아닌 `summary --last`에서
  찾으려 하면 누락됩니다.

이 프로브는 선택이며 CI가 요구하지 않습니다. 사례당 한 번의 결과는 모델
품질 측정이 아닙니다.

Evidence 테스트는 임시 Git 저장소와 합성 skill root만 사용합니다. 원문,
경로 원본, 프롬프트, 대화 기록, 자격 증명을 기록에 넣지 않습니다. `outcome`
label과 정상/이상 verdict 분리는 관찰자 입력이며 모델 품질이나 감사급 증명이
아닙니다. 손상 record 수는 filter 전 전체 scan에서 확인합니다. Windows와
Linux는 지원하지 않습니다. Claude Code, Cursor, Grok은 각 native 또는 live
단계가 별도로 실행되기 전까지 `not_measured`입니다.
