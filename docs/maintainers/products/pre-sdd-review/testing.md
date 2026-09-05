# pre-sdd-review 테스트

이 문서는 provider-free contract evidence, 제한된 합성 픽스처, 선택적
live-check 경계를 소유합니다. 모델의 실제 리뷰 품질을 측정했다고 주장하지
않습니다.

## Required provider-free command

공급자 자격 증명과 모델 호출 없이 제품 계약을 실행합니다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review -p 'test_contract.py' -v
```

이 명령은 package identity, instructions, fixture shape, activation boundary,
documented contract fact를 확인합니다. live review, semantic quality, 다른
호스트의 동등 지원은 증명하지 않습니다.

공유 evidence CLI의 schema, repository identity, create-only storage,
outcome, reporting, installer 계약은 별도 provider-free 단계로 실행합니다.
Installed command identity is `pre-sdd-review-evidence`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests/products/pre-sdd-review/evidence -p 'test_*.py' -v
```

이 단계는 네트워크나 provider를 호출하지 않습니다. 수천 개의 bounded 합성
receipt를 사용한 summary/candidates 규모 검사도 Python 표준 라이브러리 안에서
실행하며 DB나 index를 추가하지 않습니다.

## Exact fixture boundary

`cases.json`은 exactly twenty-four개의 activation, default-flow, review-only,
verdict, risk, freshness, evidence, near-miss 사례를 소유합니다. `fixtures/`는 정확히
`ready`, `missing-coverage`, `false-verification`, `runtime-removal`,
`repair-induced-schema-consumer`, `state-machine-vacuous-pass`, and
`conditional-edit-surface` 일곱 합성 저장소를 소유합니다. 각 저장소에는
`design.md`, `plan.md`, `repository.json`, and `expected.json`만 둡니다.

픽스처는 bounded synthetic contract이지 corpus가 아닙니다. user documents,
private prompts, credentials, transcripts, full model responses를 픽스처,
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

## Optional fresh-session live checks

live check는 local, explicit, optional이며 billable일 수 있고 CI never
requires it. fresh Codex session과 non-sensitive synthetic design and plan만
사용하고, record only host, client version, date, case identifier, and verdict.
provider-free 결과를 live quality 주장으로 바꾸지 않으며 user documents나
full model responses를 저장하지 않습니다.

v1.1 전진 확인은 정답을 숨긴 채 `repair-induced-schema-consumer`,
`state-machine-vacuous-pass`, `conditional-edit-surface`를 각각 따로 호출합니다.
각 호출은 그 계획만의 판정을 유지하고, 잘못된 `READY`, 관련 없는 수정, 권위
이탈이 없어야 합니다. 기존 `ready` 픽스처는 공급자 없는 긍정 대조입니다. 이
점검은 반복 평가나 일반 품질 측정을 대신하지 않습니다.

Evidence lifecycle 픽스처는 source text, raw path, prompt, transcript,
credential을 bounded reason/finding에 넣지 않고 짧은 합성 paraphrase만
사용합니다. Outcome label과 confidence는 관찰자 입력이며 audit-grade proof가
아닙니다. native Windows, Linux, Claude Code, Cursor, Grok은 각 native 또는
live 단계가 별도로 실행되기 전까지 `not_measured`입니다.
