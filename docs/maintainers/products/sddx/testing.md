# sddx 테스트

이 문서는 공급자 없는 계약, `resolve_backend.py` 픽스처 경계, Git sandbox 준비·정리와
범위가 제한된 라이브 재검증을 소유합니다. 라이브 관측을 일반적인 provider 품질이나
다른 호스트의 실행 보장으로 확대하지 않습니다.

픽스처 경로는 `tests/products/sddx/`입니다.

검사 명령은 아래 「공급자 없는 증거」와 「명령」입니다. 「행동 probe」부터
「1.0.3」까지는 그 시점의 측정 기록입니다. 지금 계약을 바꾸지 않습니다.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
`tests/products/sddx/test_resolve_backend.py`는 PATH에 가짜 바이너리를
넣어 신원 규칙을 잠급니다. 실제 Cursor/Grok 계정을 쓰지 않습니다.
Windows `.cmd` 왕복과 Win32 전송 픽스처는 삭제했습니다. 그 픽스처는
Windows 지원 증거가 아니었습니다. 합성 CLI는 stdout/stderr를 LF로 고정해
raw-byte 단언이 텍스트 변환과 섞이지 않게 합니다.
`tests/products/sddx/test_prepare_grok_sandbox.py`는 임시 저장소와 실제 linked
worktree를 만들고 Git 경로 계산, 기존 TOML 원문 복원, 재진입, 심볼릭 링크 거절,
`fchmod` 없는 다시 쓰기, CLI 성공·실패 출력을 검사합니다. Git 경로는 pathlib로
정규화해 비교합니다. 표준 `tomllib`를 사용하므로 Python 3.11 이상이
필요합니다.

생성되는 `sddx-worktree` 프로파일의 `read_write`는 linked worktree의 Git 디렉터리와
공용 `.git` 디렉터리를 허용합니다. 따라서 공용 `.git` 안에 있는 다른 브랜치 ref에도
쓰기 권한이 생깁니다. 이 검사는 정상적인 단일 컨트롤러 실행에서 기존 파일 변경을
보존하는지 확인하며, 악성 동시 변경에 대한 보안 경계나 Grok sandbox의 실제 실행
성공을 입증하지 않습니다.

결정적 검사:

- Grok 후보는 PATH의 `grok`뿐이다. `agent`만 있으면 `not_found`다.
- `agent`는 Cursor로 채택되지 않는다.
- Grok 신원의 `cursor-agent` 또는 `cursor`는 `identity_mismatch`다.
- Cursor는 headless print(`--print` 또는 `-p`), `--trust`, `--auto-review`,
  `--sandbox`, 확인된 `stream-json` 출력 형식을 모두 선언해야 한다. 하나라도
  없으면 `missing_flags`이며 force/yolo 일괄 승인으로 물러나지 않는다.
- Cursor와 Grok의 `--resume`은 값을 받는 선언(`<id>` 또는 `[id]`)이어야
  한다. 이름만 있고 값이 없으면 `missing_flags`다.
- Cursor Usage 줄에 `[prompt]` 또는 `[prompt...]`가 있어야 한다. 없으면
  `missing_flags`다. `build_argv`가 위치 인자로 prompt를 붙이기 때문이다.
- Cursor 모델 목록 명령이 성공해 id를 읽었고 그중 Grok이 없으면 `no_grok_model`
  이다. Grok id는 있는데 버전 세그먼트가 `4.7`인 것이 없으면 `no_grok_4_7`이다.
  `cursor-grok-4.6-*`, `cursor-grok-4.5-*`, `-fast`로 끝나는 id는 목록에
  있어도 `model_ids`에 들어가지 않는다. `-fast`만 있으면 `no_grok_4_7`이다. 선언된 목록 명령이 없거나 모두 실패하면 `no_model_list`,
  목록은 왔으나 id를 하나도 읽지 못하면 `model_list_unreadable`이다.
- Grok Build `models` 출력의 `* id (default)`와 `- id` 불릿에서 id를 읽는다.
  `model_ids`는 정확히 `grok-4.7`만이다. `grok-4.7-build-fast`, `grok-4.6`,
  `grok-4.5`는 빠진다. `grok-4.7`이 없으면 `no_grok_4_7`이다.
- `run_worker.py`는 Grok과 Cursor 모두 `--model`을 넘긴다. Grok은 그 옆에
  effort 플래그를 그대로 둔다. `model_ids` 밖의 id는 worker를 시작하지 않는다.
- 모델 목록의 ANSI 색상 escape는 id의 일부가 아니다. 색을 입힌 목록은 평문
  목록과 동일하게 읽힌다. 탐사는 `FORCE_COLOR=0`·`NO_COLOR=1`·`CLICOLOR=0`을
  붙여 실행하며 나머지 환경은 그대로 상속한다.
  실측(cursor-agent 2026.09.15-d2fe57e): 색을 칠지는 부모 환경의 `FORCE_COLOR`가
  먼저 정하고 그다음이 TTY 여부다. `FORCE_COLOR=1`이면 파이프에도 904개의 escape가
  섞이며 `NO_COLOR=1`·`CLICOLOR=0`·`TERM=dumb`로는 못 막는다. 재현은 둘 중 하나다 —
  `FORCE_COLOR=1 cursor-agent --list-models | cat -v`, 또는 `pty.spawn`으로 stdout을
  실제 TTY로 만들기. 고치기 전 파서는 그 실제 출력에서 grok 0개, 고친 파서는 14개다.
  두 방어층은 서로 독립이며 `test_resolve_backend.py`가 각각 고정한다.
- Grok help에 `--cwd`가 없으면 `missing_flags`다.
- argv에 `--worktree`와 `--plugin-dir`가 없다. Grok 고정 플래그에
  `--disable-web-search`가 있다.
- 없는 backend의 JSON은 `launch`가 `null`이고 `model_ids`가 빈 목록이다.

`tests/products/sddx/test_extract_task.py`는 제목 일치, 본문 경계, 중복·부재·빈
본문의 exit 3, 인자·파일 오류의 exit 2, 기존 출력 파일 비덮어쓰기를 잠급니다.
`tests/products/sddx/test_run_worker.py`는 시도 디렉터리 여섯 파일, argv 구성,
backend별 `--model`/`--sandbox-profile` 배타, `run.json` 필드(`skill_version`
포함)와 상태, 실행 중 `session_id` 기록, 래퍼 SIGTERM → `interrupted`,
러너 중단 시 worker 종료와 두 번째 인터럽트의 kill, SIGTERM 처리기의 실행 전
설치, 첫 출력 기한(`--timeout 0`·재개 포함, 더 짧은 `--timeout` 우선), 기본
타임아웃 7200, 래퍼 exit 규칙, 닫힌 stdin, 시도 경로 거절을 검사합니다.
`tests/products/sddx/test_worker_status.py`는 `stale`(running인데 pid가 없을
때만 true), `session_id_in_log`(기록에 ID가 없을 때만 채움), 읽기 전용 응답,
`pid_alive`,
Cursor·Grok 두 로그 형태의 bounded tools index, 기본 응답에 로그 본문이
없다는 점, 너무 깊은 JSON 줄 건너뛰기, `--stream` 기본 2048·최대 8192바이트,
64 KiB 응답 상한, offset
처리를 검사합니다. 어느 검사도 공급자를 호출하지 않습니다.

Windows `.cmd` 왕복 검사(`skipUnless(os.name == "nt")`)는 삭제했습니다.
CI에서 돈다고 적지 않으며, skip을 통과나 Windows 지원으로 쓰지 않습니다.
Windows는 지원하지 않습니다.

페이로드 계약 통과는 파일 정체성, 이식 가능한 frontmatter, 금지 문자열만
증명합니다. 이 공급자 없는 증거만으로 라이브 CLI, 과금, 모델 품질을
측정했다고 할 수 없습니다.

## 행동 probe

[행동 probe](../../../../tests/products/sddx/behavior-probes.md)는 이전 응답을 주지 않은
독립 문맥에서 native 모델이 제안한 행동을 컨트롤러가 수동 판정합니다. 2026-09-11
controller 시나리오 5개는 완료 판정, sandbox 실패, session 재사용·전환 기준을 모두
통과했습니다. 별도의 worker 역할 합성 표본에서는 external skill 읽기 제안이 baseline
2/5에서 candidate worker 안내 적용 후 0/5로 줄었습니다. 다섯 guided 응답은
`candidate-worker.md`를 읽었고, 최종 역할 문장과 내용은 같지만 기존 문단의 순서와
서식은 달랐습니다. 이 결과는 문자열 검사가 아니며, 작은 native simulation을 실제
Grok 호출이나 runtime 신뢰도 통계로 취급하지 않습니다.

## 2026-09-11 1.0.1 최초 Grok 검사

측정 환경은 macOS 26.5.2, Python 3.14.7, Codex controller, Grok 1.0.25,
`grok-4.6` High였습니다. 새 remote 없는 로컬 저장소의 linked worktree에서 다음
절차를 수행했습니다.

1. 수정된 제품에서 resolver와 sandbox helper를 확인하고, 각 호출 전 `prepare`,
   worker 종료 후 `cleanup`을 실행합니다.
2. 첫 task에서 Unicode 공백 정규화 구현과 테스트를 worker가 직접 커밋하게 합니다.
3. 같은 worker session에 TypeError 메시지와 동등성 테스트를 추가하라는 통제된
   요구를 보내고, 수정 커밋 뒤 native scoped review를 반복합니다.
4. 새 session으로 CLI task를 실행하고 worker의 세 번째 직접 커밋을 확인합니다.
5. fixture에서 `python3 -m unittest discover -s tests -v`, 기준과 결과 commit을
   인자로 준 `git diff --check`, `git status --short`, 변경 파일 목록과 최근 commit을
   확인합니다.

실제 provider 호출은 세 번이었고 모두 worker exit 0, cleanup exit 0, report `DONE`,
worker 직접 커밋으로 끝났습니다. 첫 task는 구현 전 `textnorm` 부재로 loader-error
test 1개를 실행한 RED exit 1 뒤 GREEN 7 tests exit 0, 통제된 same-session 수정은
RED 8 tests exit 1 뒤 GREEN 8 tests exit 0이었고, 둘째 task는 RED 14 tests
exit 1 뒤 GREEN 14 tests exit 0이었습니다. 둘째 task의
RED/GREEN은 shell wrapper exit 0 안의 실제 test exit를 별도로 확인했습니다. 원래
구현 결함은 발견되지 않았으며, same-session 변경은 미리 승인된 추가 요구의 resume
동작을 검증한 것입니다.

최종 독립 unittest는 14 tests, exit 0이었고 전체 commit 범위의
`git diff --check`도 exit 0이었습니다. worktree는 clean이었으며 세 worker commit에는
요구된 애플리케이션·테스트·README 파일 다섯 개만 포함됐습니다. 컨트롤러가 구현을
수정하거나 커밋을 보조하지 않았습니다. 생성 sandbox 설정과 복원 기록은 정리됐고,
기존 설정 byte 보존은 라이브 fixture가 아니라 공급자 없는 검사에서 입증했습니다.

실제 tool trace의 수동 검토에서는 brief-first 순서를 확인했고 external skill·전체 계획
읽기, nested agent, MCP tool 호출이나 역할 위반은 관측되지 않았습니다. 기존 host
integration의 MCP 초기화·handshake·자동 재시작 경고는 계속 나타났습니다. 이 경고는
모델의 MCP tool 호출과 다르며, 경고가 사라진다고 보장하지 않습니다.

독립 whole-fixture native review는 clean checkout, 생성 설정·journal 부재, worker가
소유한 commit 범위, same-session 수정과 새 task session, 독립 14-test 로그를 다시
확인하고 Critical/Important/Minor 0건으로 accept했습니다.

제품 구현 HEAD에서 `python3 scripts/verify.py`는 868 unittest를 포함한 전체
공급자 없는 검사를 완료해 exit 0이었습니다. 이후 변경은 문서뿐이므로 전체 suite를
반복하지 않고 내용·링크·diff를 검사합니다. Cursor worker와 Claude Code host 실행은
`not_measured`입니다.

## 명령

```bash
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py
python3 scripts/release.py check --product sddx
python3 -m unittest tests.products.sddx.test_resolve_backend
python3 -m unittest discover -s tests/products/sddx -p test_prepare_grok_sandbox.py -v
git diff --check
```

`release.py check`는 제품 소유 경로와 공용 릴리스 코드의 작업 트리가 깨끗할 때만
통과하므로, 변경을 커밋한 뒤에 실행합니다.

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 오프라인 통과를 호스트 품질로 설명하지 마세요.

## 6.0.0 오프라인 검사

6.0.0의 필수 증거는 `python3 scripts/verify.py --skill sddx`입니다. 러너 중단이
worker를 끝내고 두 번째 인터럽트에도 `running`이 남지 않는지, 출력 없는 시도가
`FIRST_OUTPUT_SECONDS` 뒤 `timed_out`으로 끝나는지(`--timeout 0`·재개 포함,
더 짧은 `--timeout` 우선, 곧바로 출력하는 worker는 제외), 기본 타임아웃 7200,
Grok `tool_use` 색인과 결과 본문 비복사, 그리고 각 규칙 문구가 모든 면에 있는지를
잠급니다. 라이브 확인은 아래 `6.0.0 라이브 확인`에 있습니다.
이 변경 뒤 `sddx-contract`는 340개 테스트입니다. 파일별로 `test_contract` 36,
`test_extract_task` 38, `test_prepare_grok_sandbox` 23, `test_resolve_backend`
75, `test_run_worker` 114, `test_worker_status` 54개입니다.

## 6.0.0 라이브 확인

2026-09-24, macOS 26.5.2 arm64, `grok 1.0.41 (4220f3b224a6) [stable]`, 모델
`grok-4.7` High. 원격 없는 새 로컬 저장소의 linked worktree에서 실제 호출 8회.
각 시도 앞뒤로 `prepare`/`cleanup`을 돌렸고 매번 `cleaned: true`였습니다. receipt와
로그는 커밋하지 않았습니다.

| # | 확인 | 결과 |
| --- | --- | --- |
| 과거 로그 | 5.0.0과 같은 로그의 색인 비교(호출 없음) | Grok 실전 로그 두 개가 읽기·검색·셸 0/0/0에서 26/32/15, 64/32/32(`truncated`)로 채워짐. Cursor 실전 로그 두 개는 변경 전과 동일 |
| L1 | 도구 색인 | `exited` 0, 70초. `reads` 2(brief, README), `searches` 1(`PAPAYA`), `shells` 4개 모두 exit 0(`echo hi` 포함). status에 파일 본문 없음 |
| L2 | L1 세션 재개 | 같은 `session_id`로 `exited` 0, 77초. 무출력 기한 미발동 |
| L3 | 러너 pid에만 SIGTERM | wrapper 130 즉시, worker 프로세스 사라짐, `interrupted`, `exit_code` -15, `the runner was interrupted (SIGTERM or Ctrl-C)`, `pid_alive: false`. worker가 띄운 zsh와 `sleep 120`은 pid 1로 입양되어 남았고(러너는 쫓지 않음) pid로 정리 |
| L4 | L3의 중단 세션 재개 | `exited` 0, 18초. 멈춤 없음 |
| L5 | `--timeout 45` | wrapper 124, `timed_out`, `exit_code` -15, worker 사라짐. 백그라운드로 넘어간 `sleep 120`은 `shells`에 `exit_code: null`로 기록. 손자 프로세스는 L3처럼 남아 pid로 정리 |

러너 가장자리 보강(97a5eec) 뒤 L1·L3·L5를 다시 돌렸습니다. L1b는 `exited`
0(185초), `shells` 11개에 exit 1인 셸까지 종료 코드가 기록됐습니다. L3b는
wrapper 130(1초), worker 사라짐, `interrupted`/-15/새 문구, 손자 프로세스는 남아
pid로 정리했습니다. L5b는 wrapper 124, `timed_out`/-15, worker 사라짐, 손자
프로세스는 pid로 정리했습니다. 모든 `cleanup`은 `cleaned: true`였습니다.

관찰: Grok은 셸 호출이 담긴 assistant 메시지를 그 호출이 돌아오거나 백그라운드로
넘어간 뒤에 기록합니다. 그래서 L3처럼 전경에서 실행 중인 셸은 색인에 아직 없습니다.

무출력 기한 자체는 오프라인 합성 CLI로 증명합니다. 실전 E3 멈춤은 재현을 목표로
하지 않았고 L4에서도 나타나지 않았습니다. 이 결과는 이 Mac과 이 Grok 버전의
관측이며 Cursor 경로는 오프라인 증거만 있습니다.

## 5.0.0 오프라인 검사

5.0.0의 필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
resolver가 Grok 4.7이 아닌 id와 `-fast` id를 `model_ids`에서 빼는지, Grok
`run`이 `--model grok-4.7`을 넘기는지를 잠급니다. 이 변경에서
`python3 scripts/verify.py`는 exit 0이었고 `sddx-contract`는 320개
테스트였습니다. 라이브 워커 재실행은 요구하지 않습니다. 4.0.3의 XHigh
로딩과 워커 스모크는 이 버전에서 다시 돌리지 않았습니다.

## 4.0.3 오프라인 검사

4.0.3의 필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
정의 파일은 `agents/sddx-reviewer-xhigh.md`이고 `plugin.json`에 `agents` 키가
없습니다.

## 4.0.2 오프라인 검사

4.0.2의 필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
SKILL.md가 `subagent_type: sddx:sddx-reviewer-xhigh`를 적는지를 잠급니다.

## 4.0.1 오프라인 검사

4.0.1의 필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
`test_resolve_backend.py`가 값을 받지 않는 `--resume`과 Cursor Usage에
위치 인자 prompt가 없는 경우를 `missing_flags`로 잠급니다. 라이브 워커
재실행은 요구하지 않습니다. XHigh 정의 로딩의 라이브 결과는 위
「리뷰어 effort 증거」에 있습니다.

## 4.0.0 오프라인 검사

4.0.0의 필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
`tests/products/sddx/test_contract.py`의 expect lock이 description·HARD-GATE·
cases 문구를 잠급니다. `tests/products/sddx/test_extract_task.py`가
`--global-constraints`의 이어붙이기·부재·중복·빈 본문·exit 3을 잠급니다.
라이브 워커 재실행은 요구하지 않습니다.

## 1.0.1 후속 실패 재현

동일 제품 HEAD `6cc1e39`를 대상으로 두 개의 새 local linked-worktree fixture에서
각각 Grok을 세 번 호출했습니다. 첫 후속 fixture는 두 새 세션 모두 전체 계획을
읽었고, 다음 main 기반 fixture는 CLI의 새 세션에서 이를 재현했습니다. 정확한
worker rules가 전달됐고 실제 성공 read 결과가 계획 본문을 반환했으므로 규칙 전달
누락으로 설명할 수 없습니다. worker의 clean DONE 보고에서 위반도 빠졌습니다.

두 fixture의 최종 앱 테스트는 각각 15개/14개 exit 0, worker 직접 커밋은 각각
3개였습니다. 기존 CRLF·주석 포함 sandbox TOML의 원문과 0640 권한은 매 호출 후
일치했고 journal도 제거됐습니다. 앱 성공과 별개로 역할 준수는 FAIL이며 독립 최종
리뷰도 부분 통과로 판정했습니다. 이전 최초 성공 표본은 이 후속 실패를 상쇄하지
않습니다. MCP 초기화 경고와 모델의 실제 MCP 도구 호출은 구분합니다.

초기 empty fixture는 Python 3.14 unittest의 NO TESTS RAN/exit 5를 미측정으로
기록합니다. shell wrapper exit 0 안의 실제 테스트 비0도 통과로 집계하지 않습니다.
로컬 raw provider trace/receipt는 저장소에 커밋하지 않습니다.

## 1.0.2 검증 절차

[행동 probe](../../../../tests/products/sddx/behavior-probes.md)의 모델 상속·High/XHigh,
위반 보고·도구 기록 누락·계획 링크 시나리오를 독립 native 문맥에서 실행합니다.
문구 포함 검사와 실제 행동 검사, 실제 Grok 실행은 서로 다른 증거입니다.

라이브에서는 동일한 함수 → 통제된 같은 세션 수정 → 새 CLI 작업을 사용합니다.
전체 계획은 fixture에 그대로 두어 읽지 않는 행동을 측정합니다. brief에 필요한
조건을 완결하고 worker 규칙과 dispatch 경계를 모두 전달합니다. 각 호출에서
실제 read와 shell 출력, scope deviations, 실제 테스트 exit, worker 커밋, session ID,
기존 sandbox 원문·권한 복원을 확인합니다. 리뷰는 같은 오케스트레이터 모델을
상속하며 effort를 따로 지정하고 선택 이유를 기록합니다. 역할 읽기 제한은 여전히
프롬프트 지침이며 OS 파일 접근 차단을 구현한 것은 아닙니다.

### 1.0.2 작성 중 발견한 검색 노출

첫 candidate로 세 단계를 실행했을 때 함수·resume은 역할 준수를 확인했지만,
CLI 작업이 대상 경로 없는 workspace `grep`으로 계획의 두 줄을 받아왔습니다.
ReadFile로 열지 않아도 검색 결과에 계획 내용이 반환되면 역할 FAIL입니다.
이번 worker는 이를 scope deviations에 공개하고 DONE_WITH_CONCERNS를 반환해
보고 개선은 확인됐습니다. 첫 candidate의 최종 앱 14 tests·커밋·복원은 성공했으며,
해당 실행 자체의 판정은 부분 통과로 유지합니다.

이를 근거로 brief의 구체적인 Search paths와 명시 파일 직접 읽기 순서를 추가했습니다.
파일 glob만으로는 디렉터리 경계가 정해지지 않는 점을 명시했습니다. controller의
증거 추출도 검색 결과를 포함한 모든 tool result를 보존하도록 보완한 별도 로컬
검증 도구를 사용합니다. 이는 제품에 새 실행 엔진을 추가한 것이 아닙니다.
이전 candidate의 소스 해시·원문과 실패 로그를 보존하고, 최종 문구로 세 단계를
새 worktree에서 다시 검증했습니다.

### 최종 문구의 실제 검증 결과

동일 seed에서 새 linked worktree를 만들어 Grok을 세 번 호출했습니다. 최종 runtime
스킬·worker rules·dispatch·helper 등 6개 파일의 SHA-256을 호출 전 고정하고 종료 뒤
일치를 확인했습니다. 함수는 RED exit 1 → GREEN 8 tests/exit 0, 통제된 같은 세션
수정은 RED 9 tests/6 failures/exit 1 → GREEN 9/exit 0, 새 CLI는 RED 6 tests/4
failures/exit 1 → 전체 GREEN 15/exit 0이었습니다. wrapper는 사용하지 않았습니다.
최종 독립 검사도 15 tests/exit 0, 전체 diff check exit 0, clean fixture였습니다.

세 worker 직접 커밋은 task 파일 5개에 한정됐습니다. 기존 sandbox 원문·0640 권한과
journal 제거, 실제 session 재사용·전환을 확인했습니다. 모든 tool 호출과 결과를
14/14, 12/12, 16/16으로 대조했으며 최종 세 호출에는 계획 내용 읽기나 workspace
내용 검색이 없었습니다. 필요한 파일 직접 읽기를 사용했으므로 검색 도구 자체의
경로 제한 기능이나 강제 파일 접근 차단을 입증한 것은 아닙니다.

마지막 worker는 root 파일명 목록 조회와 .gitignore 읽기를 DONE_WITH_CONCERNS로
공개했습니다. 독립 리뷰와 기존 컨트롤러 ruling은 이를 커밋·저장소 확인에 부수된
비차단 관측으로 수용했습니다. 실제 목록에는 계획 파일명도 있었으나 내용은
반환되지 않았습니다. 원본 보고와 Minor 절차 해석 사항을 보존합니다. 앞선 candidate의
실제 계획 내용 검색 노출은 FAIL로 유지합니다. 이번 개선 작업의 Grok 호출은 처음
3회와 최종 문구 3회를 합쳐 6회이며, 이들을 하나의 무실패 실행으로 합치지 않습니다.

실제 오케스트레이터는 실행 기록으로 확인한 gpt-6-astra/XHigh였으며, 모든 native
리뷰는 모델 인자를 생략해 상속했습니다. 국소 Task·재리뷰는 High, 전체 정책·증거
검토는 XHigh입니다. 특정 모델 고정 정책이 아닙니다. 최종 문구 반영 후 전체 공급자
없는 검증은 868 unittest와 추가 검사 exit 0이었으며, 이후 관측 결과 문서는
내용·링크·diff로 확인합니다.


## 1.0.2 검색 추가 검증과 남은 모호함

현재 main `2e9036a`의 문구로 새 Grok 세션 두 개에서 실제 내용 검색을 요구했습니다.
Native grep은 명시한 소스와 테스트 경로에 각각 검색해 본문 5줄·4줄을 반환했고,
shell rg는 공백을 포함한 두 경로를 따옴표로 지정해 파일 4개의 9줄을 반환했습니다.
계획과 범위 밖 메모에도 같은 검색어를 두었으나 해당 내용은 반환되지 않았습니다.
독립 테스트는 각각 12개·9개 exit 0, 도구 결과는 20/20·18/18을 대조했습니다.

파일명 조회의 분류는 모호했습니다. 이전 worker는 root 목록·ignore 규칙 조회를
우려사항으로 보고했고, 추가 shell 실행은 root 목록 조회 뒤 none을 보고했습니다.
독립 리뷰는 계획 본문 노출을 확인하지 못했지만 `any search`와 `content search`가
섞인 문구로는 파일명 조회·필요한 설정 직접 읽기의 보고 기준이 명확하지 않다고
판정했습니다. 당시 판정과 원본 보고는 수정 후에도 그대로 보존합니다.

## 1.0.3 파일명·설정 조회 명료화 검증

현재 worktree의 파일명 목록과 task에 필요한 ignore·빌드·테스트 설정 직접 읽기를
허용된 확인으로 명시합니다. 이 행동만으로는 scope concern이나 ruling을 요구하지
않고, 내용 검색의 경로 제한·계획 본문 금지·기록 부족 UNVERIFIED는 유지합니다.

독립 native 문맥에서 명료화 전·후 각각 5개 표본으로 파일명 조회, 설정 직접 읽기,
실제 계획 내용 노출, 도구 기록 부재를 분류합니다. 실제 Grok에서는 파일명·설정 조회와
native grep 또는 공백 경로의 shell rg를 한 작업에 함께 요구하고, 보고의 분류와
실제 결과를 대조합니다. 이 검증은 지시된 상황의 관측이며 자연 발생 준수율이나
OS 접근 차단을 입증하지 않습니다.


### 실제 결과

명료화 전 native 표본 5개는 파일명·설정 조회를 모두 AMBIGUOUS로, 수정 후 5개는
모두 명시적 ALLOWED / none으로 분류했습니다. 계획 내용 노출 FAIL과 도구 기록
부재 UNVERIFIED는 유지했습니다. 이 표본은 이전 응답을 주지 않은 별도 문맥이며
모델 준수율 통계는 아닙니다.

새 Grok 세션 두 개에 최종 worker rules와 dispatch 경계를 전달했습니다. 두 작업 모두
root 파일명 목록, .gitignore와 일반 테스트 설정 직접 읽기, 실제 내용 검색을 수행하고
이를 보고서에 기록한 뒤 DONE / Scope deviations: none으로 마쳤습니다. Native grep은
소스·테스트 경로를 각각 지정했고, shell rg는 공백을 포함한 두 경로를 따옴표로
지정했습니다. 계획·범위 밖 메모에도 검색어를 두었으나 본문 반환은 없었습니다.

Native 작업은 RED 10 tests/4 failures/exit 1 → GREEN 10/exit 0, shell 작업은
RED 8 tests/4 failures/exit 1 → GREEN 8/exit 0이었습니다. 독립 최종 테스트도 각각
10개·8개 exit 0이며, 설정에서 확인한 python3를 사용했습니다. 각 worker는 지정
소스와 신규 테스트 두 파일만 직접 커밋했고 Git 상태는 clean이었습니다.

두 작업의 도구 호출·결과는 각각 22/22이며, 기존 sandbox 원문·0640 권한 복원과
journal 제거를 확인했습니다. Native 작업은 .git을 디렉터리로 조회해 IsAFile 오류를
받은 뒤 worktree pointer 한 줄을 읽고 정상 Git 커밋 절차를 수행했습니다. Pointer
조회는 원본 보고에 포함됐고 ListDir 오류는 원본 도구 기록에서 확인했습니다. Pointer
대상의 파일 내용을 따라 읽지 않았습니다.

Runtime 6개 파일의 해시가 호출 전·후 동일했습니다. 전체 공급자 없는 검증은
868 unittest와 추가 검사 exit 0, 제품 검사는 24개 계약·45개 SDDx 테스트와 compile
exit 0이었습니다. 마지막 관측 결과 문서는 내용·링크·diff를 확인합니다. 이전 버전의
실패와 모호함 기록은 이 새 결과로 덮어쓰지 않습니다.

## 리뷰어 effort 증거

공급자 없는 증거는 `tests/products/sddx/test_contract.py`의 계약 검사입니다.
`.claude-plugin` 페이로드가 sddx에만 허용되고 다른 제품에는 거부되는지,
`plugin.json`이 제품명을 가리키는지, `plugin.json`의 version이 `release.toml`의
버전과 같은지, `plugin.json`에 `agents` 키가 없는지, `agents/`에 마크다운 정의가
정확히 `sddx-reviewer-xhigh.md` 하나이고 `name`이 파일명과 같고 `effort`가
`xhigh`이며 `model` 키가 없고 `disallowedTools`가 Edit·Write·NotebookEdit를
이름으로 포함하는지 확인합니다. 이 검사는 필드 선언까지만 확인하며, 호스트가
실제로 그 도구를 차단하는지는 확인하지 않습니다.

라이브 확인은 배포되는 제품 파일을 링크한 상태에서 합니다.
`claude plugin details sddx@skills-dir`는 Agents (1) `sddx-reviewer-xhigh`여야
합니다. Task는 `subagent_type: sddx:sddx-reviewer-xhigh`로 뜨고, 맨 이름은
찾지 못합니다. 자식 트랜스크립트 어시스턴트 이벤트의 `effort`가 `xhigh`인지도
봅니다. 스킬 호출 이름은 `sddx`입니다.

`4.0.3`에서 확인했습니다. `plugin details` Agents (1). Task 자식 기록
`effort: xhigh`(부모 세션은 high). Cursor `2026.09.15-d2fe57e`와 Grok
`1.0.34` 워커 스모크는 둘 다 `state: exited`, 보고서 `DONE`입니다.

계약 검사는 파일이 존재한다는 것까지만 증명합니다. Claude Code가 skills-dir
플러그인에서 agents를 계속 싣는지는 증명하지 못하므로, 릴리스마다 위 라이브 확인을
반복합니다. 확인에 실패하면 정의가 조용히 사라진 상태이므로 릴리스를 멈춥니다.

## 2.0.0 검증

증거는 네 종류로 나눠 기록하며 서로 대체하지 않습니다.

| 증거 종류 | 이 버전의 상태 |
| --- | --- |
| 오프라인 helper·argv 계약 검사 | 실행함 |
| 지침 문구 검사 | 실행함 |
| native 행동 probe | 이 버전에서 새로 실행하지 않음 |
| 실제 공급자 실행 | 네 조합을 모두 실행함 (`measured`). 조합별·항목별 상태는 [호환성](compatibility.md)이 소유함 |

이 버전에서는 제품 소유자 승인 아래 Claude Code를 호스트로 한 두 조합으로 실제
공급자를 호출했습니다. 둘 다 macOS 26.6.2 arm64입니다.

Cursor는 `cursor-agent 2026.09.10-fd3934a`, 모델 `cursor-grok-4.6-high`로 worker
시도 세 번을 실행했고, 승인 동작·모델 ID 수락과 `configured_effort` 기록·session
ID 회수와 `--resume`·실제 worker 타임아웃·시도 생성 전 거절을 관측했습니다.

Grok은 `grok 1.0.30 (04b7ffed98c6)`으로 모델 인자 없이 worker 시도 두 번을
실행했고(init 이벤트가 보고한 모델은 `grok-4.6`), sandbox 프로파일 준비와
정리까지 한 바퀴를 돌렸습니다.
`streaming-messages-json` 스트림의 실제 형태, `--reasoning-effort`가 명령줄에
실린 사실, session ID 회수와 `--resume`을 관측했습니다.

모델이 실제 적용한 effort는 어느 조합에서도 관측하지 못했으므로 `not_measured`로
남습니다. 요청·설정 effort는 적용값의 증거가 아니며, 공급자가 모델 ID를
수락했다는 사실도, 요청 effort가 명령줄에 실렸다는 사실도 마찬가지입니다.
worker 경계가 CLI에 의해 강제되는지도 `not_measured`입니다. Grok init 이벤트는
`--no-subagents`를 넘긴 뒤에도 `spawn_subagent`를 도구 목록에 실었고, 두 시도가
규칙을 지킨 것은 모델이 지시를 따랐기 때문입니다. Codex 호스트의 worker 실행은
실행하지 않았으므로 `not_measured`로 남습니다. Windows는 지원하지 않으며
`not_measured` OS 대기열이 아닙니다. 관측한 두 조합의 결과를 나머지로
넓히지 않습니다.
조합별 표와 항목별 측정 상태는 [호환성](compatibility.md)이 소유합니다.

### 실제 관측

`tests/products/sddx/`의 discovery 검사(`sddx-contract`)는 281개 테스트로
통과했습니다. `skipUnless(os.name == "nt")` 검사는 없습니다.
파일별로는 `test_contract` 26, `test_extract_task` 29,
`test_prepare_grok_sandbox` 23, `test_resolve_backend` 58,
`test_run_worker` 101, `test_worker_status` 44입니다. 이전 기록의 45개
SDDx 테스트는 Task 1–4의 새 파일이 discovery에 들어오기 전 숫자이고, 212개는 이
버전의 session ID 회수와 시도 타임아웃 작업이 들어오기 전 숫자이며, 269개는
실행 중 `session_id`·`pid_alive`·tools 인덱스가 들어오기 전 숫자입니다.

`verify.py`가 출력한 `python-compile` 단계 인자에 `skills/sddx/scripts`가
들어 있으므로 `extract_task.py`, `run_worker.py`, `resolve_backend.py`,
`prepare_grok_sandbox.py`가 모두 이 단계에서 컴파일됩니다.

`product-contract` 단계는 통과합니다. 작업 도중에는
`tests/repository/test_release_contract.py`의 `EXPECTED` 표가 sddx를 이전 버전
문자열로 고정하고 있어 `test_each_product_owns_an_independent_release_manifest`가
`release.toml`의 새 버전과 어긋났습니다. 이 변경에서 그 표의 sddx 행 하나를 새
버전으로 갱신했고 다른 제품 행은 건드리지 않았습니다. 갱신 뒤 `product-contract`는
24개 테스트로 통과합니다. 제품 버전을 올릴 때는 이 표의 해당 행도 같은 변경에
포함해야 합니다.

Step 3의 네 명령은 최종 상태에서 모두 exit 0입니다.

| 명령 | exit |
| --- | --- |
| `python3 scripts/verify.py --skill sddx` | 0 |
| `python3 scripts/verify.py` | 0 |
| `python3 scripts/release.py check --product sddx` | 0 |
| `git diff --check` | 0 |

`release.py check`는 출력 없이 통과합니다. 이 명령은 제품 소유 경로와 공용 릴리스
코드의 작업 트리가 깨끗할 때만 통과하므로 커밋 뒤에 실행합니다.

제품 검사는 `product-contract`, `sddx-contract`, `python-compile` 세 단계를 모두
실행했습니다. 전체 검사는 12개 단계를 모두 실행해 통과했습니다:
`repository-contract` 361, `korean-package` 9, `korean-offline`,
`korean-live-unit` 244, `korean-live-dry-run`, `image-contract`,
`image-inspector` 48, `how-it-works-contract` 56, `pre-sdd-review-contract` 54,
`pre-sdd-review-evidence` 61, `sddx-contract` 281, `python-compile`.
새 버전에서 다른 제품 단계가 모두 통과하므로 이 버전 변경이 다른 제품을 건드리지
않았음을 확인합니다. 오프라인 단계가 모두 통과해도 실제 공급자 실행 증거는 아닙니다.

## 2026-09-14 MCP 보완 회귀 검사

위 절은 `bfd1cda`까지의 Claude Code 관측입니다. 이 절은 MCP 도구 필터를 넣으며
추가한 검사와, 그 뒤 이 저장소에서 다시 돌린 라이브 확인을 기록합니다.

새 공급자 없는 검사는 실제 합성 자식 프로세스에서 다음을 확인합니다.

- Grok에만 Cursor/Claude MCP discovery 환경 변수 두 개가 `0`으로 전달되고,
  부모 및 관계없는 환경 변수는 보존됩니다. Cursor 환경과 argv 정책도 보존됩니다.
- Grok argv가 `search_tool,use_tool` 제외와 `MCPTool(*)` 거절을 전달합니다.
  필요한 옵션이 없거나 값을 받지 않으면 resolver가 `missing_flags`를 반환합니다.

원인 분리 라이브 probe에서 MCP compatibility 환경 변수만 끈 호출은 handshake
경고 0건, 도구 제외 옵션만 쓴 호출은 `handshake failed` 4건이었습니다. 둘을 합친
초기 candidate 호출은 read_file을 실행하고 exit 0으로 끝났고
그 candidate의 도구 목록에서는 spawn_subagent/search_tool/use_tool이 함께
빠졌습니다. 이 목록은 폐기한 candidate의 것이며 실제로 넣은 필터의 결과가
아닙니다. `Agent`와
내부 `task` 제외는 명령 결과 조회·종료 도구까지 함께 제거했습니다. `spawn_subagent`
표기만 제외하면 도구가 그대로 남았습니다. 따라서 최종 변경은 `search_tool,use_tool`
제외만 채택하고 명령 조회·종료 도구를 보존합니다. 하위 에이전트 경계는 기존
`--no-subagents`와 worker 지침을 유지하며 도구 제거를 주장하지 않습니다. `inspect`와 init의 MCP 서버 목록에는 가져오기 대상이
계속 표시됐으므로 그 목록을 실제 연결 증거로 사용하지 않습니다.

공급자 원본 기록은 로컬에만 보존하고 커밋하지 않습니다.

### 병합 전 라이브 재확인

같은 작업 트리에서 네 번 더 실제로 호출했습니다. Grok은 linked worktree에서
`prepare` → 신규 → `--resume` → `cleanup` 한 바퀴, Cursor는 같은 seed의 다른
worktree에서 신규와 재개입니다. 네 시도 모두 wrapper exit 0, `state: exited`,
`exit_code: 0`이고 각각 구현을 커밋한 뒤 `report.md`를 직접 썼습니다. 각 바퀴의
두 시도는 같은 `session_id`를 보고했습니다.

Grok `prepare`가 만든 `read_write`에는 실제 Git 디렉터리와 공용 Git 디렉터리가
들어갔고, worker는 그 linked worktree 안에서 직접 커밋했습니다. `cleanup`은
`{"cleaned": true}`로 자기가 만든 `.grok`을 지웠습니다.

보완 후 Grok init 이벤트의 도구 23개에 `search_tool`과 `use_tool`이 없고
`spawn_subagent`, `get_command_or_subagent_output`, `kill_command_or_subagent`는
남아 있습니다. 신규와 재개 양쪽에서 같았습니다. MCP 서버 세 개는 여전히
connected로 표시됩니다.

네 시도 모두 stderr가 0바이트였습니다. 보완 전 이 저장소의 Grok 시도도 0바이트여서,
여기서는 MCP discovery 환경 변수의 효과를 가를 수 없습니다. handshake 실패가
줄었다는 관측은 Codex의 원인 분리 probe 기록이며 이 저장소에서 재현하지 않았습니다.

한 시도에서 브리프가 `-t .`를 붙인 잘못된 discovery 명령을 지정했습니다. worker는
그 명령을 실제로 실행해 exit 1을 확인하고, 원인(`tests/`에 `__init__.py` 없음)과
지정 명령의 실제 exit 코드를 보고서에 적은 뒤 유효한 방법으로 RED exit 1 →
GREEN exit 0을 다시 냈습니다. 상태는 `DONE_WITH_CONCERNS`였습니다. 작은 표본의
역할 준수 관측이며 강제의 증거는 아닙니다.

`python3 scripts/verify.py`는 exit 0이고 SDDx 266 tests를
포함한 전체 공급자 없는 검사가 통과했습니다. 저장소 검사 361개도 통과했습니다.
새 테스트는 각각 대응하는 소스 변형에서 실패하는 것을 확인했습니다. 도구 필터 값
축소, 옵션 판정 제거, 퍼센트 변수 판정 되돌리기, `Popen`의 환경 전달 제거,
환경 변수를 Cursor에도 적용하기 — 다섯 변형이 모두 잡혔고 소스는
[호환성](compatibility.md)에 적힌 SHA-256으로 복구했습니다.
