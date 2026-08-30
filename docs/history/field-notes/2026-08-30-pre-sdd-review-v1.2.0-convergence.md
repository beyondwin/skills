# Pre-SDD Review v1.2.0 수렴성 현장 관찰

- **상태:** point-in-time observation; non-authoritative
- **관찰일:** 2026-08-30
- **대상 제품:** `pre-sdd-review` 1.2.0
- **관찰 기준 소스:** Git `08e8402`
- **범위:** 하나의 공유 설계와 세 개의 plan-local review로 구성된 공개 RAG vertical slice

## 결론

v1.2.0은 plan-local verdict, 권위 순서, 조건부 위험 검토, 두 번의 repair 제한을
통해 잘못된 `READY`를 막는 데 효과가 있었다. 반면 closure가 새로운 전체 검토로
확장될 때 reviewer 수와 발견 범위가 계속 늘어나는 것을 controller가 명시적으로
차단하지 못했다.

핵심 개선 후보는 정확성을 낮추는 finding 수 제한이 아니라 다음 수렴 규칙이다.

> Repair-impact map 밖에서 새 material finding이 발견되면 현재 invocation을
> 확대하지 않는다. 기존 verdict 규칙에 따라 `REVISE` 또는 `BLOCKED` handoff로
> 종료하고 새 invocation을 자동 시작하지 않는다.

## 계약 근거

현재 계약은 다음을 이미 요구한다.

1. 한 invocation은 구현 계획 하나만 검토하고 aggregate `READY`를 만들지 않는다.
2. 기본 reviewer는 한 명이며 두 번째 reviewer는 정해진 위험 조건에서만 추가한다.
3. repair 후 검토는 original findings와 repair-impact map을 중심으로 한 bounded
   regression이며 새로운 전체 검토가 아니다.
4. repair는 최대 두 번이고, 두 번째 repair 후 material issue가 남으면 `REVISE`다.

근거 문서:

- [`skills/pre-sdd-review/SKILL.md`](../../../skills/pre-sdd-review/SKILL.md)
  - `Resolve authoritative inputs`
  - `Select reviewers`
  - `Default mode: review -> repair documents -> scoped re-review`
- [`reviewer-protocol.md`](../../../skills/pre-sdd-review/references/reviewer-protocol.md)
  - `Review passes`
  - “Do not expand this into an unrelated full review.”
- [maintainer contract](../../maintainers/products/pre-sdd-review/contract.md)
  - `Conditional risk triggers`
  - `Default flow, verdicts, and freshness`

## 관찰된 실행

### 효과가 있었던 부분

- 세 계획을 독립 invocation으로 나눠 plan-local verdict를 유지했다.
- 공개·비공개 데이터 경계와 외부 provider가 있어 조건부 security reviewer를
  추가한 것은 trigger 집합에 부합했다.
- shared design 변경이 이전 판단에 영향을 주는지 다시 확인했다.
- runtime 계획은 두 번의 repair 뒤에도 material security finding이 남자
  `REVISE`로 멈췄다. repair limit가 false-ready를 방지했다.
- late closure findings는 loader 데이터 경계, provider timeout, referrer,
  forwarding identity, BFCache와 reduced-motion geometry처럼 실제로 틀린 구현이
  통과할 수 있는 반례를 제시했다. finding 자체를 잡음으로 취급할 근거는 없다.

### 수렴하지 못한 부분

| 관찰 | 현재 계약 | 실행상 결과 | 위험 |
| --- | --- | --- | --- |
| Provider closure에 primary, security, UX 세 관점이 동시에 투입됨 | 기본 한 명, 조건부 두 번째 한 명 | reviewer budget이 세 명으로 확장됨 | 같은 문서를 서로 다른 전체 관점으로 반복 탐색 |
| Closure prompt가 complete documents에서 새로운 omission을 찾도록 요구함 | original closure + bounded repair-impact regression | 기존 repair와 직접 관계없는 새 finding이 계속 추가됨 | closure가 사실상 다음 full review가 됨 |
| 새 finding이 repair 영향인지 기존 잠복 결함인지에 따른 routing 규칙이 없음 | 두 번째 repair까지 허용 | 새 finding이 나올 때마다 현재 invocation에서 고칠 유인이 생김 | 두 번 제한을 새 invocation으로 우회할 가능성 |
| Shared design 변경 시 invalidation 단위가 “의존한 계획”으로만 표현됨 | 영향받은 이전 계획을 재검토 | 어떤 design claim에 의존했는지 controller 판단이 반복됨 | 무관한 계획까지 재검토하거나 필요한 재검토를 놓침 |
| 둘 다 문서상 가능하지만 제품 동작이 다른 repair 후보가 나타남 | product intent 변경은 `BLOCKED` | controller가 더 안전해 보이는 안을 고를 유인이 있음 | authority-preserving repair와 새 제품 결정의 경계가 흐려짐 |

## 근본 원인

문제는 reviewer가 많다는 사실만이 아니다. 다음 세 계약 사이의 연결이 충분히
명시되지 않았다.

1. conditional reviewer의 **invocation별 최대 인원**;
2. closure에서 허용되는 **새 finding의 출처**;
3. repair-impact map 밖 material finding의 **종료 경로**.

현재 문구는 bounded regression을 요구하지만, fresh reviewer가 완전한 문서를
읽는 과정에서 발견한 별도 material issue를 어떻게 처리할지 규정하지 않는다.
정확한 reviewer는 이를 무시할 수 없고, controller는 현재 invocation을 다시
확대하게 된다.

## v1.3.0 반영

관찰 뒤 승인된 최소 규칙을 v1.3.0에 반영했다. 새 ledger나 closure schema는
추가하지 않았다.

### Review role과 repair 범위

- 한 invocation의 논리적 review role은 primary와 조건부 risk의 최대 두 개다.
- fresh re-review는 agent를 바꿀 수 있지만 role이나 risk class를 추가하지 않는다.
- 전체 최종 문서에서 finding을 탐지할 수 있지만 현재 repair에 넣는 finding은
  original finding 또는 direct mapped repair impact뿐이다.

### 승인과 종료

- authority-preserving document repair는 사용자 승인을 요구하지 않는다.
- 새 제품 결정이 필요한 항목은 나눠 묻지 않고 하나의 `BLOCKED` checkpoint로
  모은다.
- map 밖 material finding은 버리지 않고 기존 verdict 규칙에 따라 `REVISE` 또는
  `BLOCKED` handoff로 반환한다.
- 한 invocation은 discovery 한 번, repair 최대 두 번, scoped closure에서 끝난다.
- terminal verdict 뒤 새 invocation을 자동 시작하지 않는다. 문서 fingerprint,
  권위 또는 저장소 증거가 바뀌지 않았다면 같은 검토를 반복하지 않는다.

## 보류하거나 제외한 후보

- Closure 전용 입력 schema: 기존 original findings와 repair-impact map이면 충분하다.
- Shared-design invalidation map: plan-local skill 밖 orchestration 문제이므로 반복
  관찰 전에는 추가하지 않는다.
- Program ledger: aggregate program mode로 커질 가능성이 있어 제외한다.
- Evidence capability probe cache: 성능 효과가 측정되지 않았고 invocation 사이의
  설치·권한 변화를 놓칠 수 있어 제외한다.
- Authority-choice 문구 추가: 기존 `BLOCKED` 계약에 이미 있으므로 중복하지 않고
  회귀 사례로만 고정한다.

## v1.3.0 검증 사례

최소 provider-free case는 다음 세 개다.

1. `third-review-role`: primary와 conditional risk 뒤 제3 role을 거부하되 fresh
   closure agent 교체는 허용한다.
2. `unmapped-repairable-finding`: map 밖 repairable finding은 추가 repair 없이
   `REVISE` handoff로 종료하고 자동 재호출하지 않는다.
3. `unmapped-authority-finding`: map 밖 finding이 새 제품 결정을 요구하면 하나의
   `BLOCKED` checkpoint로 종료하고 자동 재호출하지 않는다.

## 비목표

- finding 수나 심각도를 임의로 제한하지 않는다.
- 조건부 security reviewer를 제거하지 않는다.
- shared design 변경 뒤 필요한 재검토를 생략하지 않는다.
- 여러 plan의 verdict를 하나의 aggregate `READY`로 합치지 않는다.
- repository reality를 승인된 제품 결정의 대체 권위로 사용하지 않는다.

## 증거 한계

이 문서는 한 번의 복합 실행에서 확인한 수렴성 관찰이다. 실행 시간, token 사용량,
다른 host나 모델에서의 발생 빈도는 측정하지 않았다. 원문 reviewer 응답과 consumer
repository의 절대 경로는 보관하지 않았다. 계약 사례는 추가했지만 일반성은 아직
측정하지 않았다.
