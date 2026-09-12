# pre-sdd-review 테스트

이 문서는 provider-free contract evidence, 제한된 합성 픽스처, 선택적
live-check 경계를 소유합니다. 모델의 실제 리뷰 품질을 측정했다고 주장하지
않습니다.

공급자 없는 픽스처 경로는 `tests/products/pre-sdd-review/`입니다.

## 공급자 없는 증거

공급자 자격 증명과 모델 호출 없이 제품 계약을 실행합니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p test_contract.py -v
```

이 명령은 패키지 정체, 지시문, 픽스처 형태, 활성화 경계, 문서화된 계약
사실을 확인합니다. 라이브 검토, 의미 품질, 다른 호스트의 동등 지원은
증명하지 않습니다.

`evidence/evidence.py` 기록기의 schema 3 checkout 결속, schema 2 read-only
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

`test_contract.py`의 schema 3 문서 assertion은 설치 지시문, 기록기 안내,
maintainer contract가 같은 lifecycle을 설명하는지 확인하는 일관성 증거입니다.
실제 recorder 동작 증거는 evidence suite가 소유합니다. 이 승인 범위에서는
provider나 실제 모델을 호출하지 않으므로 실제 모델 리뷰 품질은
`not_measured`입니다.

## 픽스처 경계

`cases.json`은 활성화, 기본 흐름, review-only, 판정, 위험, freshness,
evidence, near-miss 사례를 정확히 스물여덟 개 소유합니다. `fixtures/`는 정확히
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
- `near-miss-write-spec`
- `near-miss-write-plan`
- `near-miss-code-review`
- `near-miss-release-review`

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

Evidence 테스트는 임시 Git 저장소와 합성 skill root만 사용합니다. 원문,
경로 원본, 프롬프트, 대화 기록, 자격 증명을 기록에 넣지 않습니다. `outcome`
label과 정상/이상 verdict 분리는 관찰자 입력이며 모델 품질이나 감사급 증명이
아닙니다. 손상 record 수는 filter 전 전체 scan에서 확인합니다. native
Windows, Linux, Claude Code, Cursor, Grok은 각 native 또는 live 단계가
별도로 실행되기 전까지 `not_measured`입니다.
