# sddx 호환성

이 문서는 SDDx가 어느 프로그램에서 돌아가고, 구현은 어디에 넘기는지를 적습니다.
호스트는 스킬을 실행하는 프로그램이고, worker는 구현만 맡는 외부 CLI입니다.

현재 지원 호스트는 제품 목록의 `claude-code`, `codex`입니다. Cursor CLI와
Grok CLI는 구현 worker이지 호스트가 아닙니다. 지원 범위와 현재 측정 상태는
별개입니다. Claude.ai, Cowork,
Skills API 업로드, marketplace 게시, 클라우드 동기화는 지원하지 않습니다.

## 발견 경로

```text
skills/sddx/              저장소 원본
├─ ~/.agents/skills/sddx ─→ Codex
└─ ~/.claude/skills/sddx ─→ Claude Code
```

`~/.codex`와 `~/.grok`에 복사본을 만들지 마세요. Cursor와 Grok을
`supported_hosts`에 넣지 않습니다.

## 호출 구문

| 호스트 | 명시 호출 | 발견 경로 |
| --- | --- | --- |
| Codex | `$sddx` | `~/.agents/skills/sddx` |
| Claude Code | `/sddx` | `~/.claude/skills/sddx` |

`agents/openai.yaml`은 Codex 표시 메타데이터이며 선택적입니다. 런타임 필수
파일이 아닙니다.
`agents/claude-code/sddx-reviewer-xhigh.md`는 성격이 다릅니다. Claude Code 런타임
정의이고, skills-dir 플러그인 로딩을 통해 전달됩니다. 로딩은 이전 버전의 제품
파일로 한 번 확인했을 뿐이며 `2.0.0`에서는 다시 확인하지 않았습니다. `2.0.0`의
정의 로딩, 서브에이전트에 실제 적용된 effort, `disallowedTools`의 실제 차단 여부는
모두 `not_measured`입니다.

사용자 프로젝트의 `.claude/agents/`에 같은 이름의 정의가 있으면 그쪽이 우선합니다.
제품 접두사를 붙인 이름 외에 방어 수단이 없습니다.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill sddx`입니다. 이 명령은
패키지 정체, resolver 픽스처, sandbox 준비·복원을 검사합니다. 라이브 모델 품질과
지원 호스트 런타임 동등은 증명하지 않습니다.

## Grok linked worktree 경계

Grok linked worktree 실행은 Python 3.11+가 필요합니다. 임시 작업 프로파일은
`workspace`를 상속하고 현재 worktree의 실제 Git 디렉터리와 공용 Git
디렉터리에 쓰기 권한을 추가합니다. 이 권한은 worker가 커밋하는 데 필요하며,
worker가 저장소의 공유 Git 메타데이터를 쓸 수 있음을 뜻합니다. 준비 도구가
만든 설정과 복원 상태는 커밋하지 않고 worker 종료 뒤 정리합니다.

외부 스킬·전체 계획 읽기 제한은 worker prompt 지침입니다. Grok은 추가로
CLI에서 MCP 호출 도구를 제외하고 MCP 권한 거절 규칙을 전달합니다.
이는 모든 초기화나 shell·파일 접근을 막는 격리가 아니며 역할 이탈이 불가능하다는
보장도 아닙니다.

## 2.0.0 측정 상태

이 표는 `2.0.0` 설치 파일만 다루며 현재 상태입니다. 네 조합 모두 제품 소유자 승인
아래 실제 공급자를 호출했습니다. 측정 환경은 모두 macOS 26.6.2 arm64입니다.
Cursor는 `cursor-agent 2026.09.10-fd3934a`, 모델 `cursor-grok-4.6-high`입니다.
Grok은 `grok 1.0.30 (04b7ffed98c6)`으로 모델 인자를 받지 않습니다. Grok은 모델을
스스로 고르며 init 이벤트가 보고한 모델은 `grok-4.6`입니다.

시도는 MCP 도구 필터가 들어가기 전(`bfd1cda`까지)과 후로 나뉩니다. 보완 전은
Claude Code 호스트에서 Cursor 세 번·Grok 두 번, Codex 호스트에서 Cursor 두 번·
Grok 두 번입니다. 보완 후는 Claude Code 호스트에서 Cursor 두 번·Grok 두 번,
Codex 호스트에서 Grok 두 번과 Cursor 재개 한 번입니다. 각 줄은 자기가 어느 쪽을
관측했는지 밝히며, 관측한 조합의 결과를 나머지로 넓히지 않습니다.

| 오케스트레이터 호스트 | 구현 worker | `2.0.0` 실제 실행 | 근거 |
| --- | --- | --- | --- |
| Claude Code | Cursor CLI | `measured` | 보완 전 worker 시도 세 번, 보완 후 신규·재개 두 번이 각각 브리핑된 작업을 구현하고 브리프의 테스트를 실행하고 커밋한 뒤 `report.md`를 직접 씀. 보완 후 두 번은 같은 `session_id`를 보고했고, 읽어 본 report는 계약이 요구하는 항목(상태, 변경 파일, RED·GREEN exit 코드를 포함한 worker 검사, 커밋 SHA, 범위 이탈)을 담고 있었음 |
| Claude Code | Grok CLI | `measured` | `prepare_grok_sandbox.py prepare` → `run_worker.py run` → `--resume` → `cleanup` 한 바퀴를 보완 전 일반 체크아웃에서, 보완 후 linked worktree에서 각각 돌림. 네 시도 모두 구현·테스트·커밋·`report.md` 작성을 마쳤고, 각 바퀴의 두 시도는 같은 `session_id`를 보고했음. 읽어 본 report는 계약이 요구하는 항목을 담고 있었음 |
| Codex | Cursor CLI | `measured` | Codex 세션이 controller로 신규·재개 두 번을 실행해 구현·RED exit 1 → GREEN exit 0·worker 직접 커밋(`6c244d5`, `bffd2f9`)을 마쳤고, 보완 후 러너에서 재개 한 번을 더 실행함. 이 저장소 관리자가 직접 관측한 것이 아니라 Codex가 남긴 `trace-audit.json`과 attempt별 `run.json`을 읽어 확인한 기록이며 원본은 로컬 증거 디렉터리에만 있음 |
| Codex | Grok CLI | `measured` | 위와 같은 방식으로 신규·재개 두 번(`033cb04`, `85ade8f`), 보완 후 최종 필터로 신규·재개 두 번을 더 실행함. 마찬가지로 Codex가 남긴 기록을 읽어 확인함 |

항목별로도 측정한 것과 측정하지 않은 것을 나눠 적습니다. `measured` 줄은 각 줄이
밝힌 조합에서 관측한 사실이며 그 이상을 뜻하지 않습니다.

| 항목 | `2.0.0` 상태 | 근거 |
| --- | --- | --- |
| 실제 Cursor 승인 동작 | `measured` | resolver가 만든 argv(`--print --trust --auto-review --sandbox enabled`)로 파일 쓰기·테스트 실행·`git commit`을 포함한 도구 호출 22개가 stdin `DEVNULL`, 대화형 프롬프트 없이 실행됨. 스트림의 init 이벤트는 `permissionMode: "default"` |
| 모델 ID 수락과 `configured_effort` 기록 | `measured` | `--effort high`와 `--model cursor-grok-4.6-high` 요청에 init 이벤트가 표시 이름 `"model": "Cursor Grok 4.6 High"`로 그 모델 ID를 받아들였음을 알렸고, `run.json`의 `configured_effort` `high`는 러너가 같은 ID에서 읽어 적은 값. 공급자가 어떤 ID를 수락했는지의 관측이며 모델이 적용한 effort의 관측이 아님 |
| session ID 회수와 `--resume` | `measured` | Cursor와 Grok 양쪽에서, 실제 스트림에서 회수한 `session_id`를 `--resume`으로 돌려주자 같은 `session_id`를 보고하는 시도가 돌아왔고 worker가 작업을 이어감 |
| 실제 worker의 타임아웃 | `measured` | 실제 worker에 `--timeout 5`를 걸어 래퍼 exit 124, `state: timed_out`, `exit_code: 143`, `session_id` 기록을 확인했고 그 시도가 남긴 프로세스는 없음 |
| 시도 생성 전 거절 | `measured` | effort와 모델 ID의 모순, 그리고 `--timeout inf`가 각각 시도 디렉터리가 만들어지기 전에 exit 2와 `BLOCKED:` 줄로 거절됨 |
| 실제 Cursor OS 격리 | `not_measured` | `--sandbox enabled`는 선언 확인이며 실제 격리 범위를 측정하지 않음 |
| 모델이 실제 적용한 effort | `not_measured` | 요청·설정 effort만 기록하며 적용값을 확인할 경로가 없음. 이번 라이브 실행도 그 경로를 만들지 않았고, 모델 ID 수락 확인은 적용값의 증거가 아님 |
| Grok 스트림 형태 | `measured` | `streaming-messages-json` 스트림 두 개(19줄, 17줄)를 관측함. 두 스트림 모두 전 줄이 JSON object로 파싱되고 전 줄이 `session_id` 키를 가졌으며, 다른 철자의 세션 키는 없었음. 첫 줄은 둘 다 `system`/`init`이고 이는 같은 자리에서 관측한 Cursor 스트림의 첫 줄과 같은 철자 |
| Grok sandbox 프로파일 왕복 | `measured` | `prepare`가 `.grok/sandbox.toml`에 `sddx-worktree` 프로파일(`extends = "workspace"`)을 만들고 `cleanup`이 자기가 만든 `.grok`을 지움. 일반 체크아웃에서는 `read_write`가 빈 목록이었고, linked worktree에서는 실제 Git 디렉터리와 공용 Git 디렉터리 두 개가 들어갔음. 위 「Grok linked worktree 경계」가 말하는 쓰기 권한 부여 경로가 그 실행에서 동작했고, worker가 linked worktree 안에서 직접 커밋을 남겼음. 커밋에는 과제 파일만 들어갔고 증거·sandbox 파일은 커밋되지 않음 |
| Grok sandbox의 실제 격리 | `not_measured` | 프로파일이 만들어지고 인자로 전달된 것까지만 확인했으며 그 프로파일이 무엇을 실제로 막았는지는 측정하지 않음 |
| Grok의 실제 effort 인자 | `measured` | resolver가 고른 `--reasoning-effort high`가 실제로 명령줄에 실려 실행됐고 `run.json`의 `configured_effort`는 `high`. 명령줄에 실린 요청값의 관측이며 모델이 적용한 effort의 관측이 아님 |
| Grok MCP 호출 도구 제거 | `measured` | 보완 후 실행의 init 이벤트 도구 목록 23개에 `search_tool`과 `use_tool`이 없음. 신규와 재개 양쪽에서 확인했고, 도구 제거는 CLI가 한 것이므로 지침이 아니라 강제임 |
| Grok 하위 에이전트 경계의 강제 여부 | `not_measured` | 같은 init 이벤트는 `--no-subagents`를 넘긴 뒤에도 `spawn_subagent`를 도구 목록에 싣고, 호스트 skill 전부와 MCP 서버 세 개(`context7`, `x-docs`, `playwright-sandboxed`)를 connected로 보고함. `Agent`/`task` 그룹 제외는 명령 결과 조회·종료 도구까지 없애므로 채택하지 않았음. 관측한 시도에서 하위 에이전트 호출이 없었던 것은 모델이 지시를 따랐기 때문이며 CLI가 막았다는 증거는 아님 |
| MCP 서버 목록 표시 | `measured` | 도구 필터를 넣은 뒤에도 init 이벤트는 서버 세 개를 여전히 connected로 보고함. 이 목록은 실제 연결이나 호출의 증거가 아니며, 호출 도구가 사라졌다는 사실과 서로 모순되지 않음 |
| MCP discovery 환경 변수의 효과 | `not_measured` | runner는 Grok 자식에만 `GROK_CURSOR_MCPS_ENABLED=0`과 `GROK_CLAUDE_MCPS_ENABLED=0`을 설정함. 이 변수가 전달된다는 사실은 오프라인 검사로 확인했으나, 이 저장소에서 관측한 Grok 시도는 보완 전후 모두 stderr가 0바이트여서 효과를 가를 수 없었음. handshake 실패 4건에서 0건으로 줄었다는 관측은 Codex가 남긴 원인 분리 probe 기록이며 여기서 재현하지 않음. 변수 이름은 공급자 내부 규약이라 Grok이 이름을 바꾸면 오류 없이 조용히 무력해짐 |
| Grok 도구 필터 옵션 요구 | `measured` | resolver는 값을 받는 `--disallowed-tools`와 `--deny` 선언을 요구하고, 없으면 `missing_flags`로 실행을 거절함. 설치된 `grok 1.0.30`의 help는 `--deny <RULE>`과 `--disallowed-tools <TOOLS>`로 선언하며 실제 해석 결과 `available: true`. 이 판정은 그 help 표기에만 맞춰져 있어, 같은 옵션을 다른 표기로 적는 빌드는 실행 가능한데도 거절됨 |
| `read_session_id`의 대체 키 철자 | `not_measured` | 두 공급자 모두에서 `session_id`로 세션 ID를 회수했고 Grok 스트림에는 다른 철자가 없었음. 이 키를 먼저 보므로 `sessionId`·`chatId`·`chat_id` 분기는 실행된 적이 없음 |
| Claude Code agent 정의 로딩 | `not_measured` | `2.0.0` 파일로 `claude -p --agent sddx-reviewer-xhigh` 확인을 수행하지 않음 |
| Windows 합성 argv 전송 | `measured` | 저장소 `windows-latest`/`windows-portable` CI가 Win32 이미지와 전달 `.cmd` 셰임 언랩을 실행함. macOS에서 `skipUnless(os.name == "nt")`인 왕복은 skip이며 skip은 통과가 아님 |
| 실제 Windows Cursor/Grok CLI | `not_measured` | CI 픽스처는 합성 CLI이며 공급자 바이너리가 아님 |
| 새 세션 전환과 일반 역할 준수 | `not_measured` | 위에 센 시도 밖의 역할 준수와 세션 전환은 관측하지 않음. 관측한 시도에서는 worker가 브리프의 잘못된 검사 명령을 실행해 실패를 확인하고 그 사실을 보고서에 적은 뒤 유효한 방법으로 RED·GREEN을 다시 냈음 |

Windows 합성 argv 행은 저장소의 `windows-latest`/`windows-portable` CI에서 실제로
실행됩니다. `sddx-contract`는 `WINDOWS_EXCLUDED_STAGES`
(`scripts/lib/verification.py:14`)에 없습니다. macOS 로컬 검사를 Windows 증거로
쓰지 않습니다. 실제 Cursor/Grok CLI의 Windows 실행은 이 CI가 증명하지 않습니다.

## 알려진 플랫폼·증거 한계

Windows에서 npm 방식 `.cmd` 전달 셰임(`exe script %*`, npm cmd-shim의
`%_prog%` 형태 포함)은 대상 Win32 이미지로 풀어 CRT 따옴표 명령줄로 실행합니다.
`cmd.exe` 명령줄은 줄바꿈을 담을 수 없으므로, 전달 형태가 아닌 배치 파일은
launch failure로 기록됩니다. 의도한 선택이며, 대안은 이전 전송 방식의 조용한
인자 훼손이었습니다. native Win32 이미지와 언랩된 셰임은 그 제한을 받지
않습니다. CI worker 픽스처는 Win32 이미지와 전달 `.cmd` 둘 다를 쓰며, 전달
형태가 아닌 배치 경로는 우회하지 않습니다.

`_expandable_percent_name`은 자식 환경 매핑에 있는 이름과 `cmd.exe` 의사 변수
(`%CD%`, `%DATE%`, `%TIME%`, `%RANDOM%`, `%ERRORLEVEL%`, `%CMDEXTVERSION%`,
`%CMDCMDLINE%`, `%HIGHESTNUMANODENUMBER%`)를 거절합니다. 의사 변수는 실제 자식
환경 매핑에 없어도 `cmd.exe`가 치환합니다. 전달 셰임이 언랩되면 이 검사는
해당 실행에 적용되지 않고, 언랩되지 않은 `.cmd` 경로에만 남습니다.

Grok의 `--rules`는 시도 디렉터리에 보존되지 않습니다. 규칙 본문이 명령줄로만
전달되고 스펙이 시도 디렉터리를 정확히 여섯 파일로 고정하므로,
`skills/sddx/references/worker-prompt.md`를 고치면 과거 Grok 시도를 저장된 증거만으로
그대로 재현할 수 없습니다. 이는 여섯 파일 계약이 강제한 결과이지 누락이 아닙니다.

## 1.0.x 관측 기록

아래 관측은 모두 `1.0.x` 설치 파일의 기록이며 `2.0.0`의 증거가 아닙니다. 당시
`Codex × Grok CLI`는 1.0.3에서 실제 2회 호출, 10/8 tests, 파일명·설정 조회의 none
보고와 경로 지정 검색을 확인했습니다. 같은 시점의 `Codex × Cursor`와
`Claude Code × Cursor 또는 Grok`은 그때도 `not_measured`였습니다.

1.0.1 최초 fixture에서는 세 호출, 최종 14 tests, 역할 위반 미관측을 확인했습니다.
이후 독립된 두 fixture에서 각각 세 호출을 다시 측정했으며 최종 15/14 tests와
커밋·복원은 성공했지만, 새 세션의 전체 계획 읽기가 재현됐습니다. 기존 sandbox
설정의 바이트와 0640 권한도 후속 실제 호출마다 복원됐습니다. 이전 성공 표본을
현재의 전면 통과나 역할 준수 보장으로 해석하지 않습니다.

1.0.2는 brief 경계·보고·도구 기록 판정과 리뷰 모델 상속을 보완합니다.
리뷰어는 호스트 네이티브로 현재 오케스트레이터 모델을 따르고, High/XHigh를 따로
지정합니다. 호스트에서 해당 제어를 지원하지 않으면 한계를 보고합니다.
최종 문구의 새 세 호출은 15 tests와 직접 커밋·재개·복원을 통과했고 계획 내용
노출은 관측되지 않았습니다. 파일명·ignore 규칙 확인에 대한 마지막 worker의
DONE_WITH_CONCERNS는 실제 기록과 독립 리뷰에 근거한 기존 ruling으로 수용했습니다.
검색 노출이 있었던 초기 candidate는 별도 실패 기록으로 남습니다.
1.0.3은 파일명 목록·작업에 필요한 설정 직접 읽기의 허용과 none 보고 기준을
명시합니다. 새 두 세션에서 실제 해당 조회와 native/shell 내용 검색을 함께 수행하고,
각각 10개·8개 테스트 및 설정 복원을 확인했습니다. 두 원본 보고는 허용된 조회를
공개하고도 불필요한 scope concern 없이 DONE/none이었습니다. 이는 해당 fixture의
관측이며 일반적인 준수율이나 강제 파일 접근 차단을 증명하지 않습니다.
Claude Code의 모델·effort 대응과 Cursor event trace는 그때도 실제 실행
미측정이었습니다. 재현 절차와 버전별 관측은 [테스트](testing.md)에 있습니다.

## 라이브 증거 경계

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요.

## 새 호스트 지원

새 지원을 레지스트리와 공개 안내에 넣으려면 실제 관측 증거와 별도 지원
결정이 필요합니다. 지원 범위를 바꾸기로 결정한 경우에만 `products.toml`,
공개 안내, 테스트를 함께 고치세요. 공유 사용자 안내는
[호환성](../../../users/ko/compatibility.md)을 보세요.

## 2026-09-14 MCP 도구 필터를 넣게 된 경위

위 표가 현재 상태이고, 이 절은 그 상태에 이르기까지의 경위와 버린 선택지를
남깁니다.

macOS의 실제 Codex controller에서 별도 합성 저장소와 linked worktree를 사용했습니다.
보완 전 `d7e16ca`의 Cursor 신규·재개 2회와 Grok 신규·재개 2회는 모두 구현·테스트·
worker 직접 커밋·보고서 작성을 완료했습니다. 최종 독립 테스트는 Cursor 10개,
Grok 11개였으며 공백 문자 29개와 잘못된 타입 6개도 추가 검사했습니다.

경고 원인은 Grok이 Cursor MCP 설정을 가져와 `playwright-sandboxed` 초기화를
시도하는 것이었습니다. 전역 설정 변경 대신 자식 환경의 compatibility 변수 두 개를
끄는 방식을 채택했습니다. 모델 이름·인증·세션 저장소는 그대로 유지됩니다.

`Agent`/`task` 도구 그룹 제외는 명령 결과 조회·종료 도구까지 제거해서 채택하지
않았습니다. 실제 도구 이름 `spawn_subagent`만 제외하는 시도도 생성 도구를 없애지
못했습니다. 최종 필터는 `search_tool,use_tool`만 제외하고 `MCPTool(*)` 거절을
전달합니다. 하위 에이전트·예약 작업의 강제 차단은 이번 변경의 보장이 아닙니다.

최종 도구 필터로 시작한 새 Grok 세션에서 13개 테스트와 실제 background shell을
실행했습니다. `get_command_or_subagent_output`으로 `BG_PROBE_OK` 출력,
`completed`, exit 0을 회수했고 도구 호출·결과 9/9를 대조했습니다. 도구 목록에는
명령 결과 조회·종료 도구가 남고 MCP 검색·호출 도구는 없었습니다. `Agent` 제외
candidate에서 성공한 구현·재개 호출을 이 최종 필터의 증거와 혼동하지 않습니다.

같은 세션을 재개한 후속 요구에서도 RED exit 1 → GREEN 13 tests/exit 0,
worker 직접 커밋과 DONE을 확인했습니다. 도구 호출·결과는 11/11이며 두 호출의
session ID는 일치했습니다. 최종 두 Grok 호출 모두 MCP handshake 경고는 0건이었고
sandbox 설정과 journal도 종료 후 정리했습니다. 마지막 독립 검사는 Cursor 11개,
Grok 13개와 전체 commit diff --check를 통과했고 두 fixture는 clean이었습니다.

수정된 runner의 Cursor 기존 세션 재개도 구현·RED exit 1·GREEN 11 tests/exit 0·
직접 커밋으로 완료됐으며 실제 도구 호출·결과는 14/14였습니다. Cursor 환경과
승인·sandbox 인자는 변경하지 않았습니다.

Grok 자체의 managed-config 권한 경고, 플러그인 이름 충돌, 호환 hook 파싱 경고는
남아 있습니다. 전역 설정을 삭제하거나 경고 출력을 숨기지 않았습니다. 기존 MCP
서버 목록이 init/inspect에 표시되는 사실은 실제 연결·호출 증거가 아닙니다.
Windows 실행, 전면적인 OS 격리, 실제 적용 effort, 대형 프로젝트 장기 안정성은
이번 관측으로 입증하지 않습니다. 원본 공급자 기록은 로컬에만 보존합니다.

검증한 런타임 SHA-256 (실행 전후 일치):

- `resolve_backend.py`: `780adfee9042bf4be6ecc0e6104adc70024c265b50827bee828182eb3971f797`
- `run_worker.py`: `3bda36903eabfa53c9ca97f35f3b349cba52b2c8ddaa387d8090fc694001302b`

### 남겨 두는 두 가지 판단

`--disallowed-tools`와 `--deny`를 값 표기까지 확인하고 없으면 거절하는 판정은,
옵션 이름이 설명 문장에 등장하는 것만으로 통과하지 않게 하려고 좁게 잡았습니다.
대신 같은 옵션을 다른 표기로 적는 빌드는 실행 가능한데도 거절됩니다. 이 제품은
바로 그 형태의 결함 — 실제 CLI 출력 대신 한 가지 표기를 규칙으로 굳힌 것 —
때문에 한 번 못 쓰게 된 적이 있습니다. 지금은 좁은 쪽을 택했습니다. 거절이
`missing_flags`로 드러나 조용히 약한 실행으로 넘어가지 않기 때문입니다. 거절
사례가 실제로 나오면 `_declares`로 완화하는 쪽이 맞습니다.

MCP discovery 환경 변수는 반대로 아무 판정도 걸려 있지 않습니다. Codex의 원인
분리 probe에서 실제로 handshake 실패를 없앤 쪽은 이 변수였는데, 공급자가 이름을
바꾸면 오류 없이 조용히 무력해집니다. 이름을 확인할 방법이 공급자 문서에 없어
판정을 걸지 않았고, 대신 위 표에 `not_measured`로 남겼습니다.
