# SDDx 시도 기록과 status가 실행 중에도 사실을 말하게 한다

날짜: 2026-09-16
제품: `sddx` (목표 버전 `2.0.0`, Unreleased)
상태: 진행 중. 현재 계약을 정의하지 않는다.

## 문제

2026-09-16 Codex×Cursor 런(`teacher-style-v11`, `skill_version` `2.0.0`)에서
시도 디렉터리와 ledger를 대조했다. 스트림은 이미 아는 사실을
`run.json`/`status`가 늦게 쓰거나 영원히 안 썼다.

1. Cursor·Grok 스트림은 첫 줄에 `session_id`를 넣는다. 러너는 프로세스가
   끝난 뒤에만 `run.json`에 복사한다. 스킬은 원문이 아니라 `status`를 보라고
   하므로, 실행 중·래퍼가 죽은 뒤에는 있는 ID가 `null`로 보인다. Task 1
   유기 시도는 스트림에 `6e310188…`가 있었는데 컨트롤러는 “보고된 세션이
   없다”고 적고 새 워커로 갔다.
2. 컨트롤러가 래퍼를 SIGTERM으로 끊으면 `KeyboardInterrupt` 경로를 타지
   않는다. Task 1 `run.json`은 `state: running`, `pid`는 죽은 프로세스,
   `session_id`/`ended_at`/`exit_code`는 `null`로 남았다.
3. 스킬은 도구 호출 로그로 역할 준수를 확인하고, 로그 전체를 세션에 붙이지
   말라고 한다. `status --stream` 창은 최대 8KB이고 이벤트 대부분(약 90%)은
   thinking delta다. 그래서 컨트롤러가 `audit-trace.py`를 직접 짰다.

`skill_version` 필드, 끝난 시도의 `--resume`, 역할 검사(플랜/스펙 미읽기)는
이 런에서 동작했다. 그 계약은 바꾸지 않는다.

## 목표

한 시도의 프로세스 사실과 조회 응답이, 스트림과 OS가 이미 아는 것을 숨기지
않게 한다. 컨트롤러가 원문 로그를 파싱하거나 실행 스크립트를 새로 짜지 않고
`run_worker.py status`만으로 재개 ID와 도구 증거를 얻게 한다.

## 비목표

- `SKILL.md`에 규칙 장을 더 넣지 않는다. Watch/Evidence 문장만 사실에 맞춘다.
- `schema_version`을 3으로 올리지 않는다. 과거 schema 2 `run.json`은 그대로 읽는다.
- 트리 해시, 설치 git SHA, 과거 attempt 백필을 하지 않는다.
- 역할 준수 PASS/FAIL/UNVERIFIED, DONE, 402를 러너가 판정하지 않는다.
- 워커 프롬프트를 늘리거나 Superpowers를 고치지 않는다.
- thinking 이벤트를 필터하거나 `stderr.log`를 없애지 않는다.
- 리뷰어 backend, XHigh 정의, 네이티브 리뷰 규칙을 바꾸지 않는다.
- 라이브 모델 호출은 이 변경의 증거가 아니다.

## 접근

고치는 단위는 `scripts/run_worker.py` 한 파일이다. 파일 상단 docstring도
같이 고친다. 지금은 “세션 ID만 읽고 status는 해석하지 않는다”고 적혀 있는데,
이 변경 뒤에는 세션 ID 복사와 도구 필드 추출이 있고, DONE·402·역할 준수
판정만 하지 않는다고 써야 한다. `status`는 읽기 전용을 유지한다.
`run.json`에는 프로세스 정체만 더 정확히 적고, 커지는 도구 목록은 조회
시점에만 만든다.

`status`가 “아무것도 해석하지 않는다”는 말은 이렇게 좁힌다. DONE·402·역할
준수·테스트 통과를 추론하지 않는다. JSON object에서 이미 있는 키를 복사하는
것은 `read_session_id`와 같은 종류의 필드 추출이다.

## session_id는 실행 중에도 기록한다

`run.json.session_id`는 worker 스트림이 보고한 세션 ID다. 첫 비어 있지 않은
문자열만 채택하고 이후 바꾸지 않는다. 키 순서와 스캔 한도는 지금과 같다
(`session_id`, `sessionId`, `chatId`, `chat_id`; 64 KiB / 200줄).

기록 시점:

1. `state: running`과 `pid`를 쓴 직후 한 번 스캔한다.
2. 그 뒤 `wait`를 최대 1초 조각으로 나누고, 아직 `null`이면 조각이 끝날 때마다
   다시 스캔한다. `--timeout 0`은 제한 없이 기다리되, `wait(timeout=0)`은
   지금처럼 쓰지 않는다.
3. `exited` / `timed_out` / `interrupted`에서도 지금처럼 한 번 더 스캔한다.
   이미 값이 있으면 덮어쓰지 않는다.

실행 실패(`launch_failed`)는 스트림이 없으므로 스캔하지 않는다. `status`는
계속 레코드의 `session_id`만 거울로 보여 준다. 레코드가 없는데 스트림에 ID가
있다고 해서 `status.session_id`를 만들지 않는다.

## 래퍼 SIGTERM은 interrupted다

러너는 자식 `wait` 구간에만 SIGTERM 핸들러를 달고, 기존
`KeyboardInterrupt` → `interrupted` 경로와 같게 처리한다. 기록은
`state: interrupted`, 래퍼 exit 130, `error`는 `the controller interrupted
the attempt`, 그때까지 회수한 `session_id`, `ended_at`이다. 프로세스 트리는
죽이지 않는다.

자식이 SIGTERM으로 끝나는 것은 지금과 같다. `state: exited`(또는 타임아웃이면
`timed_out`), `exit_code`는 음수 시그널, 래퍼 exit는 `128 + signal`. 타임아웃이
자식에게 보내는 SIGTERM을 래퍼 인터럽트로 바꾸지 않는다.

SIGKILL은 프로세스 안에서 기록할 수 없다. 그 구멍은 아래 `pid_alive`가 메운다.

## status의 pid_alive

기본 `status` 응답에 `pid_alive`를 더한다. `run.json`에는 쓰지 않는다.

| `run.json.pid` | OS 관측 | `pid_alive` |
| --- | --- | --- |
| 없음 또는 메타데이터 없음 | — | `null` |
| 정수 | `kill(pid, 0)` 성공 또는 `PermissionError` | `true` |
| 정수 | `ProcessLookupError` | `false` |

`state: running`이고 `pid_alive: false`이면 컨트롤러는 그 레코드를 유기된
것으로 본다. `status`가 `run.json`을 고쳐서 `interrupted`로 바꾸지는 않는다.
pid 재사용은 알려진 한계로 남긴다. Windows 분기를 추가하지 않는다.

## 도구 인덱스

기본 `status` 응답에 `tools`를 더한다. `run.json`에는 쓰지 않는다. `--stream`
창과 별개이며, 기본 응답에는 로그 본문이 없다.

```json
"tools": {
  "reads": ["<path>", "..."],
  "searches": [{"pattern": "<str or null>", "path": "<str or null>"}],
  "shells": [{"exit_code": 1, "command": "<truncated>"}],
  "truncated": false
}
```

추출 규칙:

- `worker.jsonl`을 줄 단위로 읽는다. JSON object가 아니거나 `type`이
  `tool_call`이 아니면 건너뛴다.
- `tool_call` 안에서 이름이 `ToolCall`로 끝나는 항목만 본다. 그 밖의 공급자
  모양은 빈 목록이며 오류가 아니다.
- `subtype == started`이고 이름에 `read`가 있으면 `args.path` 문자열을
  `reads`에 넣는다. 먼저 본 순서를 유지하고 중복은 버린다.
- `subtype == started`이고 이름에 `grep` / `glob` / `search`가 있으면
  `pattern` 또는 `globPattern`, `path` 또는 `targetDirectory` /
  `target_directory`를 `searches`에 넣는다.
- `subtype == completed`이고 이름에 `shell`이 있으면 `args.command`와
  `result.exitCode` 또는 `result.success.exitCode` 또는
  `result.failure.exitCode`를 `shells`에 넣는다. 정수만 채택한다.
- 결과 본문(`content`, `stdout`, `stderr`, thinking)은 복사하지 않는다.
- 한도: `reads` 64, `searches` 32, `shells` 32, `command` 200자. 넘치면
  더 넣지 않고 `truncated: true`다. 파일은 끝까지 읽되 목록만 자른다.
- 스트림 파일이 없으면 빈 목록과 `truncated: false`다.

컨트롤러는 이 목록으로 역할 준수를 판정한다. 러너는 플랜 경로를 찾아 FAIL을
매기지 않는다. 새 CLI 플래그는 없다.

2026-09-16 Cursor 스트림은 `readToolCall` / `grepToolCall` / `globToolCall` /
`shellToolCall`이었다. Grok 도구 이벤트 모양은 이 변경에서 측정하지 않는다.

## 계약에 미치는 영향

- `schema_version`은 2. `run.json` 필드 집합은 그대로다. `session_id`의
  **기록 시점**만 바뀐다.
- `status` 기본 키에 `pid_alive`와 `tools`가 추가된다. 응답 64 KiB 상한은
  그대로다. `--stream` 창 한도(기본 2048, 최대 8192)는 그대로다.
- 예전 schema 2 `run.json`( `skill_version` 없음)은 지금처럼 읽힌다.
  `status.session_id`는 레코드 값만 따른다.
- `SKILL.md`는 Implementer의 status 문장만 고친다. 리뷰어·effort·하드 게이트
  장은 그대로다.

함께 고칠 파일은 계약서의 실행·조회 행이다. `run_worker.py`,
`references/dispatch.md`, `tests/products/sddx/test_run_worker.py`,
`tests/products/sddx/test_worker_status.py`, 계약·테스트 안내, CHANGELOG.

## 오류 처리

- 조회는 읽기 전용이다. 죽은 pid를 보고 `run.json`을 고치지 않는다.
- SIGTERM 핸들러는 `wait` 구간 밖에서 원래 처리로 되돌린다.
- 도구 인덱스 파싱 실패는 그 줄을 건너뛴다. 조회 전체를 실패로 만들지 않는다.
- 라이브 공급자 호출, 자동 재시도, 새 실행 스크립트는 없다.

## 테스트

공급자 없는 검사가 필수 증거다. `python3 scripts/verify.py --skill sddx`.

잠글 동작:

- 자식이 init 줄을 쓴 뒤에도 아직 살아 있으면 `run.json.session_id`가 채워지고
  `state`는 `running`이다.
- 값이 채워진 뒤 스트림에 다른 ID가 나와도 바꾸지 않는다.
- 래퍼 SIGTERM은 `interrupted` / 130이고 자식 트리를 죽이지 않는다.
- 자식 SIGTERM은 계속 `exited`와 음수 `exit_code`다.
- `pid_alive`는 살아있는 pid / 없는 pid / `pid: null`을 구분한다.
- 도구 인덱스는 Cursor 모양의 read/grep/shell을 복사하고 결과 본문을 넣지 않는다.
- 1MiB assistant 줄이 있는 기본 `status`는 그 본문을 담지 않는다.
- 알 수 없는 도구 모양과 JSON이 아닌 줄은 빈 목록이다.
- 한도를 넘기면 `truncated: true`다.
- 메타데이터 없는 시도의 `session_id`는 스트림에 ID가 있어도 `null`이다.

## 검증

문서만 바뀌는 문장은 링크와 diff로 확인한다. 라이브 Cursor/Grok 호출은
이 작업의 완료 조건이 아니다. CI Ubuntu `full` 통과를 macOS 실행 증거로
쓰지 않는다.
