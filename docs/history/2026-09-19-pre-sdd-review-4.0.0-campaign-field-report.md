# pre-sdd-review 4.0.0 캠페인 현장 기록 2회차

상태: 시점 기록. 이 문서는 현재 제품 계약을 변경하지 않는다. 다음 판의 설계 입력으로 쓴다.

기준: pre-sdd-review `4.0.0`, 이 저장소 `b2d06e6`, 2026-09-19.
근거: 같은 외부 저장소 `won-sec-ai` 의 같은 캠페인을 계속 돌린 실행 57회.
기록기에는 같은 저장소의 run 이 58건 있는데, `0a5a4e42`
(`2026-09-16-task-manager-hexagonal-layers`) 는 이 캠페인 밖이라 뺐다. 기록기 전체를
가리키는 수는 그렇다고 적는다.
판정 사슬, 이상 목록, finding 집계는 `python3 evidence/evidence.py summary --repo won-sec-ai`
출력이고, 개별 run 값은 `show --run-id` 출력이다. 비교에 쓴 커밋 해시와 diff 는
`won-sec-ai` 의 Git 이력이다.

앞 회차 기록은 `b20f20a` 의
`docs/history/2026-09-18-pre-sdd-review-campaign-field-report.md` 다. 그 문서는
`b2d06e6` 에서 지웠고 Git 이력에 있다. 이 문서는 그것을 다시 쓰지 않는다. 그 문서의
제안이 4.0.0 에 어디까지 들어갔고 실제로 얼마나 쓰였는지, 그리고 4.0.0 을 깔고 나서야
보이는 것만 적는다.

## 1. 지금까지 몇 번 돌았나

| | 3.0.4 기록 시점 | 지금 |
| --- | --- | --- |
| 캠페인 실행 | 44 | 57 |
| READY | 17 | 23 |
| REVISE | 21 | 26 |
| BLOCKED | 4 | 6 |
| abandoned | 1 | 2 |
| pending | 1 | 0 |
| finding | 집계 없음 | 378 |
| 합산 `elapsed_s` | 집계 없음 | 124,182초 = 34.5시간 |

기록기 전체(캠페인 밖 run 하나 포함)로는 58회, READY 24, finding 387, 124,776초다.
아래에서 `summary` 출력을 그대로 인용하는 자리는 58 기준이고, 그렇지 않은 곳은 57 기준이다.

계획 여덟 편의 판정 사슬이다. `V` 는 REVISE, `Y` 는 READY, `B` 는 BLOCKED,
`a` 는 abandoned 다.

| 계획 | 실행 | 판정 사슬 |
| --- | --- | --- |
| `2026-09-03-prompt-editor-ux` (A) | 6 | V Y V Y Y Y |
| `2026-09-03-prompt-test-run-1-backend` (B) | 5 | B Y Y Y Y |
| `2026-09-15-writing-style-prompt-1-backend` (D 백엔드) | 7 | V a V Y V V Y |
| `2026-09-15-writing-style-prompt-2-frontend` (D 프론트) | 11 | Y V V V V Y Y V V V Y |
| `2026-09-15-prompt-playground` (E) | 6 | B V V Y V Y |
| `2026-09-03-prompt-variable-guard` (C) | 13 | B Y V V V V V V V V Y a Y |
| `2026-09-16-prompt-category-1-backend` (F 백엔드) | 5 | Y V Y Y V |
| `2026-09-16-prompt-category-2-frontend` (F 프론트) | 4 | B Y B B |

3.0.4 보고를 쓴 뒤 열세 번을 더 돌렸고 **사슬은 짧아지지 않았다.** C 는 열한 번에서
열세 번이 되었고, D 프론트는 여덟 번에서 열한 번이 되었다. F 프론트는 네 번을 돌고도
`B Y B B` 로 끝났다. 즉 수렴하지 않는다는 성질은 3.0.4 의 수정안으로 고쳐지지 않았다.

합산 34.5시간은 게이트가 태운 시간의 **상한**이지 게이트 비용이 아니다. 3.5 를 보라.

## 2. 3.0.4 제안이 어디까지 갔나

앞 기록 2절의 일곱 제안이다. 셋째 칸이 이 캠페인의 기록에서 센 실제 사용량이다.

| 앞 기록 | 제안 | 4.0.0 반영 | 58회에서 실제로 |
| --- | --- | --- | --- |
| 2.1 | 공유 파일 원장과 선행 패스 | 들어감 | `ledger` 가 채워진 run 5 (전부 `review-only`), 판정 run 2 는 `null` |
| 2.2 | `plan turn` 기준선과 선행 계획 목록 | 들어감 | `baseline.prior_plans` 가 있는 run 7 |
| 2.3 | 기계 점검 다섯 가지 | 들어감 | `source=machine-check` finding 2건 |
| 2.4 | 부분 닫힘, 값 없는 수리는 패스 면제 | 둘 다 들어감 | `partially-closed` 1건, `repair_pass=0` **0건**, `costless_repairs` **0** |
| 2.5 | 같은 갈래는 unmapped 가 아니다 | 들어감 | 문구뿐. 기록에 표시가 없어 셀 수 없다 |
| 2.6 | reviewer 지시 계약 | 들어감 | 기록에 표시가 없어 셀 수 없다 |
| 2.7 | `head_changed_during_review` 를 좁혀라 | **안 들어감** | 안 들어간 것이 옳았다. 4절 |

읽는 법은 하나다. **4.0.0 은 거의 다 들어갔고 거의 안 쓰였다.**

네 가지가 특히 눈에 띈다.

- `repair_pass: 0` 과 `costless_repairs` 는 58회 중 **한 번도** 쓰이지 않았다. 값 없는
  수리에 패스를 면제하려고 스키마를 깨면서까지 범위를 0..2 로 넓혔는데 그 자리가 비어
  있다. 선행 패스 수리를 여기에 적으라는 것이 유일한 진입로인데, 선행 패스가 기록되지
  않으므로 진입로가 닫혀 있다. 3.3 을 보라.
- `source` 는 387건 중 337건이 `null` 이다. schema 3 기록이 51건이라 그렇다. 새 필드의
  집계는 한 판 지나야 의미가 생긴다는 뜻이고, 그동안 `summary` 는 그 사실을 말하지 않는다.
- 기계 점검이 낸 finding 이 2건이다. 캠페인 도중 손으로 짠 점검 스크립트가 낸 것은 그보다
  훨씬 많았다. 점검을 스킬 문장으로 옮겼지만 실행 자리를 정하지 않아 컨트롤러가 자기
  스크립트를 계속 썼고 그 산출을 `machine-check` 로 적지 않았다.
- 원장은 `review-only` run 다섯에만 달려 있고, 정작 F 두 계획의 판정 run 둘에는 `null`
  이다. 디스크에는 157줄짜리 원장이 그대로 있는데 freshness 기록이 그것을 잃었다.

## 3. 4.0.0 에서 새로 보이는 문제

각 항목은 증거, 원인, 수정안 순이다.

### 3.1 판정이 낡아도 기록은 낡았다고 말하지 않는다

`SKILL.md` 의 `Capture freshness` 는 이렇게 못박는다. "Any content change to the
resolved design or plan invalidates an earlier `READY` verdict." 옳은 규칙인데 그것을
확인해 주는 것이 아무것도 없다.

계획 여덟 편의 마지막 완료 run 을 꺼내 `plan.sha_end` 를 지금 디스크의 sha256 과
대 보고, `git.head_end` 를 지금 `HEAD` 와 대 봤다.

| 계획 | 마지막 판정 | 계획 본문 | `head_end` |
| --- | --- | --- | --- |
| A 편집기 UX | READY | 바뀜 | `4c0ec2693` |
| B 테스트 실행 | READY | 같음 | `4c0ec2693` |
| D 백엔드 | READY | 같음 | `4c0ec2693` |
| D 프론트 | READY | 바뀜 | `4c0ec2693` |
| E 플레이그라운드 | READY | 바뀜 | `4c0ec2693` |
| C 변수 가드 | READY | 같음 | `4c0ec2693` |
| F 백엔드 | REVISE | 바뀜 | `afd15218b` |
| F 프론트 | BLOCKED | 바뀜 | `afd15218b` |

지금 `HEAD` 는 `dev` `afd15218b` 다. 여덟 중 여섯이 `4c0ec2693` 에서 판정을 받았고 그것은
지금 `HEAD` 의 조상이다. 여덟 중 **다섯**은 본문이 그 뒤로 바뀌었다. 그중 셋(A, D 프론트,
E)은 **READY 를 들고 있으면서 본문이 바뀌었다.** 스킬 자신의 문장에 따르면 그 셋의 READY 는
무효다. `summary` 를 아무리 읽어도 이것이 안 보인다. 판정 글자만 보이고 그 판정이 무엇에
대한 판정이었는지는 run 을 하나씩 `show` 해서 손으로 해시를 다시 재야 나온다.

원인은 기록기가 run 에 묶여 있고 문서는 run 이 닫힌 뒤에도 계속 움직인다는 것이다.
`document_changed_without_repair_pass` 는 run **안에서** 바뀐 것만 본다. run 이 닫힌 뒤의
변화를 보는 것은 없다.

이 캠페인에서 그 간격이 제일 컸던 곳은 마지막이다. F 두 계획의 마지막 run 이 닫힌 뒤에
확인 리뷰어를 한 번 더 띄웠고 그 결과로 문서를 네 군데 더 고쳤다. 기록에는 REVISE 와
BLOCKED 만 남아 있고 그 뒤의 수리는 어디에도 없다.

이 표를 만든 것은 이것이다. 저장소 뿌리에서 돈다.

```sh
EV=<skill-root>/evidence/evidence.py
python3 "$EV" summary --repo won-sec-ai \
| python3 -c '
import json,subprocess,hashlib,os,sys
S=json.load(sys.stdin)
head=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True).stdout.strip()
for c in S["chains"]:
    last=[r for r in c["runs"] if r["status"]=="completed"][-1]
    rec=json.loads(subprocess.run(["python3",os.environ["EV"],"show","--run-id",last["run_id"]],
                                  capture_output=True,text=True).stdout)
    p=rec["plan"]["path"]
    cur=hashlib.sha256(open(p,"rb").read()).hexdigest() if os.path.exists(p) else None
    print(p, last["verdict"],
          "docs=" + ("same" if cur==rec["plan"]["sha_end"] else "drifted"),
          "head=" + ("same" if rec["git"]["head_end"]==head else "moved"))
'
```

**수정안.** `summary` 에 낡음 판정을 넣는다. 각 사슬의 마지막 완료 run 에 대해
`plan.sha_end`, `design.sha_end` 를 지금 파일과 다시 재고, `git.head_end` 를 지금 `HEAD`
와 대서 `stale: none | documents | head | both` 를 붙인다. 파일이 없으면 `missing` 이다.
또는 같은 일을 하는 `verify --repo <repo>` 하나를 더한다. 계산은 열 줄이고, 읽는 쪽은
게이트를 다시 열지 말지를 이 한 줄로 정할 수 있다.

### 3.2 schema 4 이상 하나가 기록 51건에서 절대 뜨지 않는다

`evidence.py:588` 근처다.

```python
"head_start_not_ancestor_of_head_end": record["git"].get("head_start_is_ancestor_of_head_end") is False,
```

`head_start_is_ancestor_of_head_end` 는 schema 4 에서 생긴 필드다. schema 3 기록에는
키가 없으므로 `.get` 이 `None` 을 주고 `is False` 가 거짓이 된다. 기록 58건 중 51건이
schema 3 이다. 그래서 `summary` 의 `head_start_not_ancestor_of_head_end` 는 빈 목록이다.

빈 목록이 사실과 다르다. run `288f4a74` 는 `eeadfd221` 에서 시작해 `4c0ec2693` 에서 끝났고,
`git merge-base --is-ancestor eeadfd221 4c0ec2693` 은 거짓이다. 검토 도중에 `HEAD` 가
**뒤로** 갔다. 그것이 이 이상이 잡으라고 만든 바로 그 모양인데, 그 run 이 schema 3 이라
잡히지 않았다.

빈 목록과 "답할 수 없는 기록뿐" 을 `summary` 가 구분하지 않는다는 것이 문제다. 읽는 쪽은
전자로 읽는다.

**수정안.** 새 필드에 기대는 이상은 답할 수 없었던 기록 수를 같이 낸다. 값을
`{"run_ids": [...], "not_evaluable": 51}` 로 바꾸거나, `summary` 에 이상별
`evaluable_records` 를 붙인다. 두 줄이면 된다. 그리고 이 규칙을 지금 한 번만 고치지 말고,
앞으로 스키마에 필드를 더할 때 따라야 할 것으로 `contract.md` 에 적는다.

### 3.3 선행 패스에 기록할 자리가 없어서 `review-only` 로 흘렀다

기록이다. 2026-09-18T11:59:01 에 run 넷이 **같은 초에** 시작했다.

| run | 시작 | mode | `repair_passes` | `ledger` | 계획 |
| --- | --- | --- | --- | --- | --- |
| `8293449e` | 11:59:01 | review-only | 1 | 있음 | B |
| `af10deec` | 11:59:01 | review-only | 1 | 있음 | C |
| `bfbd0650` | 11:59:01 | review-only | 1 | 있음 | F 백엔드 |
| `c370b93e` | 11:59:02 | review-only | 1 | 있음 | F 프론트 |
| `1855631c` | 12:03:43 | review-only | 1 | 있음 | D 백엔드 |

다섯 다 `review_only_with_repair` 이상이 붙었다. `summary` 의 그 목록은 정확히 이 다섯이다.

여기서 사실과 추측을 나눈다. **사실**은 위 표다. `review-only` 인데 수리를 했고, 다섯이 같은
원장을 달고 있고, 넷이 동시에 떴다. 스킬은 두 가지를 금지한다. `Review-only mode` 의 "Make
no file changes" 와 `Resolve authoritative inputs` 의 "On one host, run those invocations
one after another; do not overlap them".

**추측**은 왜 그랬는가다. 4.0.0 의 선행 패스는 원장을 만들고 기계 점검을 돌리고 **반입 수리를
하라고** 요구하면서, 동시에 "This pre-pass is not a recorded run" 이라고 못박는다. 그 수리는
다음 `start` 아래 `repair_pass: 0` 으로 적으라고 한다. 그런데 컨트롤러가 선행 패스 자체를
기록하고 싶으면 손에 쥔 유일한 기록 가능한 모양이 `review-only` 다. 그리고 `review-only` 는
선행 패스가 반드시 해야 하는 그 수리를 금지한다. 계약 안에 모순이 있다.

결과로 두 가지를 잃었다. 첫째, 이상 다섯이 붙었는데 그 다섯은 규율 위반이 아니라 모양이 없어서
생긴 것이다. 진짜 규율 위반과 구분되지 않는다. 둘째, **이 캠페인에서 값이 제일 컸던 활동이
측정되지 않는다.** 파일 중심 스윕은 단독 READY 여덟을 받은 계획들에서 교차 충돌 24건을 냈고
그중 여덟이 BLOCKER 였다. 기록기에는 그 활동을 담을 행이 없다.

**수정안.** 둘 중 하나를 고른다.

- **선행 패스를 기록 가능한 run 종류로 만든다.** `start --kind ledger-pass` 를 더하고 판정
  없이(`verdict: null`) 닫는다. 수리는 `repair_pass: 0`, `source: ledger-pass` 로 그 run 에
  적는다. 이상 검사에서 판정 없는 run 을 예외로 둔다.
- **`review-only` 에 원장 예외를 명시한다.** `--ledger` 를 달고 도는 `review-only` run 은
  `source: ledger-pass` 인 수리를 허용하고, `review_only_with_repair` 는 그 밖의 수리에만
  붙인다.

앞쪽을 권한다. 뒤쪽은 `review-only` 의 뜻을 흐린다.

그리고 겹침 금지 문장은 **판정을 내는 호출**에만 걸도록 좁힌다. 원장 스윕을 계획마다 하나씩
차례로 도는 것은 값이 없다. 같은 파일을 여덟 번 다시 읽는 일이다.

### 3.4 `outcome` 이 58회 중 0회다

`summary.counts.outcome` 이 전부 0 이다. `good`, `false-ready`, `noisy`, `abandoned`
넷 다 0 이고 `recorded` 도 0 이다.

이것이 뜻하는 바는 단순하다. **READY 가 무엇을 뜻했는지 아무도 한 번도 확인하지 않았다.**
게이트를 34.7시간 돌렸는데 그중 어느 READY 가 실제로 구현을 통과시켰는지, 어느 것이
거짓 READY 였는지 아는 길이 없다. 그러면 캠페인 안에서 결함을 줄였다는 것 말고는 게이트의
값을 증명할 자료가 없다.

원인은 스킬이 이것을 컨트롤러 책무에서 명시적으로 빼놓았다는 것이다. "Recording an
`outcome` is not a controller duty." 그리고 SDD 워커나 사용자에게 넘긴다. 그 둘은 스킬을
읽지 않는다.

**수정안.** 둘 중 하나다. 애매한 중간은 두지 않는다.

- **SDD handoff 의 일부로 만든다.** `READY` 최종 보고의 마지막 줄에 `outcome` 명령줄을
  완성된 형태로 출력한다. 구현이 끝난 뒤 사용자나 워커가 붙여 넣기만 하면 되게 한다.
  그리고 `summary` 에 `outcome_coverage` 를 눈에 띄게 낸다.
- **걷어낸다.** 58회 0% 는 기능이 아니라 죽은 무게다. `outcome` 을 지우면 명령 하나,
  스키마 한 덩이, 문서 한 절이 준다.

### 3.5 `elapsed_s` 는 게이트 비용이 아니다

`summary.cost` 가 준다. 중앙값 1,406초, 최대 18,562초, 합 124,776초.

최대 18,562초짜리는 `a051e1eb` 다. 5.2시간짜리 검토가 아니다. `start` 와 `finish` 사이에
컨트롤러가 수리하고 스크립트 짜고 다른 일을 한 시간이 전부 들어 있다. abandoned run
`a9692ed3` 은 9,882초인데 `finish` 가 없어 `reviewers` 조차 기록되지 않았다. 그 2.7시간이
무엇이었는지 기록만 보고는 알 수 없다.

`cost` 라는 이름이 이것을 비용으로 읽게 만든다. 읽는 쪽이 "게이트 한 바퀴에 23분" 으로
읽으면 틀린다. 실제로는 "게이트를 여는 순간부터 닫는 순간까지 세션이 흐른 시간" 이다.

**수정안.** 이름과 뜻을 맞춘다. `cost.elapsed_s` 를 `wall_clock_s` 로 바꾸고, 그것이
컨트롤러 작업을 포함한다고 `evidence/README.md` 에 한 줄 적는다. 진짜 비용을 재고 싶으면
`finish` 페이로드에 `reviewer_dispatches` 와 그 합산 초를 받는다. 컨트롤러가 이미 아는
값이라 새로 측정할 것이 없다.

### 3.6 degraded 열 중 여섯이 호스트 한도다

`execution` 은 full 46, degraded 10, blocked 0 이다. degraded 열의 이유를 세면 이렇다.

| 이유 | 수 |
| --- | --- |
| `fresh-agents-unavailable-thread-limit; reused-reviewers` | 5 |
| `focused-risk-role-not-reobtained` | 4 |
| `fresh-risk-and-closure-agent-unavailable-thread-limit; reused-agents` | 1 |

여섯이 스레드 한도다. 스킬은 이 경우를 이렇게 정한다. "If a fresh independent primary
reviewer cannot be obtained, return `BLOCKED`." 실제로는 `execution=blocked` 가 0 이고
컨트롤러가 에이전트를 돌려 쓰고 degraded 로 적었다. 판정 BLOCKED 여섯은 전부 다른
이유(입력 미해결)다.

스킬이 호스트 한도를 고칠 수는 없다. 그러나 지금 계약은 사실상 지켜지지 않는 문장이고,
지켜지지 않는 문장은 다른 문장의 무게까지 깎는다.

**수정안.** 한도로 인한 degraded 를 1급으로 인정한다. `degraded_reasons` 열거에
`host-agent-limit` 을 두고, 그 이유로 degraded 인 run 은 핸드오프 재사용만 금지하고
판정은 그대로 인정한다. 그리고 `summary.counts` 에 `degraded_reasons` 집계를 낸다. 지금은
`show` 를 58번 돌려야 위 표가 나온다.

### 3.7 경로가 아직 있는지 보는 것이 기계 점검에 없다

기계 점검 다섯은 전부 **문서 안의 수 세기**다. 계획이 이름으로 대는 경로가 저장소에 아직
있는지는 목록에 없다.

이 캠페인에서 기준 트리가 밑에서 움직였다. `dev` 가 운영 콘솔의 목록 화면을 루트에서
`/prompts` 로 옮기고 콘솔 홈을 메뉴 화면으로 바꿨다. 계획 넷이 루트 가정을 들고 있었다.
경로 존재 점검을 손으로 짜서 다섯 계획에 돌렸더니 바로 걸렸다.

같은 점검이 오탐도 냈다. 처음 판은 같은 계획의 `Create:` 만 제외해서 오탐 8건이 나왔다.
없는 경로가 **사슬 안 다른 계획**이 만드는 것이었다. 제외 규칙을 사슬 전체의 `Create:` 로
넓히자 오탐이 0 이 되었다.

**수정안.** 기계 점검에 여섯째를 더한다.

```
6. 계획이 백틱으로 대는 모든 저장소 경로가 그 계획의 turn 에 존재하는지.
   제외는 사슬 안 어느 계획이든 `Create:` 로 선언한 경로 전부다.
   같은 계획의 `Create:` 만 제외하면 오탐이 난다.
```

제외 규칙을 같이 적는 것이 핵심이다. 안 적으면 다음 사람이 같은 오탐 8건을 다시 만든다.

### 3.8 기록기가 컨트롤러를 네 번 잡았고 네 번 다 아무 일도 안 났다

판정과 기록이 어긋난 run 이다.

| 이상 | run | 무슨 뜻인가 |
| --- | --- | --- |
| `ready_with_unresolved_findings` | `a26035ea` | READY 인데 닫히지 않은 finding 이 있다 |
| `revise_without_unresolved_finding` | `4c1570df` | REVISE 인데 닫히지 않은 finding 이 없다 |
| `document_changed_without_repair_pass` | `ba2ad67b` | 문서가 바뀌었는데 수리 패스가 0 이다 |
| `repo_reality_citing_documents_only` | `4c1570df` 의 `PSDR-013` | `repo-reality` 인데 근거가 문서뿐이다 |

넷 다 스킬이 명시적으로 금지한 모양이다. 넷 다 기록기가 정확히 잡았다. 그리고 넷 다
판정을 바꾸지 않았고 그 자리에서 아무 조치도 없었다. "Anomalies do not change the verdict"
가 옳은 설계인 것과, 이상이 떴을 때 컨트롤러가 무엇을 해야 하는지 아무 데도 안 적힌 것은
다른 문제다.

`summary.counts.observation` 이 anomalous 17, normal 39 다. 그리고
`anomalous_verdict` 가 READY 7, REVISE 7, BLOCKED 3 이다. **READY 24개 중 7개가 관찰 이상을
달고 있다.** 29%다.

**수정안.** `finish` 가 돌려주는 이상 목록에 대한 처리를 한 줄로 정한다. 지금은 "READY 면
`Anomalies:` 줄로 출력하라" 뿐이다. 여기에 더한다. 판정과 finding 상태가 어긋나는 이상
셋(`ready_with_unresolved_findings`, `revise_without_unresolved_finding`,
`repair_without_repaired_finding`)이 뜨면 컨트롤러는 `finish` 페이로드를 고쳐 다시 내거나,
왜 그대로 두는지를 최종 보고에 한 줄 적는다. 이 셋은 저장소 사실이 아니라 컨트롤러가 자기
페이로드를 잘못 쓴 것이므로 되돌릴 수 있다.

## 4. `head_changed_during_review` 에 대한 정정

앞 기록 2.7 은 이렇게 썼다. "`head_changed_during_review` 가 일곱 번 떴는데 이 캠페인에서
`HEAD` 는 한 번도 안 움직였다. 커밋하지 않는 문서만 바뀌었다." 그리고 이상을 좁히라고
제안했다. 4.0.0 은 그 제안을 넣지 않았다. **안 넣은 것이 옳았다.**

기록을 다시 봤다. 이상이 붙은 run 아홉의 `head_start` 와 `head_end` 다.

| run | `head_start` | `head_end` | 두 커밋 사이 변경 파일 |
| --- | --- | --- | --- |
| `745bf4bc` | `5f13916` | `7ddd035` | 170 |
| `01dd5214` | `7ddd035` | `5725c95` | 83 |
| `04bb5913` | `5725c95` | `e2f4289` | 1 |
| `2d463dfb` | `e2f4289` | `4b0df16` | 0 |
| `b3f8d714` | `4b0df16` | `4c0ec26` | 2 |
| `38ef7013` | `4c0ec26` | `eeadfd2` | 0 |
| `288f4a74` | `eeadfd2` | `4c0ec26` | 0 |
| `d3a91573` | `4c0ec26` | `afd1521` | 343 |
| `4a2d400b` | `4c0ec26` | `afd1521` | 343 |

여덟 커밋 전부 지금도 저장소에 있다. 아홉 번 다 `HEAD` 가 실제로 움직였다. 앞 기록의
"안 움직였다" 는 틀렸다. 이상은 `head_start != head_end` 하나만 보므로 기계가 틀릴 여지가
없는 자리였다.

다만 앞 기록의 **불만**은 반쯤 옳았다. 아홉 중 셋(`2d463dfb`, `38ef7013`, `288f4a74`)은
두 커밋 사이 변경 파일이 0 이다. 트리가 같은 커밋 사이를 오간 것이라 검토에 아무 뜻이 없다.
그러면 좁히는 것이 맞아 보인다. 여기서 반대 증거가 나온다.

넷째 칸은 이렇게 셌다.

```sh
python3 "$EV" show --run-id <run-id> \
| python3 -c 'import sys,json; g=json.load(sys.stdin)["git"]; print(g["head_start"], g["head_end"])' \
| xargs -n2 sh -c 'git diff --name-only $0..$1 | wc -l'
```

변경 파일을 계획이 이름으로 대는 경로와 교집합해 봤다. 아홉 중 여섯이 교집합 0 이고,
캠페인에서 제일 무거운 BLOCKER 를 품은 `4a2d400b` 조차 343개 중 2개만 걸린다. 관련도로
좁혔다면 그 둘은 소음으로 떨어졌을 것이다.

교집합 쪽 수에는 단서를 달아 둔다. 계획이 대는 경로는 **오늘의 계획 본문**에서 긁은 것이고,
A, D 프론트, E, F 프론트 넷은 그 run 들 뒤에 리베이스로 본문이 바뀌었다. 그러니 여섯 개의
0 은 당시 값과 다를 수 있다. 아래 결론은 그 여섯이 아니라 F 두 run 의 "계획이 이름으로 대지
않은 파일" 쪽에 걸려 있으므로 그대로 선다.

**교집합이 작은 것이 바로 그 BLOCKER 의 정체이기 때문이다.** `dev` 가 바꾼 것은
`_lib/home-menu.ts` 와 콘솔 홈 `page.tsx` 였고, 계획이 그 파일들을 이름으로 대지 않는다는
것이 결함 자체였다. 계획의 경로 목록으로 관련도를 재면, 계획의 경로 목록이 틀렸을 때
그 사실이 감춰진다.

**결론.** 이 이상은 탐지기가 아니라 **교차 확인**이다. 값은 싸고 계획과 독립이라는 데 있다.
좁히지 않는다.

**수정안.** 좁히는 대신 크기를 붙인다. `finish` 때 `head_start..head_end` 의 변경 파일 수를
세어 기록에 넣고, `summary` 가 그 수를 이상과 함께 낸다. 0 이면 읽는 쪽이 넘기면 되고,
343 이면 멈춘다. 판정은 읽는 쪽이 한다. 기계가 미리 버리지 않는다.

## 5. 남아 있는 제일 큰 문제: 수리가 다음 회차의 결함을 만든다

사슬이 왜 안 줄어드는지에 대한 가장 단순한 설명이다. 문서를 고치는 것은 컨트롤러 하나뿐이고,
컨트롤러가 쓴 새 텍스트를 보는 것은 다음 회차의 리뷰어뿐이다. 그래서 수리가 끝나는 순간
문서에는 **아무도 안 본 텍스트**가 생긴다.

이 세션 끝의 확인 리뷰어 한 번을 예로 든다. 이 숫자는 기록기의 것이 아니라 컨트롤러 집계다.
그 회차는 기록되지 않았다.

- 앞선 두 run 의 finding 열아홉을 닫고 나서, 확인 리뷰어 하나를 좁게 띄웠다.
- 아홉이 나왔고 그중 **여섯이 그 직전 수리가 만든 것**이었다.
- 제일 무거운 것은 키를 쓰는 Task 가 키를 만드는 Task 보다 먼저 돌게 되어 있던 것이다.
  `AppMessageKey = keyof typeof ko` 이므로 그 Task 의 typecheck 가 자기 관문에서 죽는다.
  그 순서를 만든 것이 앞 회차의 내 수리였다.

4.0.0 의 `repair-impact map` 과 종결 리뷰어가 이것을 보라고 있는 것은 맞다. 그런데 종결
리뷰어의 범위는 "원 기록 닫힘 + 지도된 영향" 이다. 위 여섯 중 넷은 원 기록과도 지도와도
무관한 자리였다. 수리가 Task 경계를 넘어 **문서의 다른 곳**을 건드렸기 때문이다.

**수정안 두 가지를 같이 본다.**

- **수리 diff 를 종결 리뷰어에게 준다.** 지금은 수리된 문서 전체와 원 기록과 영향 표를 준다.
  거기에 `diff` 를 더한다. 리뷰어가 "이번에 바뀐 줄" 을 알면 그 줄부터 본다. 문서가 100KB 를
  넘으면 전체를 다시 읽는 것은 실제로 불가능하다.
- **수리가 만든 순서 의존을 기계로 본다.** 이 캠페인에서 되풀이된 모양이다. 계획은 Task 를
  순서대로 실행하고 각 Task 끝에서 초록이어야 한다. 그러면 "Task N 이 쓰는 심벌 또는 키를
  Task M 이 만들고 M > N" 은 셀 수 있다. 기계 점검 일곱째 후보다.

## 6. 이번 판에서 만들어 효과를 본 것

앞 기록 4절과 겹치지 않는 것만 적는다.

1. **치환 스크립트의 유일성 단정.** 앞 기록에도 있으나 이번에 값이 더 분명해졌다. 모든 치환
   앞에 `assert s.count(old) == n` 을 박았다. 이번 캠페인에서 **여섯 번** 걸렸고 그때마다
   쓰기 전에 멈췄다. 걸린 것 중에는 같은 코드 블록이 계획 안에 두 번 있는 줄 알았는데
   하나였던 경우, 줄바꿈 때문에 앵커가 안 맞은 경우가 있었다. 손상은 0건이다.
2. **게이트마다 `HEAD` 를 다시 재기.** 세션 시작 때 찍힌 git status 를 믿지 않는다.
   이번에 체크아웃이 세션 도중에 옮겨졌고, 그것을 늦게 알았다.
3. **좁은 확인 리뷰어 하나.** 전면 게이트를 다시 여는 대신 확인 리뷰어 하나를 좁게 띄웠다.
   한 바퀴 값으로 BLOCKER 하나를 포함해 아홉을 냈다. 전면 게이트 한 바퀴보다 훨씬 싸다.
   5절의 문제에 대한 현실적인 응급 처치다.
4. **오라클 기준으로 거르기.** "이것이 구현되면 어느 오라클이 잡는가" 로 거른다. typecheck,
   테스트, 린트가 잡는 것은 계획에 적어도 값이 작다. 아무 오라클도 안 잡는 것만이 게이트의
   수확이다. 이 기준으로 거르면 리뷰어가 낸 것의 절반 이상이 내려간다.
5. **한 바퀴 더 돌지 않기로 정하기.** 남은 것이 오라클이 덮는 종류면 멈춘다. 판을 늘리는 것이
   이 캠페인을 34.7시간 태운 동작이다.

## 7. 해봤는데 틀린 것

- **`head_changed_during_review` 를 좁히자는 제안.** 앞 기록 2.7. 4절에서 뒤집었다.
  전제였던 "HEAD 는 안 움직였다" 가 기록과 다르다.
- **Task 번호를 기억으로 대기.** D 프론트의 레일 Task 를 8번으로 알고 수리했다. 5번이었다.
  확인 리뷰어가 바로잡았다. 긴 문서에서 Task 번호는 매번 다시 읽어야 한다.
- **저장소 사실을 기억으로 주장하기.** 응답 zod 스키마가 `.strict()` 라 모르는 키를 막는다고
  적었다. 디스크를 보니 `.strict()` 인 것은 요청 스키마 하나뿐이고 응답 스키마는 평범한
  `z.object()` 다. 모르는 키는 거절이 아니라 제거다. 단정을 통째로 다시 썼다.
- **닫힌 목록을 한쪽만 고치기.** 새 메시지 키를 `ko` 에만 넣었다. `ko` 와 `en` 의 키 집합
  동등성을 단정하는 테스트가 있다. 앞 기록 3절이 이름 붙인 네 갈래 중 하나를, 그 이름을
  알면서 다시 저질렀다. 갈래를 아는 것과 매번 확인하는 것은 다르다.

## 8. 다음 판에 넣을 것

값과 드는 품을 같이 본 순서다.

| 순위 | 항목 | 절 | 드는 품 |
| --- | --- | --- | --- |
| 1 | `summary` 에 낡음 판정 또는 `verify` 명령 | 3.1 | 작다 |
| 2 | 선행 패스를 기록 가능한 run 종류로 | 3.3 | 중간 |
| 3 | 이상에 `not_evaluable` 수 붙이기 | 3.2 | 작다 |
| 4 | 경로 존재를 기계 점검 여섯째로, 제외 규칙까지 | 3.7 | 작다 |
| 5 | 종결 리뷰어에게 수리 diff 주기 | 5 | 작다 |
| 6 | `head_changed_during_review` 에 변경 파일 수 붙이기 | 4 | 작다 |
| 7 | `outcome` 을 handoff 에 넣거나 걷어내기 | 3.4 | 중간 |
| 8 | `cost.elapsed_s` 이름과 뜻 맞추기 | 3.5 | 작다 |
| 9 | `degraded_reasons` 집계와 `host-agent-limit` | 3.6 | 작다 |
| 10 | 판정과 finding 이 어긋나는 이상의 처리 규칙 | 3.8 | 작다 |
| 11 | Task 순서 의존 기계 점검 | 5 | 중간 |

1번부터 6번까지가 이 캠페인에서 실제로 물린 것이고, 열 줄에서 쉰 줄 사이에 들어간다.

한 가지를 더 적는다. 4.0.0 의 교훈은 **기능을 더 넣는 것이 아니다.** 2절의 표가 말하듯 4.0.0
은 거의 다 들어갔고 거의 안 쓰였다. 위 목록에서 새 기능은 2번 하나뿐이고 나머지는 이미 있는
것을 보이게 하거나 이름을 맞추는 일이다. 다음 판에서 기능 하나를 더하고 싶으면, 그 전에
`repair_pass: 0` 이 왜 0건인지부터 본다.

## 9. 이 문서를 접을 때

3절과 8절이 설계와 구현 계획으로 옮겨지면 이 문서는 지운다. Git 이력에서 볼 수 있다.
수정안을 제품에 넣을 때는 `docs/maintainers/products/pre-sdd-review/contract.md` 의
`함께 고칠 파일` 을 따른다.
