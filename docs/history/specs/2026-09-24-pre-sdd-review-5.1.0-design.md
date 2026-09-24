# pre-sdd-review 5.1.0: 이어 검토와 판정 무결성

- 날짜: 2026-09-24
- 대상: `skills/pre-sdd-review/` (현재 5.0.0, record schema 4)
- 범위: 사용자가 승인한 개선안 1~6. 중요성 하한(oracle 거르기)은 이번 범위가 아닙니다.

## 1. 목적

검토 → 수리 → 재검토 루프가 작은 차이 때문에 처음부터 다시 도는 비효율을 없앱니다.
동시에 판정 기록이 실제 검토와 어긋나는 결함을 막습니다. 새 기계 장치나 새 record
필드는 만들지 않고, 규칙 문장 수정·삭제와 기록기 이상 신호 두 개만 더합니다.

### 성공 기준

- 직전 판이 `REVISE`/`BLOCKED`이고 바뀐 것이 세 문서뿐이면, 다음 호출은 전체 발견 없이
  닫힘 검토 한 번으로 시작합니다.
- 두 번째 닫힘 뒤 원래 기록의 작은 잔여만 남으면 같은 호출 안에서 끝냅니다.
- 닫힘 검토 없이 `repaired`나 `READY`가 기록되지 않습니다. 기록되면 이상 신호가 드러납니다.
- 판마다 새 제품 결정이 나오는 계획은 세 판에서 설계로 돌려보냅니다.
- 선택 위험 검토자를 부르지 않은 닫힘 판이 사실과 다른 `degraded` 라벨 때문에 막히지 않습니다.

## 2. 근거 (로컬 기록 116건, 2026-09-15 ~ 09-24)

비공개 문서 원문은 싣지 않고 수치만 적습니다.

- 같은 계획이 14~15회 호출됐고, 연속 판끼리 결함 유형이 거의 겹치지 않았습니다. 판마다
  새 검토자가 전체 발견을 다시 하기 때문입니다 (`SKILL.md` 145-149, protocol 33).
- 완료 98건 중 `REVISE` 53건. 남은 지적 1건 이하 19건, 2건 이하 33건.
- `repair_passes >= review_passes`(마지막 동작이 수리) 31건, 그중 `READY` 6건.
- fix 칸에 "닫힘 미검증"이 적힌 `repaired` 43건. 호출을 쪼개 "6차 수정"까지 간 계획 1건.
- 열린 `BLOCKER`가 있는데 `REVISE`로 끝난 run 4건.
- 한 계획은 사용자가 매 판 결정 하나에 답했지만 다음 닫힘이 새 제품 결정을 찾아 지적이
  19 → 32로 늘었습니다.
- 규칙에 없는 "닫힘만 하는 호출"을 컨트롤러가 즉석에서 만들었고 판당 7~20분이었습니다.
  이때 위험 검토자를 부르지 않고 `focused-role-not-obtained`로 적었습니다.
- `repair_pass: 0` 무비용 수리 회계는 116건 중 0건 사용됐습니다.

## 3. 설계

### 3.1 이어 검토 (continuation)

새 호출의 첫 동작을 다음 조건으로 고릅니다.

1. 문서 해시·HEAD·요청이 모두 같으면: 기존 인계 재사용 규칙 그대로 (검토 없음).
2. 아래를 모두 만족하면 **이어 검토**:
   - 기록기에 이 계획의 직전 완료 run이 있고 판정이 `REVISE` 또는 `BLOCKED`입니다.
   - 그 run의 `execution`이 `full`이거나, `degraded`이고 사유가 `focused-role-not-obtained`뿐입니다.
   - `git diff --name-only <head_end> HEAD`가 해결된 설계·계획·원장 경로의 부분집합입니다.
     (사용자가 고친 문서를 커밋해도 이어 검토가 됩니다. 검토 도중 HEAD 이동 규칙
     127-130은 그대로입니다.)
   - 직전 `sha_end` 이후의 문서 diff를 만들 수 있습니다 (같은 대화에 이전 바이트가 있거나,
     그 바이트가 Git에 있음).
   - 사용자가 전체 재검토를 요청하지 않았습니다.
3. 그 밖에는 지금처럼 `start` 뒤 새 전체 발견.

이어 검토는 발견 단계를 건너뛰고, 새 읽기 전용 검토자에게 닫힘 지시를 보냅니다.
지시에는 직전 run의 열린 기록과 직전 `sha_end` 이후 diff를 싣습니다. 열린 기록의 출처는
같은 대화의 인계 패킷 원문이 있으면 그것이고, 없으면 `show`가 주는 기록(ID, 심각도, class,
Location, evidence 경로, consequence, fix)입니다. Location과 evidence 경로가 정확하므로 닫힘
판정에 충분합니다. 이어 검토에 한해 이것이 "원문(verbatim)" 요구를 대신합니다.

그 뒤 흐름은 기본 모드의 닫힘 이후와 같습니다 (수리, 닫힘, 3.2의 잔여 패스, 판정). 발견 ID는
직전 run의 것을 그대로 씁니다.

횟수 제한은 두지 않습니다. diff 밖의 문장은 이미 전체 발견을 한 번 거쳤고, diff 안은 닫힘의
범위 회귀가 봅니다. 한 번의 전체 발견 뒤 닫힘으로 끝나는 현재 호출 내부 흐름과 같은 위험입니다.

기록기가 이어 검토의 전제입니다. 이 계획의 기록 run이 없으면 이어 검토를 할 수 없고 전체
발견으로 갑니다. 기록기는 여전히 선택이며 판정을 바꾸지 않습니다.

이어 검토는 위험 검토자를 부르지 않습니다. 이 계획에 위험 분류가 없으면 `execution=full`,
`reviewers: 1`입니다. 있으면 `trigger`를 그대로 기록하고 `execution=degraded`, 사유
`focused-role-not-obtained`입니다 (3.5).

### 3.2 작은 잔여 패스

두 번째 닫힘 뒤 남은 것이 모두 아래를 만족하면, 수리를 한 번 더 하고 그 ID만 닫힘 검토합니다.

- 원래 기록의 ID입니다 (새 결함 모양 아님).
- `IMPORTANT`이고 2건 이하입니다.
- fix가 기록돼 있고 두 문서 안의 한 자리로 특정됩니다.
- repair-impact map이 비어 있습니다.

여기서 새 결함 모양이 나오면 그때 `REVISE`입니다. 수리 패스 상한은 2에서 3으로 바뀝니다.
기록기 범위도 `repair_passes` 0..3, `review_passes` 1..4, `finding.repair_pass` 0..3으로 넓힙니다.
새 필드가 없고 기존 record가 모두 계속 유효하므로 schema는 4로 둡니다. 5.1.0이 쓴
`repair_passes: 3` record는 5.0.0 기록기가 읽지 못합니다. 기록기는 스킬과 함께 배포되므로
받아들입니다.

### 3.3 판정 무결성

- `repaired`는 닫힘 검토자가 그 ID를 닫았을 때만 씁니다. 수리만 하고 닫힘을 못 했으면 `unresolved`.
- `repair_passes`는 **적용한 수리 패스 수**로 다시 정의합니다 (지금은 `repaired`가 나온 패스만 셈).
  사전 패스의 원장·기계 점검 수리는 계속 `repair_pass: 0`이고 패스로 세지 않습니다.
  기록의 `repair_pass`는 "상태를 마지막으로 바꾼 패스"가 아니라 "마지막으로 그 기록을 수리한
  패스"입니다. 수리했지만 닫히지 않은 기록은 `unresolved`이면서 `repair_pass`가 그 패스입니다.
  이에 맞춰 기존 이상 신호 `repair_without_repaired_finding`은 "적용한 패스가 있는데
  `repair_pass >= 1`인 기록이 하나도 없음"으로 좁힙니다. 적용했지만 닫지 못한 `REVISE`는
  정상 상태이기 때문입니다.
- 마지막 동작이 수리이면 `READY`를 내지 않습니다. 닫힘을 한 번 더 하거나 `REVISE`입니다.
  이것은 컨트롤러 규칙입니다. 기록기는 관찰만 합니다.
- 열린 `BLOCKER`가 있으면 판정은 `BLOCKED`입니다. `partially-closed`로도 `REVISE`가 되지 않습니다.
- 기록기 이상 신호 두 개를 추가합니다. 판정을 거부하지 않습니다.
  - `repair_after_last_review`: `repair_passes > 0` 이고 `repair_passes >= review_passes`.
  - `open_blocker_without_blocked_verdict`: 판정이 `BLOCKED`가 아닌데 `BLOCKER`가
    `unresolved` 또는 `partially-closed`로 남음.

무비용 수리(`SKILL.md` 259-265, 영향 표가 비고 닫힘 검토자가 소비자 없음을 확인하면 패스를
먹지 않음)는 지웁니다. 사용 0건이고, 패스를 적용 수로 세면 설 자리가 없습니다. 함께
`summary.counts.costless_repairs`, 계약 키 `costless-repairs-uncounted`, 해당 case와 테스트를 지웁니다.

### 3.4 범위 얼리기

- 직전 run이 사용자 결정 때문에 `BLOCKED`이고 그 결정이 아직 권위 문서에 들어가지 않았으면,
  검토자를 부르지 않고 같은 체크포인트를 다시 보여 주고 멈춥니다.
- 결정이 들어가면 3.1의 이어 검토로 그 diff만 봅니다.
- 같은 계획의 연속 세 run이 각각 새 제품 결정으로 `BLOCKED`이면, 더 돌리지 않고 `BLOCKED`로
  끝내며 인계에 "설계 미완: 설계 단계로 돌아가 남은 결정을 한 번에 정하라"를 적습니다. 연속 횟수는
  `summary`의 이 계획 chain에서 셉니다. chain이 없으면 멈추지 않고 알고 있는 횟수만 보고합니다.

### 3.5 위험 검토자와 degraded

- 위험 검토자는 **전체 발견을 하는 호출에서만** 요구합니다. 닫힘과 이어 검토에서는 부르지 않습니다.
- 기록 스키마는 바꾸지 않습니다. 부르지 않은 경우도 `degraded` + `focused-role-not-obtained`로
  기록하고, 그 사유의 뜻을 "위험 역할을 부르지 않았거나 얻지 못함"으로 넓힙니다.
- 사유가 `focused-role-not-obtained` **뿐인** `degraded` run은 인계 재사용과 이어 검토를 막지
  않습니다. 1차 역할 부재·에이전트 재사용 같은 다른 사유의 `degraded`는 지금처럼 재사용 금지.
- 기록기의 `full_reviewer_count_mismatch`는 그대로 둡니다 (`full`이면 trigger가 있을 때 2명).

대안으로 schema 5에 `stage`(discovery/continuation) 필드를 넣어 `full`로 기록하는 방법이 있지만,
legacy 경로를 포함해 기록기의 여러 면을 고쳐야 하고 6.0.0이 됩니다. 이번에는 택하지 않습니다.

### 3.6 규칙 정리

- `SKILL.md` 242-243은 210-211과 같은 문장입니다. 테스트가 고정한 `workflow` 절의 문장을
  남기고 다른 쪽을 지웁니다.
- 기준선 재구성 진술(121-125, protocol 22-25): 검토자에게 진술을 요구하는 한 줄만 남기고,
  스스로 검증되지 않는다고 설명하는 문장은 지웁니다.
- schema 2/3 pending 문단(169-172)은 `historical-unbound`를 남긴 한 문장으로 줄입니다.
- 역할·재사용 문단(203-217)을 3.5 내용과 합쳐 한 문단으로 줄입니다.
- 무비용 수리 회계 삭제는 3.3에 적었습니다.

## 4. 함께 고칠 면

각 규칙은 여러 파일에 있습니다. 구현 전에 모두 세고 한 커밋에서 맞춥니다.

- 규칙: `SKILL.md`, `references/reviewer-protocol.md`, `docs/maintainers/products/pre-sdd-review/contract.md`
  (흐름·판정·재사용 문단과 `### Contract` 키), `README.md`, `README.en.md`, 빨간 깃발 목록.
- 기록기: `evidence/evidence.py` (범위, 이상 신호 함수, `summary`의 이상 dict, costless 카운터),
  `evidence/README.md`, `CLI_VERSION`.
- 테스트: `tests/products/pre-sdd-review/cases.json`, `test_contract.py`(고정 문구,
  `INSTRUCTION_DOCUMENT_SHA256`, 계약 키), `evidence/test_evidence.py`, `test_hardening.py`,
  `testing.md`의 case 목록.
- 릴리스: `release.toml`, `SKILL.md` frontmatter, `CHANGELOG.md` 5.1.0.

## 5. 검증

- 새 case: 이어 검토 선택(세 문서만 바뀜 / 코드도 바뀜 / 기록 없음), 작은 잔여 패스,
  열린 `BLOCKER`는 `BLOCKED`, 연속 세 번 새 결정 → 설계 반송, 위험 역할 없는 닫힘 판의 인계 재사용.
- 기록기 테스트: 두 이상 신호의 참/거짓, 넓힌 범위의 경계값(3, 4 허용, 4, 5 거부), 기존 record 읽기.
- `python3 scripts/verify.py --skill pre-sdd-review`, 머지 전 `python3 scripts/verify.py`.
- 라이브 모델 호출은 하지 않습니다. 오프라인 통과는 실제 루프 효율의 증거가 아닙니다. 효과는
  다음 실사용 기록에서 호출 수와 `REVISE` 잔여 분포로 봅니다.

## 6. 하지 않는 것

- 중요성 하한(oracle 거르기)과 코드 블록 수리 제한.
- 새 record 필드, schema 5, closure 전용 입력 schema, 캐시.
- 복합 조건 증명 표 삭제 (근거 부족).
- `outcome` 기록 방식 변경.
