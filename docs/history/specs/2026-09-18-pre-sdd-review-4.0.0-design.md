# pre-sdd-review 4.0.0 교차 계획 게이트 설계 스펙

상태: 구현 전 설계. 이 문서는 현재 제품 계약을 변경하지 않는다.

기준: pre-sdd-review `3.0.4`, 저장소 `6c46d63`, 2026-09-18.
근거: 현장 기록 [`2026-09-18-pre-sdd-review-campaign-field-report.md`](../2026-09-18-pre-sdd-review-campaign-field-report.md)
와 `~/.pre-sdd-review/runs/` 의 기록 54건. 요약은 [12절](#12-근거-요약)에 있다.

## 1. 목표와 선택

`3.0.4` 는 계획 하나를 게이트에 넣는 계약이다. 캠페인 44회에서 왕복을 지배한
결함은 계획 **사이**에 있었고, 그 결함은 계획별 게이트 안에서 미대응 발견으로
한 번에 하나씩 `REVISE` 로 밀려났다. 계획 C 마지막 여섯 바퀴의 미해결 건은
기록상 **전부** 이웃 계획발이다. 지시를 더해서는 구조적으로 못 고친다.

**판정을 내지 않는 선행 패스를 앞에 두어 교차면을 한 번에 처리하고, 계획별
게이트는 구조를 그대로 둔 채 원장과 baseline 을 입력으로 받게 한다.**

| 대안 | 판단 |
| --- | --- |
| 산문 지시로만 원장·기계 점검을 요구 | §2.3 의 핵심이 "세면 나오는데 세라는 지시가 없다" 인데, 세라는 산문은 세는 것보다 약하다. 모델 편차를 그대로 탄다. 제외한다. |
| 결정적 `ledger.py` 를 제품에 추가 | 계획의 `Files:` 형식은 writing-plans 의 관례이지 이 제품의 계약이 아니다. 남의 형식에 파서를 묶으면 다른 저장소에서 조용히 빗나간다. `evidence.py` 의 `optional, non-blocking` 과 성격이 다른 두 번째 실행 표면이 생긴다. 제외한다. |
| 계약이 원장의 *모양* 만 소유하고 생성은 컨트롤러가 함 | 파서 결합이 없고 A 보다 단단하다. 그러나 교차 결함이 여전히 계획별 게이트 안에서 발견된다. 부분 채택한다(R2 의 모양 계약). |
| 판정 없는 선행 원장 패스 + 계획별 게이트 | `one-plan-per-invocation` 과 `no-aggregate-ready` 를 깨지 않고 교차면을 게이트 앞으로 옮긴다. 채택한다. |

## 2. Global Constraints

- 수정 대상은 `skills/pre-sdd-review/`, `tests/products/pre-sdd-review/`,
  `docs/maintainers/products/pre-sdd-review/`,
  `tests/repository/test_release_contract.py` 이다.
- 제품 버전은 `4.0.0`, 날짜는 `2026-09-18` 이다. record schema 와 `--version`
  handshake 가 `4` 로 바뀌므로 major 다.
- Python 3.11 이상, 표준 라이브러리만 쓴다. 새 런타임 의존성은 없다.
- 새 실행 파일을 추가하지 않는다. 기록기는 `evidence/evidence.py` 하나뿐이다.
- 호스트 지원을 넓히지 않는다. `products.toml` 과 `compatibility.md` 는 수정하지
  않는다. 지원 OS 는 macOS 만이다.
- 권위 순서는 다섯 항목을 유지한다. 원장은 유도된 증거이며 권위가 아니다.
- 판정 어휘(`READY`/`REVISE`/`BLOCKED`), 리뷰 역할 상한(둘), 수정 패스
  상한(둘)은 바꾸지 않는다.
- 사용자 문서 원문, 모델 응답 원문, 자격 증명은 픽스처·테스트·기록에 넣지 않는다.
- 태그와 GitHub Release 는 만들지 않는다.

## 3. 선행 원장 패스 — R1

`$pre-sdd-review ledger <plan...>` 로 명시 호출하거나, 외부 요청이 계획을 둘
이상 이름 대면 계획별 게이트 앞에 한 번 돈다.

`Resolve authoritative inputs` 가 바뀐다. 현재는 여러 계획을 이름 댄 요청을
"별도 호출로 나눠도 된다" 고만 적는다. 변경 뒤에는 나눈 호출 **앞에 선행 원장
패스를 먼저 도는 것이 필수**다. 판정은 지금 그대로 계획 단위이고, 넓어지는 것은
증거 범위뿐이다.

이 패스는 다음을 순서대로 한다.

1. 실행 순서를 확정한다. 사용자가 주거나 계획의 선행 조건에서 유도한다.
   확정할 수 없으면 멈추고 묻는다. 순서 없이는 baseline 이 정의되지 않는다.
2. 각 계획의 `Files:` 절 백틱 경로를 긁어 역인덱스로 뒤집어 원장을 쓴다.
3. 둘 이상이 만지는 경로만 모아 파일 중심 스윕을 돈다.
4. 기계 점검(R4)을 계획 전부에 한 번에 돌린다.
5. 3·4 의 출력은 **후보**다. 저장소에서 확인된 것만 남긴다.

2 부터 5 까지는 **컨트롤러가** 한다. 리뷰어를 파견하지 않는다. 파견하면 계획별
호출 밖에 세 번째 검토 역할이 생겨 역할 상한 둘을 깬다. 반입 수리를 검증하는 것은
그다음 계획별 게이트의 새 발견 리뷰어다. 현장 기록 §6 의 4단계(수리를 검증하는
별도 한 바퀴)는 이것으로 대체한다.

계획에 `Files:` 절이 없으면 **멈추고 묻는다.** Task 의 edit surface 에서 유도하지
않는다. 유도한 원장은 원본 형식과 조용히 어긋날 수 있고, 그 어긋남이 바로 이
패스가 막으려는 것이다.

이 패스는 `READY`/`REVISE`/`BLOCKED` 를 내지 않는다. 출력은 원장 경로와 해시,
확정된 실행 순서, 저장소로 확인된 결함 후보 목록이다.

`plan-cardinality` 계약 문구를 조인다. `one-plan-per-invocation` 은
**판정을 내는 호출** 하나에 계획 하나라는 뜻이다. `SKILL.md` 의
"One invocation reviews exactly one implementation plan" 도 판정을 내는 호출로
한정해 고친다. 선행 패스가 판정을 안 낸다는 사실에 기대지 말고 문구를 바꾼다.
`no-aggregate-ready` 는 그대로다.

`review-only` 에서는 원장을 파일로 쓰지 않고 컨트롤러 로컬로 둔다. 반입 수리도
하지 않는다. 확인된 후보는 발견으로만 보고한다. `review-only` 의 무수정 계약이
우선한다.

확인된 후보는 **컨트롤러에게** 간다. 리뷰어에게 가지 않는다. 컨트롤러가 리뷰어
파견 **전에** 고치므로(반입 수리) 리뷰어는 여전히 아무것도 듣지 않은 채 온다.
반입 수리는 리뷰 이전이므로 `repair_passes` 를 먹지 않고, 기록에는
`repair_pass: 0` 으로 남는다.

이 패스는 기록기에 run 으로 남기지 않는다. record 의 `plan` 은 단수이고 이
패스는 판정이 없어 `verdict` 계약에 맞지 않는다. `MODES` 는 `default` 와
`review-only` 둘을 유지한다. 원장은 각 계획별 run 의 `ledger` 필드로만 남는다.

## 4. 원장의 모양과 수정 허용 목록 — R2

`contract.md` 가 원장의 필수 모양을 소유한다.

머리에 생성 시각, 대상 계획 목록과 각 계획의 SHA-256, 확정된 실행 순서를 적는다.
본문은 한 행이 한 경로다.

```text
| path | 이 경로를 만지는 계획 (실행 순서대로) |
```

만지는 계획이 하나인 경로도 **전부** 적는다. 스윕 대상은 둘 이상인 행이다.
계획 해시가 머리에 있으므로 어느 계획이든 내용이 바뀌면 원장이 무효가 된다.

기본 위치는 `docs/superpowers/ledgers/YYYY-MM-DD-<campaign>.md` 이고 사용자
선호가 우선한다.

수정 허용 목록이 셋이 된다.

### Editable paths

1. resolved design specification.
2. resolved implementation plan.
3. resolved shared-file ledger.

원장은 유도된 것이지 권위가 아니다. 권위 순서 다섯은 그대로다. 원장이 계획의
`Files:` 와 어긋나면 계획이 이기고 원장을 다시 만든다. 리뷰어는 원장을 권위로
인용하지 않는다.

## 5. baseline 과 권위 순서 5번 — R3

충돌 우선순위 5번을 고친다.

- 현재: `Current repository reality`
- 변경: `Repository reality at this plan's turn`

`current` 가 `HEAD` 를 뜻하는지 이 계획의 차례를 뜻하는지 고르지 않아 기본값이
늘 `HEAD` 로 떨어졌다. 순서가 정해진 캠페인에서 계획 N 의 기준선은
"디스크 + 계획 1..N-1 적용" 이다.

`Capture freshness` 에 `baseline` 항목을 더한다. 선행 계획이 없으면 `HEAD`,
있으면 `HEAD` 와 선행 계획 목록이다. 선행 계획이 있으면 리뷰어 지시에 그 목록과
경로를 싣고, **응답 첫 줄에 기준선을 재구성했다는 진술**을 요구한다.

그 진술은 읽기 전용 리뷰어의 **자기 보고**이며 기계로 검증되지 않는다. 값은
기준선을 명시적으로 만들어 리뷰어가 `HEAD` 로 조용히 떨어지지 않게 하는 데 있지,
재구성이 실제로 일어났음을 증명하는 데 있지 않다.

## 6. 기계 점검 — R4

`Repair rules` 에 기계 점검 절을 더한다. 종결 리뷰어를 부르기 전에 돌리고 결과를
`repair-impact map` 에 붙인다. 현장에서 걸린 다섯을 언어 중립적인 다섯 갈래로
일반화한다.

1. **선언된 수 대 세어 나온 수** — 문서가 적은 정수와 실제 개수. Task 가 적은
   통과 건수 대 테스트 수, 닫힌 목록의 구성원 수.
2. **같은 구성자의 인자 개수와 순서가 자리마다 같은가.**
3. **리터럴이 그것을 받는 제약을 넘는가** — 길이, 범위, 열거.
4. **번호나 이름에 박힌 식별자가 자리마다 일치하는가** — 마이그레이션 파일
   번호와 그것을 확인하는 테스트 이름의 번호.
5. **닫힌 목록의 모든 면이 같이 갱신됐는가** — 스키마 enum, 정확 일치 키 배열,
   건수를 세는 테스트.

순서를 계약으로 박는다. **기계 점검 출력은 후보이고, 저장소에서 확인되기 전에는
결함이 아니다.** 확인 없이 결함으로 올리면 게이트가 거짓 결함으로 왕복을 만든다.

`Red flags` 에 두 줄을 더한다.

- `Claim that a test covers something without locating that test`
- `Apply a textual repair without asserting the match is unique`

## 7. 부분 닫힘, 같은 갈래, 값 없는 수리 — R5

셋은 한 원리의 세 면이다. **한 결함 = 한 기록, 자리는 여럿.**

**부분 닫힘.** 종결 판정에 `closed` / `partially-closed` / `open` 셋을 둔다.
부분 닫힘의 잔여는 새 ID 가 아니라 **같은 기록의 남은 자리**로 적는다. 수리
패스가 결함 수를 따라가지, 결함이 흩어진 자리 수를 따라가지 않는다. 마지막까지
부분 닫힘이면 판정에는 미해결로 작용해 `REVISE` 를 강제하고, 기록에는
`partially-closed` 로 남는다.

**같은 갈래 예외.** `Default mode` 의 unmapped 문단에 예외를 넣는다. 원 기록과
`class` 가 같고 갈래가 같은 발견은 **위치가 달라도** unmapped 가 아니다. 원
기록의 Location 이 불완전했던 것이며, 컨트롤러는 원 기록의 Location 을 넓히고
**같은 패스 안에서** 수리한다. 새 결함 갈래일 때만 unmapped 다.

**값 없는 수리.** 아래 두 조건을 **동시에** 만족하는 수리는 패스를 먹지 않는다.
컨트롤러 판단이 아니라 관찰 가능한 조건이다.

1. `repair-impact map` 이 비어 있다. 구조 트리거가 하나도 걸리지 않았다.
2. **종결 리뷰어가** 소비자 없음을 확인했다. 컨트롤러 자기 확인은 인정하지 않는다.

둘 다 맞는 수리는 한 패스로 묶어 처리한다. 조건 2 가 종결 리뷰어의 확인이므로
패스 계산은 그 회차의 종결 검토가 끝난 뒤에 확정된다. 수리 시점에 미리
"값 없음" 으로 셈하지 않는다.

기록에서의 구별은 R9 가 정한다. `repair_pass: 0` 은 "패스를 먹지 않고
고쳐졌다" 이고, `finding.source` 가 그 이유를 말한다. 한 기록이 여러 패스에
걸치면 `repair_pass` 는 **그 기록의 status 를 마지막으로 바꾼 패스**를 적는다.
1 패스에서 `partially-closed`, 2 패스에서 닫힌 기록은 `repair_pass: 2`,
`status: repaired` 다.

## 8. 리뷰어 지시 계약 — R6

`reviewer-protocol.md` 에 지시 필수 항목을 넣는다. **발견 지시와 종결 지시를
나눈다.** 나누지 않으면 독립성 규칙과 충돌한다.

### Discovery dispatch contract

- baseline 진술 요구. 선행 계획 목록과 경로, 응답 첫 줄.
- 원장 경로와 해시.
- 큰 문서는 Task 단위로 끊어 읽으라는 지시.
- 되풀이된 결함 갈래 넷의 이름(R7).
- 출력 형식.

앞선 회차의 기록은 **싣지 않는다.** 발견 리뷰어는 아무것도 듣지 않은 채 와야 한다.

### Closure dispatch contract

발견 지시의 항목 전부에 더해,

- 앞선 회차의 PSDR 기록 **원문**. 컨트롤러 요약은 금지한다. 닫힘 확인은 원
  기록의 Location 과 Evidence 를 대조하는 일이라 요약으로는 못 한다.
- `repair-impact map`.
- 기계 점검 결과.
- **아직 아무 기록도 가리키지 않은 Task 를 명시적으로 나열하는 칸.**

기존 red flag `Resume a reviewer by naming findings, paths, symbols, or fixes`
는 **불완전한 기록을 다시 묻는 경우에만** 적용된다고 명시한다.

## 9. 결함 갈래 넷과 증명 표 — R7

Pass 3 에 이름 붙은 검사 넷을 넣는다.

- **부록이 Task 본문에 절반만 접힘.** 수정 사항 절이 요구를 적는데 Task 코드
  블록은 옛 모양 그대로다.
- **산문만 있고 코드가 없는 검증.** "저 테스트가 덮는다" 고 적었는데 그 테스트가
  없거나 그것을 보지 않는다.
- **줄 번호를 위치로 씀.** 선행 계획이 같은 파일 위쪽에 삽입하면 번호가 밀린다.
  심벌 이름이 있으면 번호는 오정보만 준다.
- **닫힌 목록을 한쪽만 갱신.** 여러 계획이 같은 목록에 자기 것만 더한다.

Pass 4 에 증명 표를 더한다. 계획이 여러 조각이 결합된 제약을 단정하면, 조각을
하나씩 뺀 변형을 만들어 거절 사례마다 대 보고 **표로** 적기를 요구한다. 산문
판정보다 단단하고, 여섯 조각 중 셋만 잡던 것을 즉시 드러냈다.

## 10. degraded 규칙 — R8

- 인계 재사용은 `full` 만이다. `degraded` 는 `blocked` 와 같이 재사용하지 않는다.
- 한 리뷰어를 **계획이 다른 호출에** 돌려 쓰는 것을 금지한다. 재사용이 아니라
  독립성 상실이다.
- **1차 역할**에 새 독립 리뷰어를 구할 수 없으면 짧은 degraded 회차를 도는 대신
  `BLOCKED` 로 멈춘다.
- **집중 위험 역할**만 구하지 못하면 `degraded` 를 유지한다. 그 인계는 재사용
  대상이 아니다.
- `Verdict and handoff` 의 `BLOCKED` 정의를 함께 넓힌다. 현재 정의는 "필요한
  권위·입력·저장소 증거가 없음" 인데 호스트 스레드 한도는 그 셋 중 어느 것도
  아니다. **"독립 1차 리뷰어를 구할 수 없음"** 을 `BLOCKED` 사유로 명시한다.
  그 run 은 `execution=blocked` 이고 `block_reason` 에 사유를 적는다.
  `block_reason` 은 100자 이하 자유 문자열이며 `BLOCKED` 에서 null 이면
  `blocked_without_reason` 이상이 난다.
- `degraded_reasons` 를 열거로 조인다: `primary-role-not-obtained`,
  `focused-role-not-obtained`, `agent-reused-within-invocation`,
  `agent-reused-across-plans`, `other`.

## 11. 기록기 schema 4 — R9, R10

record 키가 정확 일치 검증이므로 필드 추가는 handshake 를 깬다.

| 대상 | 변경 |
| --- | --- |
| `SCHEMA` / `CLI_VERSION` | `4` / `4.0.0`. handshake 는 `{"cli_version":"4.0.0","schema":4,"skill_name":"pre-sdd-review"}`. `SKILL.md` 의 하드 게이트도 `schema=4` 로 고친다 |
| record | `baseline` 추가 (`head`, `prior_plans`), `ledger` 추가 (`path`, `sha`) 또는 null |
| `git` | `head_start_is_ancestor_of_head_end` 추가. `finish` 때 `git merge-base --is-ancestor` 로 판별한다 |
| `FINDING_KEYS` | `source` 추가. 값은 `reviewer`, `ledger-pass`, `machine-check` |
| `finding.repair_pass` | 1..2 → **0..2** |
| `FINDING_STATUSES` | `partially-closed` 추가 |
| `degraded_reasons` | 자유 문자열 → R8 의 열거 |
| anomalies | `head_start_not_ancestor_of_head_end`, `document_changed_without_repair_pass` 추가 |
| `summary` counts | `costless_repairs` 추가 |
| `start` 인자 | `--ledger <path>` 와 반복 가능한 `--prior-plan <path>` 를 더한다. 둘 다 선택이며, 없으면 `ledger` 는 null 이고 `baseline.prior_plans` 는 빈 목록이다. `evidence/README.md` 의 명령 표 `start` 행을 함께 고친다 |
| 하위 호환 | schema 2·3·4 를 **읽는다**. 변경은 4 만이다. 예외로 schema 3 pending 은 `abandon` 만 허용해 업그레이드 시점의 진행 중 run 을 닫을 수 있게 한다 |

`head_changed_during_review` 는 **유지한다.** 현장 기록 §2.7 셋째 항목은 기록이
반박한다. 관찰된 11건 전부 `head_start != head_end` 이므로 참 양성이고, 좁히면
진짜 신호를 죽인다. 대신 분해한다. `HEAD` 가 앞으로 나아간 것은 리뷰 중 커밋이며
이미 red flag `Commit before finish` 가 덮는다. **되감긴 것**은 baseline 이 통째로
바뀐 것이라 판정 근거가 무효일 수 있으므로 따로 낸다. 이름은 재는 것을 그대로
부르는 `head_start_not_ancestor_of_head_end` 로 한다. 되감기만이 아니라 리뷰 중
rebase 도 같은 모양이므로 `head_moved_backward` 는 나중에 이름을 다시 바꾸게 된다.

`document_changed_without_repair_pass` 는 문서 SHA 가 바뀌었는데 수리 패스가 0
이고 `repair_pass: 0` 수리도 하나도 없을 때만 낸다. 반입 수리와 값 없는 수리를
오탐하지 않기 위해서다.

마찰 정리 둘을 함께 넣는다.

- `SKILL.md` 의 `Optional local evidence` 에 finding 레코드의 모양을 한 줄로
  적는다. 특히 `evidence` 가 산문이 아니라 **저장소 상대 경로의 목록**이라는 것.
- `summary` 직후 `pending` 이 있으면 그것부터 닫으라는 문장을 지금보다 앞에 두고,
  `chains` 출력에서 `pending` 을 눈에 띄게 한다.

## 12. 근거 요약

`~/.pre-sdd-review/runs/` 기록 54건(완료 52, abandoned 1, pending 1) 중 캠페인은
`won-sec-ai` 44회다.

- 계획 C 마지막 여섯 바퀴의 미해결 발견이 전부 이웃 계획발이다:
  `stale-line-citation-under-prerequisite-plan` 4,
  `citation-drifts-by-a-prerequisite-plan` 2,
  `sibling-seed-overwritten-in-shared-file`,
  `required-field-breaks-sibling-fixtures`,
  `shared-fixture-mutation-breaks-sibling-cases`,
  `component-replaced-by-prerequisite-plan`. R1·R3 의 근거다.
- `stale-line-citation-under-prerequisite-plan` 이 전체 패턴 1위(6회). R7 의 근거다.
- 09-17 17:13 회차가 직전 회차의 패턴 다섯을 다시 냈다. R5 의 근거다. 패턴
  문자열은 컨트롤러가 붙인 이름이므로 대리 지표이고 측정값이 아니다.
- 09-17 08:11–08:42 여섯 회차가 전부 `fresh-agents-unavailable-thread-limit;
  reused-reviewers` 이고 회차당 약 5분이다. 완료 중앙값은 1234초다. 여섯 모두
  몇 시간 뒤 `full` 로 다시 돌았다. 그 사이 문서를 고쳤으므로 판정이 틀렸다는
  증거는 아니다. 증거가 되는 것은 독립성 상실과 재작업 비용이다. R8 의 근거다.
- `head_changed_during_review` 11건 전부 `head_start != head_end` 다. 17:13 은
  `eeadfd22 -> 4c0ec269` 으로 되감겼다. R10 의 근거다.
- 09-17 22:19 은 계획 SHA 가 바뀌었는데 `repair_passes=0` 이다. R10 의 근거다.

## 13. 검증

- `python3 scripts/verify.py --skill pre-sdd-review` 를 먼저 돌린다. 머지 전에는
  `python3 scripts/verify.py` 다.
- `cases.json` 에 다섯 케이스를 더한다: 원장 필수 입력, baseline 재구성, 부분
  닫힘, 값 없는 수리, degraded 인계 재사용 금지.
- `tests/products/pre-sdd-review/evidence/` 에 schema 4 테스트를 더한다.
  handshake, 새 필드 검증, `repair_pass` 0 허용, `partially-closed`,
  `degraded_reasons` 열거, 새 이상 둘, schema 3 pending 의 `abandon` 전용 허용.
- 픽스처는 기존 일곱을 유지하고 교차 계획 픽스처를 더하지 않는다. 선행 패스는
  판정이 없어 픽스처의 `expected.json` 계약에 맞지 않는다.
- 오프라인 통과를 실제 모델 품질이나 다른 환경의 실행 증거로 확대하지 않는다.

## 14. 함께 고칠 파일

`contract.md` 의 `함께 고칠 파일` 을 따른다.

- 권위 순서·판정·repair 한도·reviewer role: `skills/pre-sdd-review/SKILL.md`,
  `references/reviewer-protocol.md`,
  `docs/maintainers/products/pre-sdd-review/contract.md`,
  `tests/products/pre-sdd-review/cases.json`, 제품 README 둘.
- `tests/products/pre-sdd-review/test_contract.py` 의 `TARGET_VERSION`,
  `INSTRUCTION_DOCUMENT_SHA256`(`SKILL.md` 와 `references/reviewer-protocol.md`
  의 고정 해시), `CASE_IDS` 를 함께 고친다. 지시 문서를 고치면 해시 고정이
  반드시 깨지므로 같은 커밋에 넣는다.
- `tests/repository/test_release_contract.py` 의 `pre-sdd-review` 버전을
  `4.0.0` 으로 올린다. 태그와 아티팩트 이름도 함께 바뀐다.
- 기록기 명령·schema 4: `skills/pre-sdd-review/evidence/evidence.py`,
  `evidence/README.md`, `tests/products/pre-sdd-review/evidence/`.
- 호스트 지원: 넓히지 않는다. `products.toml` 과 `compatibility.md` 는 수정하지
  않는다.
- `release.toml` 과 `CHANGELOG.md` 를 `4.0.0` 으로 올린다.

`contract.md` 의 `하지 않는 것` 에서 `program ledger` 를 뺀다.
`shared-design invalidation map`, `closure-only input schema`,
`evidence probe cache` 는 범위 밖이므로 유지한다.

`Contract` 목록에 항목을 더한다.

- `ledger`: `pre-pass-no-verdict`, `derived-not-authority`
- `baseline`: `plan-turn-reality`
- `repair-passes`: `at-most-two`, `costless-repairs-uncounted`
- `second-reviewer`: `conditional-only`, `no-cross-plan-reuse`
- `handoff`: `unresolved-packet`, `full-execution-only`

## 15. 이 문서를 접을 때

구현이 끝나면 이 문서와 현장 기록을 함께 지운다. Git 이력에서 볼 수 있다.
