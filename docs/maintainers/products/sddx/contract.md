# sddx 계약

이 문서는 SDDx가 무엇을 소유하고, 언제 켜지고, 워커를 어떻게 띄우고, 결과를
어떻게 판정하는지 정하는 규범입니다. 동작을 바꾸기 전에 이 문서와 맨 아래
「함께 고칠 파일」을 확인하세요.

## 이 문서에서 찾을 수 있는 것

- 제품 이름, 소유 경계, 켜지는 조건: 「제품 정체」, 「하드 게이트」
- 호출 인자와 워커 종류 고르기: 「호출과 백엔드 선택」
- 리뷰어 모델과 추론 강도, XHigh 리뷰어 정의: 「리뷰어와 강도」
- 과제를 워커에 나누는 단위: 「과제 단위」
- 구현 워커의 모델, 강도, 세션 재사용: 「구현 워커의 모델과 강도」
- 워커가 하면 안 되는 일: 「워커 부작용과 비밀」
- Grok 샌드박스 준비·정리: 「Grok 샌드박스 프로파일」
- 브리프 작성과 워커의 읽기·검색 범위: 「브리프와 읽기 범위」
- 과제를 완료로 볼 수 있는 조건: 「완료 판정」
- `resolve_backend.py` 출력과 필수 플래그: 「백엔드 해석」
- Grok 도구 제한: 「Grok 워커 도구와 MCP 초기화」
- `extract_task.py`, `run_worker.py`의 명령·기록·종료 코드·타임아웃: 「실행 helper와 시도 증거」
- 작업 기록 안의 현재 상태 블록: 「현재 상태」

## 용어

| 말 | 뜻 |
| --- | --- |
| 호스트 | 스킬을 실행하는 프로그램입니다. `claude-code`와 `codex` 두 가지뿐입니다. |
| 오케스트레이터(controller) | `/sddx` 또는 `$sddx`를 받은 그 호스트 세션입니다. 과제를 나눠 보내고, 결과를 확인하고, 리뷰를 돌립니다. |
| 워커(worker) | 구현만 맡는 외부 CLI 프로세스입니다. Cursor Agent 또는 Grok Build입니다. |
| 백엔드(backend) | 워커로 쓸 CLI 종류입니다. 값은 `cursor` 또는 `grok`입니다. |
| 백엔드 선택(picker) | 백엔드 인자가 없을 때 사용자에게 한 번 묻는 선택지입니다. |
| 작업 기록(ledger) | Superpowers SDD가 계획마다 두는 진행 기록 파일입니다. |
| 보내기(dispatch) | 워커나 리뷰어에게 일을 맡겨 띄우는 것입니다. |
| 브리프(brief) | 워커가 받는 과제 한 건의 설명서입니다. |
| 러너(runner) | 워커를 띄우고 시도를 기록하는 `scripts/run_worker.py`입니다. |
| 시도(attempt) | 워커 실행 한 번입니다. 시도마다 폴더가 하나 생깁니다. |
| 작업 트리(worktree) | Superpowers가 쓰는 Git 작업 트리입니다. linked worktree는 `git worktree`로 추가한 작업 트리입니다. |
| 강도(effort) | 추론 강도입니다. High와 XHigh가 있고 XHigh가 더 깊게 생각합니다. |
| 판정(ruling) | 워커가 막혔거나 설계가 모호할 때 오케스트레이터가 내리는 결정입니다. |
| 수정 라운드(fix round) | 리뷰에서 나온 결함을 고치는 회차입니다. |

## 제품 정체

제품 ID, 스킬 `name`, 디렉터리 이름은 `sddx`입니다. 표시 이름은 `SDDx`입니다.
호출은 Claude Code `/sddx`, Codex `$sddx`입니다.

지원 호스트는 `claude-code`와 `codex`뿐입니다. Cursor CLI와 Grok CLI는 구현
워커이지 호스트가 아니므로 `cursor`와 `grok`을 `supported_hosts`에 넣지 않습니다.

소유 경계는 다음과 같습니다. SDD 본문을 이 스킬에 복사하지 않습니다.

- Superpowers SDD: 작업 트리, 작업 기록, `sdd-workspace`, review-package, 리뷰어
  프롬프트, 수정 반복(fix loop), 브랜치 전체 리뷰(whole-branch review),
  워크스페이스와 리포트 파일 이름.
- `sddx`: 인자 해석, 백엔드 선택, `resolve_backend.py`, 구현 워커 argv, 워커
  제약·실행 증거 확인, 리뷰 모델·강도 선택, 과제 구간 추출(`extract_task.py`).

## 하드 게이트

설치된 Superpowers `subagent-driven-development`의 흐름을 따르되, 구현 워커
보내기, 리뷰 모델·강도, 워커 증거 확인에는 SDDx 규칙이 우선합니다. Superpowers
파일을 고치지 않습니다. 오케스트레이터 세션에서 직접 구현하지 않습니다.

사용자 메시지에 `/sddx` 또는 `$sddx`가 있을 때만 활성화합니다. 슬래시·달러
호출이 없는 외부 구현 요청, native SDD, executing-plans(Native 포함),
writing-plans, pre-sdd-review로는 켜지 않습니다.

## 호출과 백엔드 선택

인자는 `sddx <plan-file> [cursor|grok|c|g]`입니다. `c`는 `cursor`, `g`는
`grok`입니다. 한 호출은 계획 하나입니다. 계획 경로가 없거나 파일이 아니면
추측하지 말고 한 번 묻습니다.

- 백엔드 인자가 있으면 선택을 묻지 않습니다.
- 인자가 없으면 이 계획에서 한 번만 묻습니다. Claude Code는 AskUserQuestion,
  Codex는 번호 있는 선택지로 한 번 묻고 답을 기다립니다. 선택지는 Grok CLI와
  Cursor Agent (Grok)입니다. 과제마다 다시 묻지 않습니다.
- 고른 값은 작업 기록에 `Backend: cursor|grok`로 적고 그 계획의 모든 과제에
  유지합니다.
- 쓸 수 있는 백엔드가 하나뿐이어도 자동으로 고르지 않습니다. 그 사실과 빠진
  백엔드의 `reason`을 보여 주고, 백엔드 인자가 없었다면 확인을 받은 뒤에만
  진행합니다.
- 요청한 백엔드가 없으면 다른 쪽으로 바꾸지 않고 멈춥니다. 둘 다 없으면
  `BLOCKED`입니다.

## 리뷰어와 강도

과제 리뷰어, 범위 재리뷰어(scoped re-reviewer), 최종 리뷰어는 호스트
네이티브입니다. Claude Code는 Task, Codex는 `spawn_agent`로 띄웁니다. 외부
프로세스는 구현 워커뿐입니다.

### 모델

- 오케스트레이터는 `/sddx` 또는 `$sddx`를 받은 세션의 모델·강도 그대로입니다.
  더 싼 모델, 최종 최상위 모델, 구현 워커와 같은 모델 계열로 바꾸지 않습니다.
- 모든 과제 리뷰·재리뷰·최종 리뷰는 보내는 시점의 오케스트레이터 모델을
  따릅니다. 일반 SDD의 저비용 모델 선택이나 최종 최상위 모델 선택보다 이 규칙이
  우선합니다.
- 호스트가 지원하면 모델을 상속하고, 명시해야 하면 확인된 같은 모델 ID를
  씁니다. 특정 모델 계열로 고정하거나 리뷰만 다른 모델로 내리지 않습니다.
- 모델 ID를 확인할 수 없으면 추측하지 않고, 상속했다는 사실과 ID 미확인을
  기록합니다.

네이티브 리뷰어에 닿지 못하면(한도 소진, spawn 불가) 리뷰를 조용히 다른 곳으로
옮기지 않습니다. 순서는 다음과 같습니다.

1. 막힌 조건이 풀릴 때까지 기다렸다가 네이티브로 다시 보냅니다.
2. 오케스트레이터 호스트가 제공하는 다른 네이티브 경로를 씁니다.
3. 멈추고 사용자에게 묻습니다.

리뷰를 네이티브 밖으로 옮기는 근거는 사용자의 답뿐이며, 그때도 구현자와 같은
모델 계열은 마지막 선택입니다. 자기 작업을 자기가 검토하면 이 절이 지키려는
독립성이 사라지기 때문입니다. 바뀐 호스트·모델·사유는 현재 상태 블록과 해당
리뷰 줄마다 남깁니다.

### 강도

- 리뷰 강도는 세션 강도와 따로 정합니다. Claude Code에서 High는 SDD가 쓰던
  방식 그대로 `model` 인자 없이 보내는 것이고, XHigh는 `model` 인자 없이
  `subagent_type`을 `sddx:sddx-reviewer-xhigh`로 지정하는 것입니다. 리뷰어에
  `model` 오버라이드를 넘기지 않습니다.
- XHigh 조건(trigger)은 lock·순서·공유 상태 변경, auth·권한·secret·sandbox
  경계 변경, 라운드 4–5 재리뷰, 반복해서 놓친 결함입니다.
- 판단 근거는 review-package stat, 과제 브리프, 변경 파일 경로, 작업
  기록입니다. diff 본문을 읽어 정하지 않습니다.
- 파일 수, 줄 수, 구현 난이도, 짧은 diff, 최종 리뷰라는 사실은 조건이
  아닙니다. 재리뷰는 원래 결함의 위험도를 유지합니다.
- 세션 강도가 이미 XHigh 이상이면 더 올리지 않고, 세션을 낮추지도 않습니다.
- 작업 기록에는 모든 리뷰 보내기를 적습니다. High는 한 줄이고, XHigh는 조건과
  구체 경로를 함께 적습니다. 조건을 대지 못하면 High입니다.

### XHigh 리뷰어 정의

정의 파일은 `agents/sddx-reviewer-xhigh.md`이고 Task 이름은
`sddx:sddx-reviewer-xhigh`입니다. 파일 frontmatter 이름만으로는 Task가 찾지
못합니다.

- `plugin.json`에 `agents` 키를 두지 않습니다. 기본 `agents/*.md` 스캔이 Claude
  Code 인벤토리와 Task 등록을 모두 채웁니다. 중첩 경로나 `plugin.json` `agents`
  필드를 쓰면 `plugin details`가 Agents (0)을 보고합니다.
- 설치 링크는 두 개 그대로이며 새 설치 단계를 추가하지 않습니다.
- 정의가 없으면(Codex에는 항상 없고, Claude Code에서도 로딩에 실패하면
  없습니다) 요청 강도를 지정할 수 없다고 보고한 뒤 기본 방식으로 보냅니다.
  다른 모델이나 강도로 대체하지 않고, 정의를 새로 만들지 않으며, 정의가 없다는
  이유로 실행을 `BLOCKED`로 세우지 않습니다.

## 과제 단위

한 워커가 여러 계획 과제를 묶지 않습니다. 계획 제목 하나가 워커 하나, 리뷰
패키지 구간 하나입니다. 같은 모양의 한 줄 수정이어도 묶지 않습니다.

중첩 native SDD로 내려가지 않습니다. 한 단계 아래 서브에이전트에
`subagent-driven-development`를 통째로 맡기지 않습니다.

계획이 이름 붙이지 않은 일은 보내기 전에 한 번 묻습니다. “끝까지 돌려”는
계획에 있는 과제만 덮습니다.

## 구현 워커의 모델과 강도

두 백엔드 모두 Grok 4.7만 씁니다. `-fast` 변형은 지원하지 않습니다.

- Grok: resolver가 확인한 `grok-4.7`을 `--model`로 넘기고, 강도는
  `--reasoning-effort` 또는 `--effort`로 넘깁니다. `grok-4.7-build-fast`,
  `grok-4.6`, `grok-4.5`는 넘기지 않습니다.
- Cursor: 버전 세그먼트가 `4.7`이고 `-fast`로 끝나지 않는 확인된 id만
  넘깁니다.

구현 강도는 과제 난이도 표에 따라 과제마다 High 또는 XHigh입니다.

- 세션 강도를 구현에 복사하지 않습니다. 리뷰어 XHigh가 구현 XHigh를 강제하지
  않습니다.
- High: 요구가 분명하고 로컬·기계적인 변경, 단순한 통합.
- XHigh: 동시성·race·잠금·순서·공유 상태, auth·권한·secret·sandbox 경계, 여러
  하위 시스템이 얽힌 부작용.
- 설계 모호함은 XHigh가 아니라 오케스트레이터 판정으로 풉니다. 이유를 대지
  못하면 High입니다.

세션 재사용 규칙은 다음과 같습니다.

- 새 과제는 새 워커입니다. 강도가 오르면 새 워커입니다.
- 수정 라운드 1–3은 요청 강도가 같을 때만 같은 워커 세션을 재개(resume)합니다.
  라운드 4–5는 새 워커와 XHigh입니다.
- 워커가 `NEEDS_CONTEXT` 또는 `BLOCKED`를 반환하면 판정한 뒤 같은 백엔드로 다시
  보냅니다.
- 워커에 `--worktree`를 넘기지 않습니다. cwd는 현재 Superpowers 작업
  트리입니다.

## 워커 부작용과 비밀

호스트 자격 증명이나 환경 값을 워커 프롬프트나 `--prompt-file`에 넣지 않습니다.
워커가 push, publish, 공유 브랜치 갱신처럼 호스트 밖 부작용을 필요로 하면 멈추고
`BLOCKED`입니다. 그 결과를 리뷰 통과 `DONE`으로 쓰지 않습니다.

## Grok 샌드박스 프로파일

Grok 워커를 보낼 때는 다음 순서를 지킵니다. 새 과제와 재개 모두 같습니다.

1. 워커 실행 직전에 `prepare_grok_sandbox.py prepare`를 호출합니다. prepare가
   실패하면 워커를 시작하지 않습니다.
2. 반환된 작업용 프로파일로 resolver `argv_prefix`에 있던 `--sandbox` 값 하나를
   바꿉니다. 워커 프롬프트 전체는 `--rules`로 넘깁니다.
3. 워커와 워커가 실행한 작업이 끝나면, 성공이든 실패든
   `prepare_grok_sandbox.py cleanup`을 호출합니다.

정리에 실패하면 다른 파일을 덮어쓰지 않고, 남은 차이와 상태 기록 위치를 작업
기록에 남깁니다. 생성 설정과 복원 상태는 제품 산출물도, 커밋 대상도 아닙니다.

## 브리프와 읽기 범위

### 브리프 만들기

- 보내기 전에 오케스트레이터는 `extract_task.py --global-constraints`로 과제를
  뽑고, 필요한 조건과 과제 참고자료를 채웁니다.
- 계획이 전체 실행에 대해 한 번만 적어 두는 제약은 그 플래그가
  `Global Constraints` 절로 브리프 앞에 붙입니다. 손으로 다시 복사하지 않습니다. 워커는
  계획을 읽을 수 없으므로 브리프에 없는 제약은 워커에게 없는 것과 같고, 리뷰가
  뒤늦게 워커가 피할 방법이 없던 결함으로 보고하게 됩니다.
- 전체 계획을 참고자료로 넘기지 않습니다. 새 호출과 재개 모두 문서 경계를 직접
  적습니다.
- 브리프의 검증은 `Worker checks`와 `Host checks`로 나눕니다. 과제의
  Host checks는 그 과제 리뷰 전에 돌리며 계획 끝으로 몰지 않습니다.

### 읽기와 검색

- 브리프의 `Search paths:`에 구체적인 소스·테스트 파일과 디렉터리를 적습니다.
  워커는 명시된 파일부터 직접 읽습니다.
- 내용 검색이 필요하면 이 경로를 도구 인자로 지정합니다. 파일 glob만으로 경로가
  제한된다고 가정하지 않습니다. 검색 경로가 없으면 명시된 파일을 직접 읽거나
  오케스트레이터에 빠진 경로를 요청합니다. 워크스페이스 전체 내용 검색은 하지
  않습니다.
- 워커는 필요한 소스·테스트를 읽을 수 있지만 전체 계획은 링크·셸·검색·Git
  이력으로도 읽지 않습니다. 부족한 결정은 `NEEDS_CONTEXT`입니다.
- `Search paths`는 내용 검색을 제한합니다. 현재 작업 트리 안의 파일명 목록
  조회(root 포함)와 그 과제에 필요한 저장소 ignore·빌드·테스트 설정 직접 읽기는
  허용된 확인입니다. 이것만으로 범위 이탈(scope deviation)이나 별도 판정을
  요구하지 않으며, 다른 이탈이 없으면 `Scope deviations: none`이 맞습니다. 이
  허용은 전체 계획 본문·자격 증명·비밀정보 읽기를 포함하지 않습니다.

### 워커 보고

- scope deviations 항목은 필수입니다. 시도하거나 수행한 행동·대상·결과를 적고,
  계획 원문을 다시 복사하지 않습니다. 이탈한 뒤 바로잡았어도 깨끗한 `DONE`이
  아닙니다.
- 테스트 래퍼를 쓰면 전체 명령의 exit와 실제 테스트 exit를 구분합니다.

## 완료 판정

프로세스 exit 0만으로 과제를 완료 처리하지 않습니다. 워커 보고서의 테스트 결과,
과제 변경 커밋, 실제 도구 호출·결과(tool-call/results) 기록, 네이티브 리뷰를
확인해야 합니다.

- 작업 기록의 역할 준수는 `PASS`, `FAIL`, `UNVERIFIED`로 적습니다.
- 읽기 시도와 실제 내용 반환을 구분하고, 셸·검색 도구 결과도 확인합니다.
  검색이 계획의 일부 줄을 반환해도 계획 내용 읽기에 해당합니다.
- 금지된 문서 읽기가 성공했으면 테스트 성공과 무관하게 `FAIL`, 기록이 없거나
  불완전하면 `UNVERIFIED`입니다. 둘 다 깨끗한 `DONE`으로 올리지 않습니다.
- 보고서와 다른 관측은 리뷰어에게 전달합니다. 나중에 인정하거나 정상 호출을
  했다고 앞선 위반이 지워지지 않습니다. 필요한 조치는 기존 판정으로 정합니다.
- `BLOCKED`, `NEEDS_CONTEXT`, 보고서 누락, 불명확한 결과는 `DONE`이 아닙니다.
- `DONE_WITH_CONCERNS`는 기존 판정 절차로 처리하며, 검증만 한 응답에는 새
  커밋을 요구하지 않습니다.

## 백엔드 해석

오케스트레이터는 로드된 스킬 루트에서 `scripts/resolve_backend.py`를
실행합니다. 이 명령은 네트워크를 쓰지 않고, 파일을 쓰지 않고, 워커를 띄우지
않습니다.

- 성공하면 stdout은 JSON 객체 하나와 LF입니다.
- 없는 백엔드는 종료 코드 0과 `available: false`입니다. 잘못된 인자일 때만
  0이 아닌 코드입니다. 종료 코드만 보고 다른 백엔드를 고르지 않습니다.

### 후보 실행 파일

- Grok 후보는 PATH의 `grok`뿐입니다.
- Cursor 후보는 `cursor-agent`, 그다음 신원이 Cursor Agent CLI인 `cursor`입니다.
  Grok Build 신원을 Cursor로 채택하지 않습니다.
- `agent`는 Grok 후보도 Cursor 후보도 아닙니다.

### JSON 출력

키는 `backend`, `available`, `executable`, `identity`, `argv_prefix`, `reason`,
`launch`, `model_ids`입니다.

- `launch`는 `cwd_flag`, `prompt_flag`, `effort_flag`, `output_format`을
  담습니다. `available`이 false면 `launch`는 `null`이고 `model_ids`는 빈
  목록입니다.
- `output_format`은 해당 호스트의 resolver가 돌려준 값을 그대로 쓰며 백엔드별로
  하드코딩하지 않습니다.
- 사용 가능한 양쪽의 `model_ids`는 Grok 4.7만 담습니다. Grok Build는 목록에
  찍힌 `grok-4.7`만 돌려주고, Cursor는 버전 세그먼트가 `4.7`이고 `-fast`로
  끝나지 않는 Grok id만 돌려줍니다. `4.6`, `4.5`, `-fast` 변형은 목록에 있어도
  빠집니다.

없는 백엔드의 `reason`은 `not_found`, `identity_mismatch`, `missing_flags`,
`no_model_list`, `model_list_unreadable`, `no_grok_model`, `no_grok_4_7` 중
하나입니다. 모델 목록에 관한 넷은 서로 다른 사실을 말합니다.

| `reason` | 뜻 |
| --- | --- |
| `no_model_list` | 목록을 아예 얻지 못했습니다. |
| `model_list_unreadable` | 목록은 왔으나 id를 하나도 읽지 못했습니다. |
| `no_grok_model` | id를 읽었으나 그중 Grok이 없습니다. |
| `no_grok_4_7` | Grok id는 읽었으나 4.7이 없습니다. `-fast`만 남아도 이것입니다. |

앞의 둘은 모델이 없다고 주장하지 않습니다. `no_grok_4_7`일 때 4.6이나 4.5로
바꾸지 않습니다.

### 필수 플래그

Grok resolver는 `--sandbox`, `--rules`, `--disable-web-search`를 포함한 필수 실행
플래그를 확인하고, 기본 `argv_prefix`에 `--sandbox workspace`를 넣습니다. 도구
제한 플래그는 「Grok 워커 도구와 MCP 초기화」에 있습니다.

Cursor는 다음을 요구합니다.

- `prompt_flag`는 `null`로 고정되어 `build_argv`가 프롬프트를 이름 없는 위치
  인자로 덧붙입니다. 그래서 Usage 줄에 `[prompt]` 또는 `[prompt...]`가 있어야
  통과합니다.
- `2.0.0`의 비호환 변경은 Cursor 필수 기능입니다. Cursor resolver는 headless
  print(`--print` 또는 `-p`), `--trust`, `--auto-review`, `--sandbox`, 확인된
  `stream-json` 출력 형식, 그리고 모델 목록 명령이 실제로 성공해 돌려준 Grok 4.7
  id를 모두 요구합니다. `--auto-review`, `--sandbox`, 구조화 출력 형식을
  선언하지 않는 기존 Cursor CLI는 `available: false`와 `reason: missing_flags`입니다.
- 예전의 `--force`/`--yolo` 일괄 승인 대체 경로는 없어졌고 플래그로 되살릴 수
  없습니다. 해결된 prefix가 이미 headless·승인 플래그를 담으므로 두 번째
  `--sandbox`나 두 번째 승인 플래그를 덧붙이지 않습니다.

`--resume`은 Cursor와 Grok 모두 값을 받는 선언(`<id>` 또는 `[id]`)이어야
합니다. `build_argv`가 위치 인자 프롬프트 바로 앞에 `--resume <id>`를 넣으므로,
값을 받지 않는 `--resume`은 프롬프트를 다른 자리로 밀어냅니다. 값을 받는
`--resume`이나 Cursor의 위치 인자 프롬프트 선언 중 하나라도 없으면
`missing_flags`입니다.

## Grok 워커 도구와 MCP 초기화

- Grok resolver는 값을 받는 `--disallowed-tools`와 `--deny` 선언을 요구합니다.
  하나라도 없으면 `missing_flags`이며 더 약한 실행으로 대체하지 않습니다.
- `--disallowed-tools search_tool,use_tool`로 MCP 호출용 도구를 빼고,
  `--deny MCPTool(*)`를 함께 넘깁니다.
- 러너는 Grok 자식 프로세스에만 `GROK_CURSOR_MCPS_ENABLED=0`,
  `GROK_CLAUDE_MCPS_ENABLED=0`을 설정합니다. 새 호출과 재개 모두 적용하며,
  부모 환경, 전역 설정, 인증·세션 위치는 바꾸지 않습니다. Cursor에는 적용하지
  않습니다.
- 지원 OS는 macOS뿐이며 Windows 명령 전송은 제품 계약이 아닙니다.

이 변경은 Cursor/Claude에서 가져오는 MCP 초기화와 특정 도구 사용 경계만
다룹니다. 한계는 다음과 같습니다.

- `Agent`/`task` 제외는 명령 결과 조회·종료 도구까지 없애므로 쓰지 않습니다.
- 하위 에이전트는 기존 `--no-subagents`와 워커 지침으로 제한하지만 도구 제거를
  보장하지 않습니다.
- Grok 자체·플러그인 MCP 초기화, 셸을 통한 호출, 파일 접근을 모두 막는 격리가
  아닙니다.
- init/inspect에 보이는 서버 목록은 실제 연결이나 도구 호출의 증거가 아니므로
  stderr와 실제 도구 기록을 확인합니다. 다른 CLI 시작 경고는 숨기지 않습니다.

## 실행 helper와 시도 증거

### 과제 추출

오케스트레이터는 계획에서 과제 구간을 뽑을 때
`scripts/extract_task.py <plan-file> --heading "<# 없는 제목 전체>" --global-constraints --output <file>`을
씁니다.

- `--heading`은 `#` 표시를 뺀 제목 전체입니다. 과제 제목을 뽑을 때
  `--global-constraints`는 필수입니다.
- exit 0은 성공, 2는 파일·인자 오류, 3은 제목 부재·중복 또는 빈 본문입니다.
  `Global Constraints`/`Global constraints` 절이 없거나, 둘 이상이거나, 본문이
  비어 있어도 exit 3이며, 그때는 워커를 보내지 않습니다.
- 이미 있는 출력 파일은 덮어쓰지 않으므로 추출마다 새 경로를 씁니다.
- 계획 제목이 없는 브리프(수정 라운드, 이어가기)는
  `extract_task.py <plan-file> --heading "Global Constraints" --output <file>`로
  제약 절만 뽑아 그 출력으로 시작합니다. 계획이 다른 계획의 제약을 가리키면 그
  계획에서 뽑습니다. 손으로 옮기거나 `/tmp` 캐시를 쓰지 않습니다.

### 워커 실행

- 워커 실행은 `scripts/run_worker.py run` 하나로만 합니다. 공급자 명령을 직접
  조합하거나 실행마다 새 실행 스크립트를 만들지 않습니다.
- `--attempt-dir`는 Superpowers `sdd-workspace`가 만든 계획 디렉터리 아래의 새
  폴더입니다. 그 계획 디렉터리는 작업 트리의 `.superpowers/sdd/<계획이름>/`에
  있습니다. 공용으로 쓰는 평평한 `.superpowers/` 이름은 쓰지 않습니다. 시도 부모
  폴더는 첫 실행 전에 만듭니다.
- 러너는 시도 폴더에 `brief.md`, `dispatch.md`, `worker.jsonl`, `stderr.log`,
  `run.json`, `report.md` 여섯 파일을 남깁니다. `report.md`는 워커가 직접 쓰고
  러너는 쓰지 않습니다.
- 러너는 `prepare`·`cleanup`을 호출하지 않습니다. prepare → run → 종료 확인 →
  cleanup 순서는 오케스트레이터가 지킵니다.
- 자동 재시도는 어느 helper에도 없습니다.
- `run`·`status` 출력을 exit를 가리는 파이프로 넘기지 않습니다.
- `--model`은 양쪽 모두 필수이며 그 백엔드의 `model_ids` 안에 있어야 합니다.
  Grok은 `--sandbox-profile`과 `--model grok-4.7`을 요구합니다. Cursor는
  resolver `model_ids`에서 고른 Grok 4.7 `--model`을 요구하고
  `--sandbox-profile`을 거부합니다.

### 시도 조회

시도 조회는 읽기 전용인 `scripts/run_worker.py status`만 씁니다. 살아 있는지,
세션 ID, 어떤 파일을 읽었는지는 이 명령으로만 보고, 로그 전체를 세션에 붙이지
않습니다.

기본 응답은 메타데이터, 로그 크기, `report.md` 존재 여부, `pid_alive`, `stale`,
`session_id_in_log`, `tools`입니다. 로그 본문은 없습니다. 역할 준수(계획을
읽었는지, `DONE`인지)는 오케스트레이터가 판정합니다. 본문 창은 `--stream`을 줘야
나오며 기본 2048바이트, 최대 8192바이트이고, JSON 응답 전체는 64 KiB까지입니다.

- `session_id`는 워커 스트림이 처음 적어 준 ID입니다. `state`가 `running`이어도
  스트림에 나오는 즉시 `run.json`에 복사하고, 한 번 적으면 바꾸지 않습니다.
  `status`는 그 기록만 보여 줍니다. 기록이 없는데 로그에 ID가 있다고 해서 만들지
  않습니다. 스트림이 아무 ID도 주지 않으면 `null`입니다.
- `pid_alive`는 기록된 pid가 지금 살아 있는지입니다. `run.json`에는 넣지
  않습니다. `state`가 `running`인데 `pid_alive`가 false면 기록만 남은 것입니다.
  `status`는 그 기록을 `interrupted`로 고치지 않습니다.
- `stale`은 그 판정 자체입니다. `state`가 `running`이고 `pid_alive`가 false일
  때만 true입니다. 종료 상태이거나 기록이 없으면 false이며, `run.json`에는 넣지
  않습니다.
- `session_id_in_log`는 기록에 ID가 없을 때만 로그가 보고한 ID를 함께 보여
  줍니다. 기록에 ID가 있으면 `null`입니다. `session_id`가 재개에 쓰는 유일한
  값이라는 규칙은 그대로이고, 두 값이 엇갈릴 일이 없습니다. 러너가 기록하기 전에
  죽어도 워커 세션을 재개할 수 있게 하려는 것이며, `run.json`에 쓰지 않습니다.
- `tools`는 로그에서 복사한 짧은 목록입니다. `reads`(경로), `searches`(검색어·경로),
  `shells`(종료 코드·명령), `truncated`로 이루어집니다. Cursor `tool_call`
  이벤트와 Grok `tool_use` 항목을 읽습니다.
  - Grok `list_dir`은 `pattern`이 null인 검색입니다.
  - 정수 종료 코드가 돌아오지 않은 Grok 셸(백그라운드 작업, 먼저 멈춘 워커)의
    `exit_code`는 null입니다.
  - Grok은 셸 호출을 그 호출이 돌아오거나 백그라운드로 옮겨진 뒤에야 적으므로,
    포그라운드에서 아직 실행 중인 Grok 셸은 아직 인덱스에 없습니다. 없다고
    "명령이 실행되지 않았다"로 읽지 않습니다.
  - 파일 내용, stdout, stderr, thinking은 없습니다.
  - 한도는 읽기 64, 검색 32, 셸 32, 명령 200자입니다. 알 수 없는 도구 모양은 빈
    목록이며 오류가 아닙니다. JSON이 아니거나 너무 깊은 줄은 건너뜁니다.

### 시도 끝내기와 멈추기

시도가 끝났다는 판단은 `state`가 `running`이 아니고 `pid_alive`가 false인
것입니다. 이전 시도의 `pid_alive`가 true인 동안 새 시도를 띄우지 않습니다.

`run.json.pid`와 `pid_alive`는 워커의 것입니다. 멈출 때는 러너에 SIGTERM을
보냅니다. 러너는 호스트 작업의 pid이거나, `ps -o ppid= -p <pid>`로 얻는 기록된
pid의 부모입니다. `run.json.pid` 자체나 `pkill -f`에는 보내지 않습니다. 그 부모가
pid 1이면 러너는 이미 없고 워커는 고아입니다. 그때만 `run.json.pid`의 워커를
직접 멈춥니다(SIGTERM, 남아 있으면 SIGKILL).

### `run.json`과 종료 코드

`run.json`은 프로세스 사실만 담습니다. `schema_version` 2와 함께 `backend`,
`identity`, `model`, `worktree`, `attempt_dir`, `brief_sha256`, `resume_id`,
`session_id`, `requested_effort`, `configured_effort`, `skill_version`, `state`,
`pid`, `exit_code`, `started_at`, `ended_at`, `error`를 기록합니다.

- `skill_version`은 설치된 스킬의 `release.toml` 버전이며 시작 때 한 번만
  적습니다. 없거나 읽을 수 없으면 시도 디렉터리를 만들기 전에 실행을 거부합니다.
  이 필드가 없는 예전 schema 2 기록은 그대로 읽습니다.
- `state`는 `starting`, `running`, `exited`, `launch_failed`, `timed_out`,
  `interrupted` 중 하나이며 과제 상태가 아닙니다. 프로세스 exit 0은 깨끗한
  `DONE`이 아닙니다.

래퍼 exit는 워커의 exit를 따릅니다.

- POSIX 시그널로 끝나면 `128 + signal`을 반환하고, `run.json.exit_code`에는
  실제 음수 returncode가 남습니다.
- 실행 실패는 2, 처리된 중단은 130, 시간 제한으로 끝나면 124입니다. exit 2는
  실행 실패와 워커가 정말 2로 끝난 경우가 겹치므로 `run.json.state`로
  구분합니다.
- 시도 디렉터리가 없거나 `run.json` 없이 있으면 시도가 만들어지기 전에 거절된
  것이고, stderr의 `BLOCKED:` 줄이 그 이유입니다.

### 신호

신호는 두 갈래입니다.

- 러너(래퍼)에 SIGTERM 또는 Ctrl-C가 오면 러너는 먼저 `interrupted`를
  기록하고, 타임아웃과 같은 방식(SIGTERM, 10초, SIGKILL)으로 워커 프로세스
  하나를 끝낸 뒤 회수한 `exit_code`를 다시 기록하고 130으로 끝납니다. 워커가
  끝났는지 확인하지 못하면 그 `exit_code`는 `null`이므로 정리 전에 `pid_alive`를
  확인합니다. 그 대기 중에 들어온 두 번째 인터럽트, 그리고 타임아웃이 워커를
  끝내는 대기 중에 들어온 인터럽트는 곧바로 SIGKILL로 넘어갑니다. `error`는
  `the runner was interrupted (SIGTERM or Ctrl-C)`이며 신호를 보낸 주체를 적지
  않습니다.
- 워커에 SIGTERM이 가면 `exited`(타임아웃이 보낸 것이면 `timed_out`)와 음수
  `exit_code`입니다. SIGKILL은 기록을 남기지 못하므로 `pid_alive`로 봅니다.

신호는 워커 프로세스 하나에만 보냅니다. 워커는 터미널 인터럽트가 닿도록
오케스트레이터와 같은 프로세스 그룹에 남으므로, 워커가 시작한 자식 프로세스는
쫓아가지 않습니다. 인터럽트 경로와 타임아웃 경로의 한계가 같으며, 프로세스
트리를 정리했다고 적지 않습니다.

- 워커가 시작한 프로세스(예: 백그라운드 셸, 빌드 데몬, 워커가 끝난 뒤 pid 1로
  입양된 채 남은 것이 관측된 Cursor `worker-server`)는 워커보다 오래 남을 수
  있으니 정리 전에 pid로 확인하고 끝냅니다.
- 워커 프로세스를 띄우는 중에 들어온 인터럽트는 `run.json`을 pid 없는
  `starting`으로 남길 수 있습니다. 그때는 다음 시도를 띄우기 전에 호스트에 남은
  워커가 있는지 확인합니다.

### 타임아웃

- `--idle-timeout <초>`는 `worker.jsonl`과 `stderr.log`가 둘 다 그 시간 동안
  자라지 않으면 시도를 끝냅니다. 새 시도든 재개든 실행 직후부터 끝날 때까지
  적용됩니다. 기본값은 900이고 `--idle-timeout 0`은 끕니다.
- `--timeout <초>`는 한 시도의 실제 경과 시간을 제한하는 선택 항목입니다.
  기본값은 0이고 `--timeout 0`은 제한 없이 기다립니다.

둘 중 하나에 걸리면 러너는 워커에 SIGTERM을 보내고 10초를 기다린 뒤 그래도 살아
있으면 kill한 다음, `state`를 `timed_out`으로 두고 실제 `exit_code`를
기록합니다. session ID는 이미 복사한 첫 값을 유지하고, 아직 null이면 한 번만 더
스캔합니다. 그 뒤 124로 끝냅니다.

`error` 문구는 다음과 같습니다. 둘 다 지났으면 경과 시간 제한이 먼저입니다.

- 유휴 타임아웃: `the worker wrote no output for <N> seconds`. `<N>`은
  `--idle-timeout` 값을 평범한 숫자로 쓴 것입니다(`900`, `0.5`; 기본
  `the worker wrote no output for 900 seconds`).
- 경과 시간 제한: `the attempt exceeded its timeout`.

유휴 타임아웃이 나면 작업 트리의 부분 변경을 확인하고, 그 세션을 재개하거나
제한을 올려 다시 돌리지 않습니다. 대신 이전 `report.md`와 이미 만든 커밋을 적은
이어가기 브리프로 새 워커를 보냅니다.

Grok은 오래 걸리는 명령을 기다리는 동안 그 명령이 전경이든 백그라운드로 넘긴
것이든 스트림에 아무것도 쓰지 않으므로, 그 기다림 내내 조용합니다. 백그라운드로
돌려도 시도가 유휴 창을 넘기지 못합니다. 브리프에 유휴 시간보다 오래 걸릴 명령이
있으면 그 시도를 띄우기 전에 `--idle-timeout`을 그 명령의 예상 시간보다 크게
올립니다. 그 명령을 적은 새 이어가기 시도도 여기에 포함됩니다.

### 강도 기록

요청 강도와 설정 강도는 따로 기록합니다. Cursor는 강도를 플래그가 아니라 모델
ID에 담으므로, 러너는 선언된 강도가 `--effort`와 어긋나는 모델을 거부하고
`configured_effort`에는 ID에서 읽은 강도를 적습니다. ID가 강도를 선언하지 않으면
`null`로 남고 적용된 강도는 `unknown`입니다. 어느 쪽도 모델이 실제로 적용한
강도를 증명하지 않으므로 요청값을 적용값으로 적지 않습니다.

## 현재 상태

한 실행의 현재 상태는 해당 계획의 Superpowers SDD 작업 기록 한 곳에만 둡니다.

- 작업 기록 첫 줄 바로 아래에 `<!-- sddx:current:start -->`와
  `<!-- sddx:current:end -->`로 감싼 블록 하나를 두고, 갱신할 때마다 그 내용만
  교체합니다. 블록 아래의 완료 줄과 수정 라운드 이력은 그대로 둡니다.
- 블록의 필드는 `skills/sddx/references/current-state.md`가 소유합니다.
- 블록은 보내기 직전, 과제 완료, 수정 라운드의 시작·종료, 실행을 바꾸는 판정,
  사용자의 범위 변경 때마다 다시 씁니다.
- 모든 필드는 지금의 실행을 서술합니다. 디스크의 증거(시도 디렉터리, 블록 아래
  리뷰 줄, Git HEAD)와 어긋난 필드는 결함이며 다음 보내기보다 먼저 고칩니다.
- 이력은 블록 아래에 두고 블록 안에 쌓지 않습니다. 낡은 값은 덧붙이지 않고
  교체합니다.
- `controller-current-state.md`, `controller-recovery.md` 같은 별도 상태 파일을
  만들지 않습니다. `run.json`은 한 시도의 프로세스 기록이고 작업 기록은 실행의
  기록이며, 둘을 양방향으로 동기화하지 않습니다.

공유 제품 소스를 바꿔도 진행 중인 실행은 자동으로 전환되거나 다시 시작되지
않습니다. 변경은 새 실행부터 적용하고, 기존 실행은 작업 기록과 프로세스를 확인한
뒤 명시적으로 재개합니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- 호스트 또는 백엔드 정체: `products.toml`, 이 계약, 제품 README, 공개
  호환성 안내, `tests/products/sddx/`
- 활성화·백엔드 선택·하드 게이트: `skills/sddx/SKILL.md`,
  `skills/sddx/references/dispatch.md`,
  `skills/sddx/references/worker-prompt.md`,
  `tests/products/sddx/cases.json`, `tests/products/sddx/test_contract.py`,
  `scripts/lib/product_contract.py`, `tests/repository/test_repository.py`
- `resolve_backend.py` 신원·플래그 규칙: `skills/sddx/scripts/resolve_backend.py`,
  `tests/products/sddx/test_resolve_backend.py`
- 과제 추출 규칙: `skills/sddx/scripts/extract_task.py`,
  `tests/products/sddx/test_extract_task.py`
- 실행·조회 규칙: `skills/sddx/scripts/run_worker.py`,
  `skills/sddx/references/dispatch.md`,
  `tests/products/sddx/test_run_worker.py`,
  `tests/products/sddx/test_worker_status.py`
- 현재 상태 블록: `skills/sddx/references/current-state.md`,
  `skills/sddx/SKILL.md`
- 버전과 설치 파일: `skills/sddx/release.toml`, `SKILL.md`, `CHANGELOG.md`,
  `skills/sddx/.claude-plugin/plugin.json`
