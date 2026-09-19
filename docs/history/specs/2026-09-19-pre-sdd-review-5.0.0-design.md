# pre-sdd-review 5.0.0 캠페인 스케줄 설계 스펙

상태: 구현 전 설계. 이 문서는 현재 제품 계약을 변경하지 않는다.

기준: pre-sdd-review `4.0.0`, 저장소 `40f9374`, 2026-09-19.
근거: 승인된 브레인스토밍(접근=A 안쪽 루프 + B 2단계 스케줄),
won-sec-ai 캠페인 기록 57회, `afd15218b`의 `Files:` 그래프,
현장 기록은 입력이지 구현 목록이 아니다.
실행 문서: [구현 계획](../plans/2026-09-19-pre-sdd-review-5.0.0.md).

## 1. 목표와 선택

`4.0.0`은 교차면을 선행 원장으로 옮겼다. 캠페인 57회는 사슬이 짧아지지
않았다. 합산 34.5시간 중 한 바퀴 중앙값 합은 3.3시간이고, 49회가 재호출이다.
호출 전체를 겹치면 `Files:` 충돌이 빽빽해 1.3배뿐이다.

**읽기(발견)는 겹치고 쓰기(수리)는 직렬로 두며, 종결은 수리 diff만 보고,
REVISE 뒤에 자동으로 다음 호출을 열지 않는다.**

| 대안 | 판단 |
| --- | --- |
| 안쪽 루프만 (diff 종결, 자동 재호출 금지) | 31시간은 재호출이라 1순위다. 뒤 계획은 계속 쉰다. 부분만. |
| 호출 전체 병렬 | 실측 1.3배. plan-turn을 깬다. 제외. |
| A+B | 루프와 스케줄을 한 상태기계로. 채택. |

## 2. Global Constraints

- 수정 대상은 `skills/pre-sdd-review/`, `tests/products/pre-sdd-review/`,
  `docs/maintainers/products/pre-sdd-review/`,
  `tests/repository/test_release_contract.py`다.
- 제품 버전은 `5.0.0`, 날짜는 `2026-09-19`다. record schema는 `4`로 둔다.
  handshake `cli_version`은 제품과 맞춰 `5.0.0`이다.
- 새 실행 파일·원장 파서·dirty record 키를 만들지 않는다. 스케줄 규칙은
  SKILL.md가 소유하고, 합성 그래프 테스트만 추가한다.
- Python 3.11 이상, 표준 라이브러리만 쓴다.
- 호스트 지원을 넓히지 않는다. `compatibility.md`와 `products.toml`은 수정하지
  않는다. 지원 OS는 macOS만이다.
- 권위 순서, 수정 허용 목록, 판정 어휘, 역할 상한 둘, 수리 패스 상한 둘,
  `no-aggregate-ready`, `review-only` 무수정은 유지한다.
- 사용자 문서 원문·모델 응답·자격 증명은 픽스처에 넣지 않는다.
- 태그와 GitHub Release는 만들지 않는다.
- 라이브 `--execute`는 이번 범위가 아니다.

## 3. 바깥 스케줄러와 계획 로컬 호출 — R1

캠페인은 바깥 스케줄러다. 역할 상한·수리 패스·판정·기록 run은 계획 로컬
호출에 남는다. 캠페인을 하나의 거대 호출로 만들지 않는다.

바깥 요청이 계획을 둘 이상 이름 대면 아래 기계를 돈다. 계획 하나면 `n=1`이다.

```text
0 동결  순서 → 원장 → 기계점검 → 반입 수리 → 문서 해시 H0, HEAD H_git0
1 발견  계획마다 신선 리뷰어, 읽기만, 판정 없음. k명이면 k명씩 웨이브
2 수리  실행 순서대로 컨트롤러만 수정. 동시에 하나. 계획당 ≤2패스
3 종결  수리 diff ∪ 영향 표 ∪ dirty 계획만. 읽기이므로 한도 안에서 병렬
4 판정  계획 로컬 READY | REVISE | BLOCKED. 자동으로 다시 열지 않음
```

`Resolve authoritative inputs`의 "On one host, run those invocations one after
another; do not overlap them"을 분리한다. **발견은 겹칠 수 있다. 수리는
겹치지 않는다.** `P=1`이면 발견도 직렬이며 합법이다.

0단계는 지금처럼 판정 없는 패스다. 별도 `ledger-pass` run 종류는 만들지 않는다.
원장 해시는 각 계획 `start`의 `--ledger`로 들어간다. 같은 repo·다른 계획의
`pending` 겹침은 허용한다. 같은 계획 `pending`은 지금처럼 먼저 닫는다.

## 4. 발견 지시와 jobserver — R2

발견 지시는 지금 프로토콜과 같다. 더하는 것은 동결뿐이다.

- 기준선: `HEAD` ⊕ 선행 계획. 문서는 H0 해시 본문. 응답 첫 줄에 재구성 진술.
- 원장 경로와 H0 해시. 원장은 증거이지 권위가 아니다.
- Task 단위로 읽기, 되풀이 갈래 넷, PSDR 형식.
- 이 캠페인의 finding, 다른 계획의 발견 결과, “이것을 고쳤다”는 넣지 않는다.

한도: 신선 1차를 한 명도 못 구하면 그 계획만 `BLOCKED`. 컨트롤러로 대체하지
않는다. 빈자리를 재사용으로 채우지 않는다. `k`명이면 `k`명씩 웨이브한다.
집중 위험 역할만 없으면 지금처럼 그 계획 `execution=degraded`.

선행 계획이 `BLOCKED`여도 후행 발견은 돈다. 후행 `READY`를 선행에 묶지 않는다.

## 5. dirty와 수리 — R3

계획 `j`의 읽기집합: 해결된 설계·계획·원장 경로와 해시, `Files:` 경로, 선행
계획 경로, 발견 기록 `evidence` 경로.

계획 `i` 수리 뒤 Δ: 바뀐 설계·계획·원장 지문, 영향 표의 심벌·경로·명령·소비자,
수리한 finding이 인용한 경로.

`j`가 dirty인 경우: `i`가 앞이고 Δ가 읽기집합과 겹치거나, `j`가 의존하는 공유
설계 지문이 바뀌었다. 앞 계획이 공유 설계를 바꾸면 새 캠페인을 열지 않고
3단계 dirty로 본다.

`Files:`에 없는 경로는 이 집합에 없다. 기계점검 여섯째: 계획이 백틱으로 대는
경로가 그 계획의 turn에 있는지. 제외는 사슬 전체 `Create:`. 인용하지 않은
경로는 dirty가 아니라 발견의 `repo-reality`다.

안쪽 순서:

1. 실행 순서로 1차 수리. Δ마다 dirty 갱신.
2. 수리가 있었거나 dirty인 계획만 종결. 한도 안에서 병렬.
3. 적격 2차 수리가 있으면 순서대로 2차 수리 → dirty → 2차 종결. 계획당 여기까지.
4. 발견 0건이고 dirty가 아니면 종결 없이 `READY`. dirty이면 종결을 탄다.

오라클(구현 때 타입체크·테스트가 잡을 것)을 리뷰어에게 “플래그하지 마라”고
하지 않는다. 컨트롤러가 수리할 수는 있고, 그것만으로 긴 종결 리뷰어를 부르지
않는다. 영향 표가 비면 값 없는 수리로 끝낸다. 고치지 않고 남기면 미해결이라
`REVISE`. `READY`의 뜻은 바꾸지 않는다.

dirty 집합은 사용자 문서가 아니라 컨트롤러 로컬 상태다. 4.0.0 계약의
`shared-design invalidation map` 금지를 이것으로 대체한다.
`closure-only input schema`는 넣지 않는다.

## 6. 종결 지시 — R4

종결 지시에 수리 diff를 필수로 붙인다. 영향 표가 비는 스칼라 수정도 diff는
있다.

- 열린 PSDR 원문 (컨트롤러 요약 금지)
- 수리 diff (설계·계획·원장)
- 영향 표 (구조 트리거가 있을 때만 본문)
- 기계점검 결과
- 아직 아무 기록도 가리키지 않은 Task 목록

현재 수리 대상은 원 기록 또는 직접 매핑된 영향뿐이다. class+갈래가 같으면
위치가 달라도 unmapped가 아니다. unmapped 중요 발견은 패스를 넓히지 않고
`REVISE` 인계다.

## 7. 실패, HEAD, review-only — R5

| 상황 | 동작 |
| --- | --- |
| Spec 미해결, required-base 아님 | 그 계획만 `BLOCKED` |
| 신선 1차 0명 | 그 계획만 `BLOCKED`, 재사용 금지 |
| 집중 위험만 없음 | `degraded`, 인계 재사용 금지 |
| 제품 결정을 바꾸는 수리 | `BLOCKED`, 승인 요청 하나 |
| unmapped 중요 발견 | `REVISE` 인계 |
| 불완전 PSDR | 그 리뷰어에게 한 번, 빠진 필드만 |
| `Files:` 없음, 순서 불가 | 멈추고 물음 |
| 기록기 실패 | 검토 계속, `Evidence: not_recorded` |
| 캠페인 중단 | 열린 run `abandon` |
| 최종 REVISE/BLOCKED | 인계 후 종료. 자동 재호출 없음 |

0단계에서 `H_git0`를 찍는다. 캠페인 중 `HEAD != H_git0`이면 동결이 깨진 것이다.
이상은 기록한다. 그 HEAD에 대해 READY를 내지 않는다. 열린 run은
`input-changed`로 닫는다. 새 HEAD로 0단계부터 다시 여는 것은 바깥 요청이 있을
때만이다. `head_changed_during_review`는 좁히지 않는다.

`review-only`는 원장을 메모리에만 두고 반입 수리가 없다. 발견만 병렬로 돌리고
그 결과로 계획 로컬 판정한다. 2·3단계는 없다.

## 8. 테스트와 문서 — R6

공급자 없는 계약이 1차 증거다. 라이브 모델 품질은 `not_measured`다.

1. `test_contract.py`의 `"do not overlap them"` 단언을 분리한다. 발견 겹침
   허용, 수리 겹침 금지, 종결에 수리 diff 필수, dirty면 0건이어도 종결,
   한도에서 재사용 금지, 자동 재호출 금지를 단언한다.
2. `cases.json` `serialize-split-plans` expect를
   `discoveries_may_overlap`, `repairs_do_not_overlap`, `no_aggregate_ready`,
   `reviewers_are_distinct_agents`로 바꾼다. 사례를 더한다:
   `zero-findings-but-dirty`, `closure-requires-repair-diff`,
   `host-limit-waves-not-reuse`, `head-break-no-ready`,
   `no-automatic-second-campaign`.
3. `tests/products/pre-sdd-review/test_campaign_schedule.py`에 합성 그래프
   하나(계획 넷, `Files:` 교집합, 선행 순서, 호스트 `k=2`)를 둔다. 웨이브 폭,
   수리 직렬, dirty 전파, 재사용 0을 단언한다. 제품 런타임 모듈은 없다.
   규칙 함수는 테스트 파일에만 둔다.
4. 기록기는 같은 계획 `pending`만 컨트롤러가 닫는다. 다른 계획 겹침을 거부하는
   코드가 있으면 같은 계획으로 좁힌다. 지금은 `start`가 거부하지 않는다.
5. testing.md 사례 수와 인벤토리를 맞춘다. 선택 라이브 프로브를 CI에 넣지 않는다.

필수: `python3 scripts/verify.py --skill pre-sdd-review`. 머지 전
`python3 scripts/verify.py`.

함께 고칠 파일은 지금 계약과 같다. README 두 벌은 겹침 규칙과 종결 diff,
자동 재호출 금지를 같은 뜻으로 적는다.

## 9. 하지 않는 것

- `ledger-pass` run 종류, dirty를 record 필드로 넣기, `outcome`을 컨트롤러 일로.
- `summary` 낡음 명령, `elapsed_s` 이름 변경, 변경 파일 수 기록(관측은 선택).
- 리뷰어 토론, 학습 메모리, HEAD 기준 추측 리뷰, 파일 락으로 발견 스케줄.
- 집계 `READY`, 새 실행 스크립트, 원장 파서, 호스트 확대, 라이브 `--execute`.
- 현장 리포트 8절의 나머지 항목. A+B에 없으면 다음 판이다.

## 10. 완료 기준

- SKILL.md에 발견 겹침 허용과 수리 겹침 금지가 있고, `do not overlap them`이
  쓰기를 가리지 않은 채 남아 있지 않다.
- 종결 지시에 수리 diff가 필수다.
- dirty면 발견 0건이어도 종결한다. dirty가 아니고 0건이면 종결을 건너뛴다.
- 한도로 1차를 재사용하지 않는다. REVISE 뒤 자동 재호출이 없다.
- `test_campaign_schedule.py`가 재사용 0과 수리 직렬을 통과한다.
- handshake가 `{"cli_version":"5.0.0","schema":4,"skill_name":"pre-sdd-review"}`
  이다.
- `python3 scripts/verify.py --skill pre-sdd-review`와 `python3 scripts/verify.py`가
  exit 0이다.
- `python3 scripts/release.py check --product pre-sdd-review`는 커밋 뒤 작업
  트리가 깨끗할 때 통과한다.
