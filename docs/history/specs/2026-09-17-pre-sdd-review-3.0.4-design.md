# pre-sdd-review 3.0.4 재검토 진입·이상 보고 정리 설계 스펙

상태: 구현 전 설계. 이 문서는 현재 제품 계약을 변경하지 않는다.

기준: pre-sdd-review `3.0.3`, 저장소 `6484dff`, 2026-09-17.
근거: `6484dff` 검증 보고 두 건(Codex 라이브 평가, Claude Code 라이브 평가)과
코드 재현 스크립트. 요약은 [7절](#7-근거-요약)에 있다.
실행 문서: [구현 계획](../plans/2026-09-17-pre-sdd-review-3.0.4.md).

## 1. 목표와 선택

`3.0.3`은 관찰 이상을 `READY` 보고에 적고 불완전 기록을 유도 없이 재질의하게
했다. 그러나 라이브 검증에서 지침 두 곳이 서로 충돌하고, 기록기 조회가
윈도우 때문에 방금 끝낸 run을 놓칠 수 있음이 재현됐다. **지침 충돌을 기록기가
계산하는 값으로 대체하고, 문구는 그 값을 그대로 출력하게 한다.** 새 명령이나
새 schema는 만들지 않는다.

| 대안 | 판단 |
| --- | --- |
| 문구만 손질 (`--last 20` → `--last 200`) | 윈도우 크기만 바뀌고 누락 조건은 남는다. 재사용 충돌도 해결하지 않는다. 제외한다. |
| `summary --run-id` 새 옵션 | 명령 하나가 늘고 컨트롤러가 두 번 조회한다. `finish`가 이미 record를 검증하므로 중복이다. 제외한다. |
| `finish`가 이 run의 anomalies를 반환 + 재사용 규칙을 `execution`으로 분기 | 조회 한 번이 줄고, 재사용 판단이 기록된 값 하나로 기계화된다. 채택한다. |

## 2. Global Constraints

- 수정 대상은 `skills/pre-sdd-review/`, `tests/products/pre-sdd-review/`,
  `docs/maintainers/products/pre-sdd-review/`, `tests/repository/test_release_contract.py`이다.
- record 형식과 `schema=3`은 바꾸지 않는다. `--version` 정규 줄
  `{"cli_version":"3.0.0","schema":3,"skill_name":"pre-sdd-review"}`도 바꾸지 않는다.
  `finish` 출력에 키를 추가하는 것은 additive 변경이다.
- Python 3.11 이상, 표준 라이브러리만 쓴다. 새 런타임 의존성은 없다.
- 호스트 지원을 넓히지 않는다. `claude-code`는 `not_measured`로 남는다.
  이번 라이브 측정은 근거 문서이지 지원 증거가 아니다.
- 지원 OS는 macOS만이다.
- 판정 규칙(`READY`/`REVISE`/`BLOCKED`), 권위 순서, 수정 허용 목록,
  리뷰 역할 상한(둘), 수정 패스 상한(둘)은 바꾸지 않는다.
- 사용자 문서·모델 응답 원문·자격 증명은 픽스처, 테스트, 기록에 넣지 않는다.
- 제품 버전은 `3.0.4`, 날짜는 `2026-09-17`이다. 태그와 GitHub Release는 만들지 않는다.

## 3. 기록기: `finish`가 이 run의 관찰 이상을 반환 — R1

현재 `cmd_finish`는 `{"run_id","status","verdict"}`만 돌려준다. anomaly 계산은
`summarize`에만 있고, `repo_reality_citing_documents_only`는
`observation_anomalies()`에도 없다. 컨트롤러는 `summary --last 20`에서 이 run을
찾아야 하는데 `--last`는 시작 시각 순이라 먼저 시작해 나중에 끝난 run이 빠진다.

변경:

- `finding_anomalies(record) -> list[dict]`를 추가한다. completed record의
  finding 중 `class == "repo-reality"`이고 `evidence`가 검토한 plan·design 경로의
  부분집합이면 `{"name": "repo_reality_citing_documents_only", "finding_id": <id>}`를 낸다.
  completed가 아니면 빈 목록이다.
- `run_anomalies(record) -> list[str]`를 추가한다. `observation_anomalies(record)`
  이름 집합과 `finding_anomalies` 이름 집합의 합집합을 정렬해 돌려준다.
- `cmd_finish`는 record를 쓴 뒤 `{"run_id","status":"completed","verdict",
  "anomalies": run_anomalies(record)}`를 돌려준다. 키 순서는 기존 정규 JSON
  직렬화 규칙을 따른다.
- `summarize`의 repo-reality 인라인 검사는 `finding_anomalies`를 호출해
  대체한다. `summary` 출력 형태와 값은 바뀌지 않는다.
- `evidence/README.md`의 명령 표 `finish` 행과 "Reading the log" 절을 새 출력과
  재사용 규칙([4절](#4-컨트롤러-재사용-규칙-r2))에 맞춘다.

검증: 정상 run은 `anomalies: []`. `reviewers=2`(trigger 없음)와 문서만 인용한
repo-reality finding을 가진 run은 `["full_reviewer_count_mismatch",
"repo_reality_citing_documents_only"]`. 같은 home의 `summary`가 같은 run을 같은
이름으로 분류한다. `abandon`은 anomalies를 돌려주지 않는다.

## 4. 컨트롤러 재사용 규칙 — R2

현재 SKILL.md 79–82행은 문서 해시가 이전 `REVISE`/`BLOCKED` run의 `sha_end`와
같으면 새 리뷰를 시작하지 말라 하고, 245행 red flag가 이를 강화한다. 그러나
220–223행은 권위·저장소 근거·명시 요청이 바뀌면 새 호출을 허용한다. 라이브에서
Codex는 required base가 생겼는데도 과거 `BLOCKED`를 재사용했고, Claude Code는
충돌을 지적하며 우회했다. 재현된 사례에서 branch는 `HEAD`에 생성돼
`git.head_end`가 현재 `HEAD`와 같았다. 따라서 HEAD 비교로는 이 사례를 가를 수
없고, 기록의 `execution=blocked`, `reviewers=0`이 유일한 기계적 판별자다.

새 규칙(SKILL.md Optional local evidence 절):

1. `start` 전에 `summary --repo <repo display name>`을 실행한다. `--last`는 쓰지
   않는다. `runs`와 `chains`에서 이 plan 경로를 찾는다.
2. 이 plan의 `pending` run이 있으면 먼저 닫는다(기존 규칙 유지).
3. 이 plan의 마지막 완료 판정이 `REVISE` 또는 `BLOCKED`이면 그 run을 `show`한다.
4. 그 run의 `execution`이 `blocked`이면 인계를 **재사용하지 않는다**. 리뷰어를
   부르지 않은 run이므로 반복할 리뷰가 없다. Resolve authoritative inputs 절의
   게이트(`**Spec:**` 해석, required base 확인)를 다시 돌리고, 통과하면 `start`한다.
   통과하지 않으면 새 `BLOCKED`를 기록한다.
5. `execution`이 `full` 또는 `degraded`이면 다음이 **모두** 참일 때만 재사용한다:
   `plan.sha_end`·`design.sha_end`가 현재 문서와 같다; `git.head_end`가 현재
   `HEAD`와 같다; 외부 요청이 재검토를 요구하거나 바뀐 권위·저장소 근거를 말하지
   않는다. 하나라도 거짓이면 `start`한다.

Red flags 두 줄을 이에 맞춘다: "문서·`HEAD`·요청이 모두 같은 `full`/`degraded`
`REVISE`/`BLOCKED` run 뒤에 새 리뷰 시작"과 "`execution=blocked` run의 인계
재사용, 또는 문서 해시만으로 인계 재사용". contract.md의 기록기 계약 단락과
"REVISE나 BLOCKED 뒤" 단락, `evidence/README.md`의 "Reading the log"를 같은
말로 맞춘다.

## 5. 컨트롤러 보고와 재질의 문구 — R3

- Verdict and handoff 절의 "After `finish`, read `summary --last 20`" 문장을
  바꾼다. `finish`가 돌려준 `anomalies`를 `Anomalies: <names>`로 출력한다. 비어
  있으면 `Anomalies: none`. 기록기를 쓰지 않았거나 `finish`가 실패했으면
  `Anomalies: not_recorded`. 이 run을 윈도우 있는 `summary`에서 찾지 않는다.
  이상은 판정을 바꾸지 않는다(유지).
- Red flag "Print `READY` without this run's observation anomalies"를
  "Print `READY` without the `Anomalies:` line from `finish`"로 바꾼다.
- Select reviewers 절 "Reviewers never edit files." 뒤에 긍정 지침을 넣는다:
  리뷰어가 요약을 내거나 PSDR 필드가 빠진 기록을 내면 **그 리뷰어에게 한 번**,
  빠진 필드 이름만 들어 완전한 기록을 요청한다. 의심되는 finding·경로·심볼·
  수정을 요청에 넣지 않는다. 요약을 finding으로 받지 않는다. 지금 이 규칙은
  red flag 두 줄(부정형)과 contract.md에만 있다.
- contract.md 최종 보고 단락의 "`summary --last 20`에서 이 run의 관찰 이상
  이름을 그대로 적습니다"를 "`finish`가 돌려준 `anomalies`를 `Anomalies:` 줄로
  그대로 적습니다"로 바꾼다. README.md·README.en.md의 대응 문장도 같은 뜻으로
  맞춘다.

## 6. 심각도 정의와 픽스처 — R4

라이브 10 finding 중 5건이 fixture 기대 심각도와 달랐다. Claude는 `BLOCKER`로
올리고 Codex는 `missing-coverage`에서 `IMPORTANT`로 내렸다. 원인은
reviewer-protocol.md의 두 정의가 겹치기 때문이다: `BLOCKER`의 "acceptance
evidence is materially invalid or missing"과 `IMPORTANT`의 "an unverifiable
acceptance claim"이 같은 사실을 가리킬 수 있다.

새 정의(reviewer-protocol.md Finding vocabulary):

- `BLOCKER`: the minimal document fix needs authority, input, or repository
  evidence outside the two reviewed documents, or a new product decision.
  Left unresolved, it forces `BLOCKED`.
- `IMPORTANT`: the minimal document fix is an authority-preserving edit within
  the two reviewed documents. Left unresolved, it forces `REVISE`.

이 정의는 심각도를 판정 규칙과 정합시킨다. 픽스처 조정:

- `missing-coverage/expected.json`의 심각도를 `BLOCKER`에서 `IMPORTANT`로 바꾼다.
  설계는 "Empty input is rejected"를 이미 적었고, 거부 방식은 설계 세분도
  아래의 구현 세부다. plan에 "빈 문자열은 throw"와 `assert.throws` 테스트 한
  단계를 추가하면 두 문서 안에서 닫힌다. 라이브 두 호스트 모두 `IMPORTANT`를
  선택했다. 기대 판정 `REVISE`는 그대로다. 이 항목은 이번 설계에서 유일한
  판단 사항이며, 유지관리자가 거부하면 정의를 유지한 채 이 픽스처만 되돌린다.
- `ready/design.md`의 "The function returns the rendered string for the supplied
  input."을 "The function returns the supplied input unchanged."로 바꾼다.
  라이브에서 "rendered"가 미정의라는 이유로 정상 대조군이 `BLOCKED`
  (authority-drift)로 읽혔다. 정상 대조군은 해석 여지가 없어야 한다.
- 두 픽스처 원문은 `test_contract.py`의 `FIXTURE_CONTENTS`에 그대로 고정돼
  있으므로 같은 문자열을 함께 바꾼다. 두 픽스처는 `V1_1_FIXTURE_SHA256` 대상이
  아니다.

## 7. 근거 요약

| 항목 | Codex (이전 보고) | Claude Code (이번 보고) |
| --- | ---: | ---: |
| 의도한 결함 발견 | 5/5 | 5/5 |
| 결함 사례의 잘못된 READY | 0/6 | 0/6 |
| 정상 대조군 오탐 | 0/2 | 1/2 (`ready`) |
| 표적 finding 심각도 일치 | 4/5 | 1/5 |
| PSDR 필드 완전성 | 10/10 | 14/14 |
| 변경된 저장소 근거 재검토 프로브 | FAIL | PASS (충돌 지적 후 우회) |
| 최근 20건 밖 실행 보고 프로브 | PASS (범위 확장) | PASS (범위 확장) |

코드 재현: 문서 해시 동일·HEAD 변경 상태에서 해시 규칙이 재사용을 지시함;
먼저 시작해 나중에 끝난 run이 `--last 20`에서 빠짐; 새 cases.json 두 항목의
`request`를 비워도 contract 56건이 통과함(라벨 비교라는 설계상 사실).

## 8. 테스트와 문서

- evidence suite: `finish` 출력의 `anomalies`를 실제로 실행해 확인하는 테스트를
  추가하고, `finish` 출력을 exact-dict로 고정한 두 단언(`test_evidence.py`,
  `test_hardening.py`)을 새 키에 맞춘다.
- contract suite: 바뀐 문장을 단언한다. `summary --last 20` 존재 단언은 제거하고
  `summary --repo`, `Anomalies:`, `execution` 분기, 긍정 재질의 문장, 새 red flag
  두 줄, 새 심각도 정의를 단언한다. `INSTRUCTION_DOCUMENT_SHA256`,
  `MAINTAINER_CANONICAL_DIGEST`, 관련 subsection digest, `TESTING_CANONICAL_DIGEST`,
  `FIXTURE_CONTENTS`, `TARGET_VERSION`, changelog 날짜를 갱신한다.
- cases.json에 `blocked-execution-restarts` 사례를 추가한다
  (`expect: ["no_reuse_blocked_execution", "rerun_input_gates", "start"]`).
  testing.md의 사례 수를 서른한 개로, Case inventory에 항목을 추가한다.
- testing.md "선택적 라이브 검사"에 컨트롤러 경계 프로브 절차 네 가지를
  적는다: 변경된 저장소 근거 재검토, 불완전 기록 재질의, 이상 있는 READY 보고,
  윈도우 밖 run 보고. 합성 recorder 상태를 만들고 `PRE_SDD_REVIEW_HOME`을
  격리한 뒤 컨트롤러에게 SKILL.md만 준다. 결과는 결정 파일로 채점한다.
  이 절차는 선택이며 CI가 요구하지 않는다.
- compatibility.md는 바꾸지 않는다.

## 9. 하지 않는 것

- `summary`에 `--run-id` 옵션이나 새 명령을 추가하지 않는다.
- record schema, `cli_version`, `--version` 출력을 바꾸지 않는다.
- `cmd_start`에 같은 plan의 pending 중복 거부를 넣지 않는다. 컨트롤러 규칙으로
  남긴다.
- 리뷰어 프롬프트에 심각도 판정 예시를 늘리지 않는다. 정의 두 줄로 끝낸다.
- 호스트 지원표, 공개 사용자 문서(`docs/users/`)는 바꾸지 않는다.
- 라이브 프로브를 CI나 `verify.py`에 넣지 않는다.

## 10. 완료 기준

- `python3 scripts/verify.py --profile full`이 exit 0이다.
- `python3 scripts/release.py check --product pre-sdd-review`가 통과한다.
- 스크래치 저장소에서 `finish`가 anomalies를 돌려주고, 같은 home의 `summary`와
  분류가 일치한다.
- SKILL.md, contract.md, evidence/README.md, README.md, README.en.md에
  `summary --last 20`이 남아 있지 않다.
- 재현 스크립트의 "hash-only reuse" 사례를 SKILL.md 새 규칙에 대입하면
  `execution=blocked` 분기로 `start`에 이른다.
