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

## Exact fixture boundary

`cases.json`은 exactly fourteen개의 activation, default-flow, review-only,
verdict, risk, freshness, near-miss 사례를 소유합니다. `fixtures/`는 정확히
`ready`, `missing-coverage`, `false-verification`, and `runtime-removal` 네 합성
저장소를 소유합니다. 각 저장소에는 `design.md`, `plan.md`,
`repository.json`, and `expected.json`만 둡니다.

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
- `stale-document-hash`
- `near-miss-write-spec`
- `near-miss-write-plan`
- `near-miss-code-review`
- `near-miss-release-review`

### Fixture inventory

- `false-verification`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `missing-coverage`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `ready`: `design.md`, `expected.json`, `plan.md`, `repository.json`
- `runtime-removal`: `design.md`, `expected.json`, `plan.md`, `repository.json`

## Optional fresh-session live checks

live check는 local, explicit, optional이며 billable일 수 있고 CI never
requires it. fresh Codex session과 non-sensitive synthetic design and plan만
사용하고, record only host, client version, date, case identifier, and verdict.
provider-free 결과를 live quality 주장으로 바꾸지 않으며 user documents나
full model responses를 저장하지 않습니다.
