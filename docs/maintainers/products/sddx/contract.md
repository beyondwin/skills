# sddx 계약

이 문서는 SDDx가 무엇을 소유하고 어떻게 켜지는지를 적습니다.

- 호스트: 스킬을 실행하는 프로그램. 지금은 Claude Code와 Codex뿐입니다.
- 워커: 구현만 맡는 외부 CLI. Cursor 또는 Grok입니다.
- 오케스트레이터: `/sddx` 또는 `$sddx`를 받은 그 세션입니다.

## 제품 정체

제품 ID, 스킬 `name`, 디렉터리 이름은 `sddx`입니다. 표시 이름은 `SDDx`입니다.
슬래시 호출은 Claude Code `/sddx`, Codex `$sddx`입니다.

지원 호스트는 `claude-code`와 `codex`뿐입니다. Cursor CLI와 Grok CLI는
구현 worker이지 호스트가 아닙니다. `cursor`와 `grok`을 `supported_hosts`에
넣지 않습니다.

Superpowers SDD는 worktree, ledger, `sdd-workspace`, review-package, 리뷰어
프롬프트, fix loop, whole-branch review를 소유합니다. 워크스페이스와 리포트
파일 이름을 소유합니다. `sddx`는 인자 해석, backend picker,
`resolve_backend.py`, implementer argv, worker 제약·실행 증거 확인, 리뷰
모델·effort 선택, 구간 추출(`extract_task.py`)을 소유합니다. SDD 본문을 이
스킬에 복사하지 않습니다.

## 하드 게이트

설치된 Superpowers `subagent-driven-development`의 흐름을 따르며 implementer
dispatch, 리뷰 모델·effort, worker 증거 확인에 SDDx 규칙을 우선합니다.
Superpowers 파일을 고치지 않습니다. 오케스트레이터
세션에서 구현하지 않습니다.

사용자 메시지에 `/sddx` 또는 `$sddx`가 있을 때만 활성화합니다. 슬래시/달러가
없는 외부 implementer 요청, native SDD, executing-plans(Native 포함),
writing-plans, pre-sdd-review로는 켜지 않습니다.

## 호출과 picker

인자는 `sddx <plan-file> [cursor|grok|c|g]`입니다. 계획 경로가 없거나
파일이 아니면 추측하지 말고 한 번 묻습니다. 한 호출은 계획 하나입니다.

backend 인자가 있으면 picker를 생략합니다. `c`는 `cursor`, `g`는 `grok`입니다.
인자가 없으면 이 계획에서 한 번만 고릅니다. Claude Code는 AskUserQuestion,
Codex는 번호 있는 선택지를 한 번 묻고 답을 기다립니다. task마다 backend를
다시 묻지 않습니다. 고른 값은 ledger에 `Backend: cursor|grok`로 적고 그
plan의 모든 task에 유지합니다.

사용 가능한 backend가 하나뿐이어도 그 사실과 빠진 backend `reason`을 보여
주고, argv가 없으면 확인을 받은 뒤에만 진행합니다. 하나뿐이라고 자동
선택하지 않습니다.

요청한 backend가 없으면 다른 쪽으로 바꾸지 않고 멈춥니다. 둘 다 없으면
`BLOCKED`입니다.

## 리뷰어와 effort

task reviewer, scoped re-reviewer, 최종 리뷰어는 호스트 네이티브입니다.
Claude Code는 Task, Codex는 `spawn_agent`입니다. 구현 worker만 외부
프로세스입니다.

모든 task 리뷰·재리뷰·최종 리뷰는 dispatch 시점의 오케스트레이터 모델을
따릅니다. 일반 SDD의 저비용 모델 선택이나 최종 최상위 모델 선택보다 이 규칙이
우선합니다. 호스트가 지원하면 모델을 상속하고, 명시해야 하면 확인된 동일 모델 ID를
사용합니다. 특정 모델 계열로 고정하거나 리뷰만 다른 모델로 내리지 않습니다.
모델 ID를 확인할 수 없으면 상속 사실과 ID 미확인을 기록하며 추측하지 않습니다.

네이티브 리뷰어 호스트에 닿지 못하면(한도 소진, spawn 불가) 리뷰는 조용히
옮겨 가지 않습니다. 순서는 ① 막힌 조건이 풀릴 때까지 기다렸다 네이티브로 재파견,
② 오케스트레이터 호스트가 제공하는 다른 네이티브 경로, ③ 멈추고 사용자에게
묻기입니다. 리뷰를 네이티브 밖으로 옮기는 근거는 사용자의 답뿐이며, 그때도
구현자와 같은 모델 계열은 마지막 선택입니다. 자기 작업을 자기가 검토하게 되면
이 절이 지키려는 독립성이 사라집니다. 바뀐 호스트·모델·사유는 current-state
블록과 해당 리뷰 줄마다 남깁니다.

리뷰 effort는 세션 effort와 별도로 지정합니다. Claude Code에서 High는 SDD가 쓰던
방식 그대로 `model` 인자 없이 dispatch하는 것이고, XHigh는 `model` 인자 없이
`subagent_type`을 `sddx:sddx-reviewer-xhigh`로 지정하는 것입니다. 리뷰어에 `model`
오버라이드를 넘기지 않습니다.

XHigh trigger는 lock·순서·공유 상태 변경, auth·권한·secret·sandbox 경계 변경,
round 4–5 재리뷰, 반복해서 놓친 결함입니다. 판단 근거는 review-package stat, task
brief, 변경 파일 경로, ledger이며 diff 본문을 읽어 정하지 않습니다. 파일 수, 줄 수,
구현 난이도, 짧은 diff, 최종 리뷰라는 사실은 trigger가 아닙니다. 재리뷰는 원래
결함의 위험도를 유지합니다.

세션 effort가 이미 XHigh 이상이면 더 올리지 않고, 세션을 낮추지도 않습니다.

ledger에는 모든 리뷰 dispatch를 적습니다. High는 한 줄이고, XHigh는 trigger와
구체 경로를 함께 적습니다. 대지 못하면 High입니다.

정의는 `agents/sddx-reviewer-xhigh.md`입니다. `plugin.json`에 `agents` 키를
두지 않습니다. 기본 `agents/*.md` 스캔이 Claude Code 인벤토리와 Task 등록을
모두 채웁니다. Task 이름은 `sddx:sddx-reviewer-xhigh`입니다. 파일
frontmatter 이름만으로는 Task가 찾지 못합니다. 중첩 경로나 `plugin.json`
`agents` 필드는 `plugin details`가 Agents (0)을 보고하게 합니다. 설치 링크는
두 개 그대로이며 새 설치 단계를 추가하지 않습니다. 정의가 없으면 — Codex에는 항상 없고, Claude Code에서도 로딩에
실패하면 없습니다 — 요청 effort를 지정할 수 없다고 보고한 뒤 기본 dispatch로
진행합니다. 다른 모델이나 effort로 대체하지 않고, 정의를 새로 만들지도 않습니다.
정의 부재로 실행을 BLOCKED로 세우지 않습니다.

한 워커가 여러 계획 과제를 묶지 않습니다. 계획 제목 하나가 워커 하나, 리뷰
패키지 구간 하나입니다. 같은 모양의 한 줄 수정이어도 묶지 않습니다.
중첩 native SDD로 내려가지 않습니다. 한 단계 아래 서브에이전트에
`subagent-driven-development`를 통째로 맡기지 않습니다.
계획이 이름 붙이지 않은 일은 보내기 전에 한 번 묻습니다. “끝까지 돌려”는
계획에 있는 과제만 덮습니다.

오케스트레이터는 `/sddx` 또는 `$sddx`를 받은 세션의 모델·effort입니다. 더
싼 모델, 최종 최상위 모델, 구현 워커와 같은 모델 계열로 바꾸지 않습니다.
픽커 선택지는 Grok CLI와 Cursor Agent (Grok)입니다. 둘 다 Grok 4.7만
씁니다. Grok에는 resolver가 확인한 `grok-4.7`을 `--model`로 넘기고, effort는
`--reasoning-effort` 또는 `--effort`로 넘깁니다. `grok-4.7-build-fast`,
`grok-4.6`, `grok-4.5`는 넘기지 않습니다. Cursor에는 버전 세그먼트가 `4.7`이고 `-fast`로 끝나지 않는
확인된 id만 넘깁니다. `-fast` 변형은 지원하지 않습니다. 구현 CLI는 이 계획에서 한 번만 고릅니다.
구현 effort는 과제 난이도 표로 과제마다 High 또는 XHigh입니다. 세션
effort를 구현에 복사하지 않습니다. 리뷰어 XHigh가 구현 XHigh를 강제하지
않습니다. 요구가 분명하고 로컬·기계적인 변경, 단순한 통합은 High입니다.
동시성·race·잠금·순서·공유 상태, auth·권한·secret·sandbox 경계, 여러
하위계가 얽힌 부작용, 이 과제에서 High 리뷰가 이미 실패한 경우는
XHigh입니다. 설계 모호함은 XHigh가 아니라 오케스트레이터 ruling입니다.
이유를 대지 못하면 High입니다. effort가 오르면 새 워커입니다. worker가
`NEEDS_CONTEXT` 또는 `BLOCKED`를 반환하면 ruling한 뒤 같은 backend로 다시
보냅니다.

새 task는 새 worker입니다. fix 라운드 1–3은 요청 effort가 같을 때만 같은
worker session을 resume합니다. 라운드 4–5는 fresh worker와 XHigh입니다.
worker에 `--worktree`를 넘기지 않습니다. cwd는 현재 Superpowers worktree입니다.

## Worker 부작용과 비밀

호스트 자격 증명이나 환경 값을 worker prompt나 `--prompt-file`에 넣지
않습니다. worker가 push, publish, 공유 브랜치 갱신처럼 호스트 밖 부작용을
필요로 하면 멈추고 `BLOCKED`입니다. 그 결과를 리뷰 통과 DONE으로 쓰지
않습니다.

## Grok worktree 프로파일과 완료 판정

Grok implementer dispatch는 worker 실행 직전에 `prepare_grok_sandbox.py
prepare`를 호출하고, 반환된 작업용 프로파일로 resolver `argv_prefix`의 기존
`--sandbox` 값 하나를 교체합니다. worker prompt 전체를 `--rules`로 넘깁니다.
prepare가 실패하면 worker를 시작하지 않습니다.

worker와 worker가 실행한 작업이 종료된 뒤에는 성공과 실패 모두에서
`prepare_grok_sandbox.py cleanup`을 호출합니다. 새 task와 resume은 같은
준비·실행·종료·정리 순서를 씁니다. 정리 실패 시 다른 파일을 덮어쓰지 않고
남은 차이와 상태 기록 위치를 ledger에 남깁니다. 생성 설정과 복원 상태는 제품
산출물이나 커밋 대상이 아닙니다.

dispatch 전 컨트롤러는 `extract_task.py --global-constraints`로 과제를 뽑고,
필요한 조건과 task 참고자료를 완결합니다. 계획이 전체 실행에 대해 한 번만
적어 두는 제약은 그 플래그가 `Global Constraints` 절을 brief 앞에 붙입니다.
손으로 다시 복사하지 않습니다. worker는 계획을 읽을 수 없으므로 brief에
없는 제약은 worker에게 존재하지 않으며, 리뷰가 뒤늦게 worker가 피할 방법이 없던
결함으로 보고하게 됩니다. 전체 계획을 참고자료로 전달하지 않으며 새 호출과 resume 모두에 문서 경계를
직접 명시합니다. brief의 `Search paths:`에 구체적인 source/test 파일·디렉터리를
적고 worker는 명시된 파일부터 직접 읽습니다. 내용 검색이 필요하면 이 경로를 도구 인자로
지정하며, 파일 glob만으로 경로가 제한된다고 가정하지 않습니다. 검색 경로가 없으면
명시된 파일을 직접 읽거나 컨트롤러에 누락 경로를 요청합니다. 전체 workspace 내용
검색은 하지 않습니다. worker는 필요한 source/test를 읽을 수 있으나 전체 계획은
링크·shell·검색·Git 이력으로도 읽지 않습니다. 부족한 결정은 `NEEDS_CONTEXT`입니다.

`Search paths`는 내용 검색을 제한합니다. 현재 worktree 안의 파일명 목록 조회
(root 포함)와 해당 task에 필요한 저장소 ignore·빌드·테스트 설정 직접 읽기는
허용된 확인입니다. 이 행동만으로 scope deviation이나 별도 ruling을 요구하지
않습니다. 다른 이탈이 없으면 `Scope deviations: none`이 맞습니다. 이 허용은
전체 계획 본문·자격 증명·비밀정보 읽기를 포함하지 않습니다.

worker 보고에는 scope deviations 항목이 필수입니다. 시도/수행한 행동·대상·결과를
기록하며, 계획 원문을 다시 복사하지 않습니다. 이탈한 뒤 정정했어도 clean `DONE`이
아닙니다. 테스트 wrapper를 사용하면 전체 명령과 실제 테스트 exit를 구분합니다.

프로세스 exit 0만으로 task를 완료 처리하지 않습니다. worker report의 테스트
결과, task 변경 커밋, 실제 tool-call/results 기록, 네이티브 리뷰를 확인해야 합니다.
ledger의 역할 준수는 `PASS`, `FAIL`, `UNVERIFIED`로 적습니다. 읽기 시도와 실제
내용 반환을 구분하고 shell·검색 도구 결과도 확인합니다. 검색에 계획 일부 줄이
반환돼도 계획 내용 읽기에 해당합니다. 금지된 문서 읽기 성공은 테스트
성공과 무관하게 `FAIL`, 기록 누락·불완전은 `UNVERIFIED`이며 둘 다 clean `DONE`으로
승격하지 않습니다. 보고서와 다른 관측을 리뷰어에게 전달합니다. 이후 인정이나 정상
호출로 앞선 위반을 지우지 않습니다. 기존 ruling으로 필요한 조치를 판단합니다.
`BLOCKED`,
`NEEDS_CONTEXT`, 보고서 누락, 불명확한 결과는 `DONE`이 아닙니다.
`DONE_WITH_CONCERNS`는 기존 ruling 절차로 처리하며, 검증만 한 응답에는 새
커밋을 요구하지 않습니다.

## Backend 해석

컨트롤러는 로드된 스킬 루트에서 `scripts/resolve_backend.py`를 실행합니다.
네트워크를 쓰지 않고 worker를 띄우지 않습니다. 성공 시 stdout은 JSON 한
객체와 LF입니다. 없는 backend는 종료 코드 0과 `available: false`입니다.
잘못된 인자만 비0입니다. 종료 코드만으로 다른 backend를 고르지 않습니다.

Grok 후보는 PATH의 `grok`뿐입니다. `agent`는 Grok 후보가 아닙니다. Cursor
후보는 `cursor-agent`, 그다음 신원이 Cursor Agent CLI인 `cursor`입니다.
`agent`는 Cursor 후보가 아닙니다. Grok Build 신원을 Cursor로 채택하지
않습니다.

Grok resolver는 `--sandbox`, `--rules`, `--disable-web-search`를 포함한 필수
실행 플래그를 확인하고, 기본 `argv_prefix`에 `--sandbox workspace`를 넣습니다.
resolver 자체는 파일을 쓰거나 worker를 시작하지 않습니다.

JSON 객체의 키는 `backend`, `available`, `executable`, `identity`,
`argv_prefix`, `reason`, `launch`, `model_ids`입니다. `launch`는 `cwd_flag`,
`prompt_flag`, `effort_flag`, `output_format`을 담으며 `available`이 false면
`null`이고 `model_ids`는 빈 목록입니다. 사용 가능한 양쪽의 `model_ids`는
Grok 4.7만 담습니다. Grok Build는 목록에 찍힌 `grok-4.7`만 돌려주고,
Cursor는 버전 세그먼트가 `4.7`이고 `-fast`로 끝나지 않는 Grok id만
돌려줍니다. `4.6`, `4.5`, `-fast` 변형은 목록에 있어도 빠집니다. `-fast`만
남으면 `no_grok_4_7`입니다.
`output_format`은 해당 호스트의 resolver가 돌려준 값을 그대로 쓰며 backend별로
하드코딩하지 않습니다. 없는 backend의 `reason`은 `not_found`,
`identity_mismatch`, `missing_flags`, `no_model_list`, `model_list_unreadable`,
`no_grok_model`, `no_grok_4_7` 중 하나입니다. 모델 목록 관련 넷은 서로 다른
사실을 말합니다. `no_model_list`는 목록을 아예 얻지 못한 것,
`model_list_unreadable`은 목록은 왔으나 id를 하나도 읽지 못한 것,
`no_grok_model`은 id를 읽었고 그중 Grok이 없는 것, `no_grok_4_7`은 Grok id는
읽었으나 4.7이 없는 것입니다. 앞의 둘은 모델의 부재를 주장하지 않습니다.
`no_grok_4_7`일 때 4.6이나 4.5로 바꾸지 않습니다.

Cursor `prompt_flag`는 `null`로 고정돼 있어 `build_argv`가 prompt를 이름 없는
위치 인자로 덧붙입니다. 게이트는 Usage 줄에 `[prompt]` 또는 `[prompt...]`가
있어야 통과합니다. `--resume`은 Cursor와 Grok 모두 값을 받는 선언이어야
합니다(`<id>` 또는 `[id]`). `build_argv`가 위치 인자 prompt 바로 앞에
`--resume <id>`를 넣으므로, 값을 받지 않는 `--resume`은 prompt를 다른 자리로
밀어 냅니다. 둘 다 없으면 `missing_flags`입니다.

`2.0.0`의 비호환 변경은 Cursor 필수 기능입니다. Cursor resolver는 headless
print(`--print` 또는 `-p`), `--trust`, `--auto-review`, `--sandbox`, 확인된
`stream-json` 출력 형식, 그리고 모델 목록 명령이 실제로 성공해 돌려준 Grok 4.7
id를 모두 요구합니다. `--auto-review`, `--sandbox`, 구조화 출력 형식을 선언하지
않는 기존 Cursor CLI는 `available: false`와 `reason: missing_flags`입니다.
예전의 `--force`/`--yolo` 일괄 승인 대체 경로는 없어졌고 플래그로 되살릴 수
없습니다. 해결된 prefix가 이미 headless·승인 플래그를 담으므로 두 번째
`--sandbox`나 두 번째 승인 플래그를 덧붙이지 않습니다.

## Grok worker 도구와 MCP 초기화

Grok resolver는 값을 받는 `--disallowed-tools`와 `--deny` 선언을 요구합니다.
둘 중 하나라도 없으면 `missing_flags`이며 더 약한 실행으로 대체하지 않습니다.
`--disallowed-tools search_tool,use_tool`로 MCP 호출용 도구를 제외하고, `--deny MCPTool(*)`를 함께 전달합니다.

runner는 Grok 자식 프로세스에서만 `GROK_CURSOR_MCPS_ENABLED=0`,
`GROK_CLAUDE_MCPS_ENABLED=0`을 설정합니다. 신규·재개 호출 모두 적용하며
부모 환경, 전역 설정, 인증·세션 위치는 변경하지 않습니다. 지원 OS는 macOS뿐이며
Windows 명령 전송은 제품 계약이 아닙니다. Cursor에는 이 변경을 적용하지
않습니다.

이 변경은 Cursor/Claude에서 가져오는 MCP 초기화와 특정 도구 사용 경계를 다룹니다.
`Agent`/`task` 제외는 명령 결과 조회·종료 도구까지 제거하므로 사용하지 않습니다.
하위 에이전트는 기존 `--no-subagents`와 worker 지침으로 제한하지만 도구 제거를
보장하지 않습니다. Grok 자체·플러그인 MCP 초기화, shell을 통한 호출, 파일 접근을 모두 차단하는 격리는
아닙니다. init/inspect에 표시되는 서버 목록은 실제 연결이나 도구 호출의 증거가
아니므로 stderr와 실제 도구 기록을 확인합니다. 다른 CLI 시작 경고는 숨기지 않습니다.

## 실행 helper와 시도 증거

컨트롤러는 계획에서 task 구간을 뽑을 때
`scripts/extract_task.py <plan-file> --heading "<# 없는 제목 전체>" --global-constraints --output <file>`을
씁니다. `--heading`은 `#` 표시를 뺀 제목 전체입니다. `--global-constraints`는
필수입니다. exit 0은 성공, 2는 파일·인자 오류, 3은 제목 부재·중복 또는 빈
본문입니다. `Global Constraints`/`Global constraints` 절이 없거나, 둘
이상이거나, 본문이 비어 있으면 exit 3이며 그 경우 워커를 보내지 않습니다.
이미 있는 출력 파일은 덮어쓰지 않으므로 추출마다 새 경로를 씁니다.

worker 실행은 `scripts/run_worker.py run` 하나입니다. 공급자 명령을 직접
조합하거나 실행마다 새 실행 스크립트를 만들지 않습니다. `--attempt-dir`는
Superpowers `sdd-workspace`가 만든 계획 디렉터리 아래의 새 폴더입니다. 그
계획 디렉터리는 worktree `.superpowers/sdd/<계획이름>/` 안에 있습니다.
공용으로 쓰는 평평한 `.superpowers/` 이름은 쓰지 않습니다. 러너는 그곳에 `brief.md`,
`dispatch.md`, `worker.jsonl`, `stderr.log`, `run.json`, `report.md` 여섯 파일을
남깁니다. `report.md`는 worker가 직접 쓰고 러너는 쓰지 않습니다. 러너는
`prepare`·`cleanup`을 호출하지 않으며, prepare → run → 종료 확인 → cleanup 순서는
컨트롤러가 지킵니다. 자동 재시도는 어느 helper에도 없습니다.

`--sandbox-profile`은 Grok에만 필수이고 Cursor에서는 거부됩니다. `--model`은
양쪽 모두 필수이며 그 backend의 `model_ids` 안에 있어야 합니다. Grok은
`--sandbox-profile`과 `--model grok-4.7`을 요구합니다. Cursor는 resolver
`model_ids`에서 고른 Grok 4.7 `--model`을 요구하고 `--sandbox-profile`을
거부합니다.

시도 조회는 `scripts/run_worker.py status`뿐입니다. 읽기 전용입니다. 살아 있는지,
세션 ID, 어떤 파일을 읽었는지는 이 명령으로만 봅니다. 로그 전체를 세션에 붙이지
않습니다.

기본 응답은 메타데이터, 로그 크기, `report.md` 존재 여부, `pid_alive`, `stale`,
`session_id_in_log`, `tools`입니다.
로그 본문은 없습니다. 역할 준수(플랜을 읽었는지, DONE인지)는 컨트롤러가 판정합니다.
본문 창은 `--stream`이 있어야 하며 기본 2048바이트, 최대 8192바이트, JSON 응답
전체는 64 KiB입니다.

- `session_id`는 워커 스트림이 처음 적어 준 ID입니다. `state`가 `running`이어도
  스트림에 나오는 즉시 `run.json`에 복사하고, 한 번 적으면 바꾸지 않습니다.
  `status`는 그 기록만 보여 줍니다. 기록이 없는데 로그에 ID가 있다고 해서 만들지
  않습니다. 스트림이 아무 ID도 안 주면 `null`입니다.
- `pid_alive`는 기록된 pid가 지금 살아 있는지입니다. `run.json`에는 넣지 않습니다.
  `state`가 `running`인데 `pid_alive`가 false면 기록만 남은 겁니다. status는 그
  기록을 `interrupted`로 고치지 않습니다.
- `stale`은 그 판정 자체입니다. `state`가 `running`이고 `pid_alive`가 false일 때만
  true입니다. 종료 상태이거나 기록이 없으면 false이며, `run.json`에는 넣지 않습니다.
- `session_id_in_log`는 기록에 ID가 없을 때만 로그가 보고한 ID를 함께 보여 줍니다.
  기록에 ID가 있으면 `null`입니다 — `session_id`가 재개의 단일 값이라는 규칙은
  그대로이고, 두 값이 엇갈릴 일이 없습니다. 러너가 기록하기 전에 죽어도 워커 세션을
  재개할 수 있게 하려는 것이며, `run.json`에 쓰지 않습니다.
- `tools`는 로그에서 복사한 짧은 목록입니다. `reads`(경로), `searches`(검색어·경로),
  `shells`(종료 코드·명령), `truncated`. Cursor `tool_call` 이벤트와 Grok
  `tool_use` 항목을 읽습니다. Grok `list_dir`은 `pattern`이 null인 검색이고,
  정수 종료 코드가 돌아오지 않은 Grok 셸(백그라운드 작업, 먼저 멈춘 worker)의
  `exit_code`는 null입니다. 파일 내용, stdout, stderr, thinking은
  없습니다. 한도: 읽기 64, 검색 32, 셸 32, 명령 200자. 알 수 없는 도구 모양은
  빈 목록이며 오류가 아닙니다. JSON이 아니거나 너무 깊은 줄은 건너뜁니다.

`run.json`은 프로세스 사실만 담습니다. `schema_version` 2와 함께 `backend`,
`identity`, `model`, `worktree`, `attempt_dir`, `brief_sha256`, `resume_id`,
`session_id`, `requested_effort`, `configured_effort`, `skill_version`, `state`,
`pid`, `exit_code`, `started_at`, `ended_at`, `error`를 기록합니다.
`skill_version`은 설치된 스킬의 `release.toml` 버전이며 시작 때 한 번만 적습니다.
없거나 읽을 수 없으면 시도 디렉터리를 만들기 전에 실행을 거부합니다. 필드가 없는
예전 schema 2 기록은 그대로 읽습니다. `state`는 `starting`,
`running`, `exited`, `launch_failed`, `timed_out`, `interrupted` 중 하나이며 task
상태가 아닙니다. 프로세스 exit 0은 깨끗한 DONE이 아닙니다.

래퍼 exit는 worker의 exit를 따릅니다. POSIX 시그널은 `128 + signal`을 반환하고
`run.json.exit_code`에는 실제 음수 returncode가 남습니다. 실행 실패는 2, 처리된
중단은 130, 시간 제한으로 끝난 경우는 124입니다. exit 2는 실행 실패와 worker가
정말 2로 끝난 경우가 겹치므로 `run.json.state`로 구분합니다. 시도 디렉터리가
없거나 `run.json` 없이 있으면 시도가 만들어지기 전에 거절된 것이고 stderr의
`BLOCKED:` 줄이 그 이유입니다.

시그널은 두 갈래입니다. 러너(래퍼)에 SIGTERM 또는 Ctrl-C가 오면 러너는 먼저
`interrupted`를 기록하고, 타임아웃과 같은 방식(SIGTERM, 10초, SIGKILL)으로
worker 프로세스 하나를 끝낸 뒤 회수한 `exit_code`를 다시 기록하고 130으로
끝납니다. 그 대기 중 두 번째 인터럽트는 곧바로 SIGKILL로 넘어갑니다.
`error`는 `the runner was interrupted (SIGTERM or Ctrl-C)`이며 신호를 보낸
주체를 적지 않습니다. worker가 시작한 자식은 쫓지 않습니다. 워커에 SIGTERM이 가면
`exited`(타임아웃이 보낸 것이면 `timed_out`)와 음수 `exit_code`입니다. SIGKILL은
기록을 남기지 못하므로 `pid_alive`로 봅니다.

`--timeout <초>`는 한 시도의 실제 경과 시간을 제한합니다. 기본값은 7200이고
`--timeout 0`은 제한 없이 기다립니다. 제한에 걸리면 러너는 worker에 SIGTERM을
보내고 10초를 기다린 뒤 그래도 살아 있으면 kill한 다음, `state`를 `timed_out`으로
두고 실제 `exit_code`를 기록합니다. session ID는 이미 복사한 첫 값을 유지하고,
아직 null이면 한 번만 더 스캔합니다. 그 뒤 124로 끝냅니다.

새 시도든 재개든 시작 후 300초 동안 stdout이 0바이트이면 러너는 같은 방식으로
worker를 끝내고 `timed_out`, exit 124, `error` `the worker wrote no output within
300 seconds`를 기록합니다. `--timeout 0`이어도 적용되고 플래그는 없습니다.
`--timeout`이 더 짧으면 `--timeout`이 먼저입니다. 이 오류면 타임아웃을 올려 다시
돌리거나 그 세션을 재개하지 않고, 이어가기 브리프로 새 worker를 보냅니다.

신호는 worker 프로세스 하나에만 보냅니다. worker는 터미널 인터럽트가 닿도록
컨트롤러와 같은 프로세스 그룹에 남으므로, worker가 시작한 자식 프로세스는 쫓아가지
않습니다. 인터럽트 경로와 같은 한계이며 프로세스 트리를 정리했다고 적지 않습니다.

요청 effort와 설정 effort는 따로 기록합니다. Cursor는 effort를 플래그가 아니라
모델 ID에 담으므로, 러너는 선언된 effort가 `--effort`와 어긋나는 모델을 거부하고
`configured_effort`에는 ID에서 읽은 effort가 들어갑니다. ID가 effort를 선언하지
않으면 `null`로 남고 적용된 effort는 `unknown`입니다. 어느 쪽도 모델이 실제로
적용한 effort를 증명하지 않으므로 요청값을 적용값으로 적지 않습니다.

## 현재 상태

한 실행의 현재 상태는 해당 계획의 Superpowers SDD ledger 한 곳에만 둡니다.
ledger 첫 줄 바로 아래에 `<!-- sddx:current:start -->`와
`<!-- sddx:current:end -->`로 감싼 블록 하나를 두고 갱신할 때마다 그 내용만
교체합니다. 블록 아래의 완료 줄과 fix 라운드 이력은 그대로 둡니다. 블록의 필드는
`skills/sddx/references/current-state.md`가 소유합니다.
블록은 dispatch 직전, task 완료, fix 라운드의 개시·종료, 실행을 바꾸는 ruling,
사용자의 범위 변경 때마다 다시 씁니다. 모든 필드는 지금의 실행을 서술하며,
디스크의 증거(시도 디렉터리, 블록 아래 리뷰 줄, Git HEAD)와 어긋난 필드는 결함이고
다음 dispatch보다 먼저 고칩니다. 이력은 블록 아래에 두고 블록 안에 쌓지 않습니다 —
낡은 값은 덧붙이는 것이 아니라 교체합니다.
`controller-current-state.md`, `controller-recovery.md` 같은 별도 상태 파일을
만들지 않습니다. `run.json`은 한 시도의 프로세스 기록이고 ledger는 실행의
기록이며, 둘을 양방향으로 동기화하지 않습니다.

공유 제품 소스를 바꿔도 진행 중인 실행은 자동으로 전환되거나 다시 시작되지
않습니다. 변경은 새 실행부터 적용하고, 기존 실행은 ledger 기록과 프로세스를
확인한 뒤 명시적으로 재개합니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- 호스트 또는 backend 정체: `products.toml`, 이 계약, 제품 README, 공개
  호환성 안내, `tests/products/sddx/`
- 활성화·picker·하드 게이트: `skills/sddx/SKILL.md`,
  `skills/sddx/references/dispatch.md`,
  `skills/sddx/references/worker-prompt.md`,
  `tests/products/sddx/cases.json`, `tests/products/sddx/test_contract.py`,
  `scripts/lib/product_contract.py`, `tests/repository/test_repository.py`
- `resolve_backend.py` 신원·플래그 규칙: `skills/sddx/scripts/resolve_backend.py`,
  `tests/products/sddx/test_resolve_backend.py`
- task 추출 규칙: `skills/sddx/scripts/extract_task.py`,
  `tests/products/sddx/test_extract_task.py`
- 실행·조회 규칙: `skills/sddx/scripts/run_worker.py`,
  `skills/sddx/references/dispatch.md`,
  `tests/products/sddx/test_run_worker.py`,
  `tests/products/sddx/test_worker_status.py`
- 현재 상태 블록: `skills/sddx/references/current-state.md`,
  `skills/sddx/SKILL.md`
- 버전과 설치 파일: `skills/sddx/release.toml`, `SKILL.md`, `CHANGELOG.md`,
  `skills/sddx/.claude-plugin/plugin.json`
