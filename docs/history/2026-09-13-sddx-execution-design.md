# SDDx 실행 정리 설계 스펙

상태: 구현 전 설계. 이 문서는 현재 제품 계약을 변경하지 않는다.

기준: SDDx `1.1.1`, 저장소 `db853c0`, 2026-09-13.
근거: [여섯 세션 및 오픈소스 조사](2026-09-13-sddx-orchestration-research.md).
실행 문서: [구현 계획](2026-09-13-sddx-implementation-plan.md).

## 1. 목표와 선택

사용자가 계획과 backend를 지정하면 기존 SDD 흐름으로 진행하되, 태스크 발췌·CLI 실행·현재 상태 복구를 세션마다 다시 만들지 않게 한다. **규칙 정리 + 작은 Python 도구 두 개**를 선택한다.

| 대안 | 판단 |
| --- | --- |
| 문구만 정리 | 현재 상태와 질문은 개선하지만 제목 추출·실행 스크립트 재작성은 남는다. |
| 규칙 + 발췌·실행 도우미 | 관측된 반복을 직접 줄이면서 기존 역할과 검증을 유지한다. 채택한다. |
| 새 오케스트레이터 | 상태 DB, scheduler, replay, 자동 retry의 복잡도가 필요 이상이다. 제외한다. |

Superpowers는 worktree, 태스크 순서, review-package, 수정 라운드, 최종 리뷰를 계속 소유한다. SDDx는 외부 worker에 필요한 입력·실행·증거 확인만 보완한다. 프로세스 helper가 다음 태스크나 리뷰 통과를 결정하지 않는다.

## 2. Global Constraints

- 수정 대상은 `skills/sddx/`, `tests/products/sddx/`, `docs/maintainers/products/sddx/`이며 설계·계획은 `docs/history/`에 둔다.
- Superpowers 원본, 다른 제품, `catalog/`, 전역 호스트 설정은 수정하지 않는다.
- 지원 호스트는 `claude-code`, `codex`이며 backend는 `cursor`, `grok`이다.
- Python 3.11 이상과 표준 라이브러리를 사용하고 새 런타임 의존성은 추가하지 않는다.
- 공급자 호출·라이브 모델 검증은 별도 명시적 승인 없이 실행하지 않는다.
- 비공개 세션 원문·자격 증명·공급자 로그는 커밋하지 않고 테스트에는 합성 자료만 쓴다.
- 기존 SDD 수정 횟수, 네이티브 리뷰, 실제 테스트 exit 확인, 역할 PASS/FAIL/UNVERIFIED 판정을 유지한다.
- 기존 실행 이력과 실패를 보존하며 진행 중 실행을 자동 변환하거나 다시 시작하지 않는다.

## 3. 입력과 재개 — R1

기존 명령 표기 `sddx <plan-file> [cursor|grok|c|g]`를 유지하고 같은 의미의 파일 링크·자연어 지정도 인정한다. 자연어를 별도 Python parser로 만들지 않는다.

backend는 **이번 요청의 명시적 지정 → 같은 실행의 현재 상태 → 한 번 질문** 순으로 정한다. 같은 메시지에 서로 다른 명시적 지정이 있으면 하나만 확인한다. 사용 가능한 CLI가 하나뿐이라는 이유로 선택하지 않는다. 명시적 지정이 있으면 재승인을 요구하지 않는다.

실행 계획 하나에 spec·ADR·참조 문서가 붙어도 계획 하나다. 상위 프로그램 계획에 순서가 정의돼 있으면 이를 따르고, 사용자가 독립 계획들의 순서를 지정했으면 차례로 실행한다. 한 시점에는 활성 계획과 그 원장 하나만 두고 다음 계획 링크를 현재 상태에 기록한다. 하위 계획의 조건을 합치거나 순서를 이름·날짜로 추측하지 않는다.

질문은 경로가 없거나 유효하지 않은 경우, 독립 계획의 순서가 불분명한 경우, 병행 작업과 소유 파일·인터페이스가 충돌하는 경우에 한정한다. 재개에서는 현재 상태를 실제 Git HEAD·미커밋 변경·실행 상태와 대조한다.

사용자가 backend 변경을 지시하면 이전 실행 종료와 필요한 cleanup을 확인하고 다음 시도를 시작한다. 새 backend에는 기존 공급자 세션 ID를 전달하지 않는다. 태스크, 수정 횟수, 미해결 지적, 사용자 승인 범위는 이어받는다.

## 4. 정확한 태스크 발췌 — R2

새 `scripts/extract_task.py`는 **완전한 ATX 제목 문자열 하나**를 받아 해당 절의 원문 byte를 반환한다. SDDx dispatch에서 제목을 숫자로 변환한 임시 계획을 만들지 않는다. SDD의 브리프 구성과 리뷰 절차를 복제하지 않고 본문 발췌만 대체한다.

```text
python3 <skill-root>/scripts/extract_task.py <plan-file> --heading "Task P1: 상태 저장" --output <section-file>
```

계약:

- `extract_task(plan: bytes, heading: str) -> bytes`; 실패는 `ValueError`다.
- `heading`은 `#` 표시를 제외한 전체 제목이다. `Task 1`, `Task P1`, `Task U1`, `Task F1`, `S01`, `P1-T1`을 같은 규칙으로 처리한다.
- 1–6단계 ATX heading을 인식한다. Markdown의 선택적 닫는 `#`와 앞쪽 0–3칸 공백은 제목 비교 때만 제거한다. 대소문자·ID·본문은 바꾸지 않는다.
- backtick/tilde fenced code 안의 가짜 제목은 무시한다. 다음 동일하거나 더 높은 단계 제목 직전에서 끝내고 하위 제목은 포함한다.
- 제목이 없거나 중복되거나 본문이 비어 있으면 실패한다. Setext heading은 지원하지 않으며 유사 제목을 추측하지 않는다.
- 성공 시 원문의 개행과 Unicode를 보존한다. 기존 output은 덮어쓰지 않는다. CLI exit는 성공 0, 입력/출력 오류 2, 절 선택 오류 3이며 실패 시 부분 output을 남기지 않는다.

컨트롤러는 발췌 본문에 적용되는 전역 제약, 확정 인터페이스, 명시 소스·테스트 경로, `Search paths`, 실제 검증 명령, host 전용 검증을 보충한다. 완결성은 추출기의 성공 여부와 별도로 확인한다. worker에 전체 계획을 참조로 주지 않는다.

## 5. 실행 기능 확인과 Cursor 기본값 — R3

기존 `resolve_backend.py`를 확장한다. identity 검증과 backend alias는 유지한다. 알려진 실제 flag만 선택하며 CLI가 없거나 필수 기능이 없으면 사유를 반환한다.

기존 JSON 필드는 유지하고 두 필드를 추가한다.

```text
launch: {cwd_flag: str, prompt_flag: str | null,
         effort_flag: str | null, output_format: str} | null
model_ids: list[str]
```

- Grok: cwd/rules/sandbox/no-plan/no-subagents/disable-web-search와 명시적 resume을 유지한다. `prompt_flag`는 `--prompt-file` 우선, 없으면 확인된 `--single` 또는 `-p`다. effort flag도 확인된 alias를 사용한다. 출력은 `streaming-messages-json` 지원을 확인한다.
- Cursor: `argv_prefix`는 확인된 print flag, `--trust`, `--auto-review`, `--sandbox enabled`를 포함하고 `--force`/`--yolo`를 포함하지 않는다. `stream-json`, workspace/cwd, model, resume 지원을 확인한다.
- 필수 flag·출력 형식이 없으면 `available=false`, `reason=missing_flags`다. 더 넓은 권한이나 비구조화 출력으로 대체하지 않는다.
- Cursor 모델은 읽기 전용 모델 목록에서 확인한 정확한 Grok ID를 `model_ids`로 제공한다. 조회 후보는 help의 실제 선언에서 만든다. `models`는 subcommand로 선언됐을 때만, `--list-models`는 option으로 선언됐을 때만 넣으며 둘 다 있으면 그 순서다. 설명 본문의 단어만으로 후보를 만들거나 선언되지 않은 명령을 시험하지 않는다. 조회 결과는 exit code·stdout·stderr를 분리하고 exit 0의 stdout에서만 ID를 읽는다. 실패 출력이나 stderr의 모델명은 채택하지 않는다. 첫 조회에서 유효한 ID를 얻지 못했을 때만 다음 확인된 후보를 시도한다. 후보가 없으면 조회 호출 없이 `no_grok_model`이다. 컨트롤러가 확인된 ID 중 하나를 지정하며, 이름만 비슷한 모델이나 임의의 effort suffix를 만들지 않는다. ID를 확인하지 못하면 `no_grok_model`이다.
- Cursor에 별도 effort 제어가 확인되지 않으면 `effort_flag=null`이다. 요청한 High/XHigh와 실제 적용을 구분하고 적용값을 `unknown`으로 기록한다. backend나 모델을 자동 변경하지 않는다.
- unavailable 응답의 `launch`는 null, `model_ids`는 빈 목록이다. 기존 `reason`의 의미를 유지한다.

Auto-review는 headless 상황에서 추가 권한을 요구할 수 있다. 그 경우 차단 또는 미완료로 기록하고 원인을 확인한다. 이를 해결하려고 `--force`를 자동 추가하지 않는다. 플래그 확인은 OS 격리 성공, 저장소 밖 읽기 차단, 모델 동작을 증명하지 않는다.

## 6. 작은 실행·조회 도구 — R4

새 `scripts/run_worker.py`는 `run`, `status` 두 subcommand만 제공한다. scheduler, 자동 retry, detach, backend failover, tool 결과 의미 판정, 프로세스 트리 관리자를 만들지 않는다.

```text
run_worker.py run --backend grok --worktree <worktree> --brief <brief-file>
  --attempt-dir <new-attempt-dir> --effort high --sandbox-profile <prepared-profile>
run_worker.py run --backend cursor --worktree <worktree> --brief <brief-file>
  --attempt-dir <new-attempt-dir> --effort high --model <confirmed-grok-id> --resume <known-id>
run_worker.py status --attempt-dir <attempt-dir>
run_worker.py status --attempt-dir <attempt-dir> --stream stdout --offset 0 --max-bytes 2048
```

### 실행의 소유 범위

`attempt-dir`는 해당 worktree의 `.superpowers/` 아래 새 경로다. 부모가 실제 worktree 안에 있는지 확인하고 symlink 우회와 기존 디렉터리는 거절한다. 시도 이름은 기존 SDD task/round 이름을 이용한다. 자동 번호 증가나 전역 ID 서비스는 필요 없다.

runner는 resolver 결과로 argv를 만들고 worker rules와 brief/report 경로를 넣은 dispatch를 생성한다. `--continue`, `--worktree`, `--plugin-dir`, 추가 MCP 승인을 넣지 않는다. stdout/stderr를 새 파일에 직접 연결하고 프로세스 종료를 기다린다. Python의 `shell=True`나 동적 shell 명령문을 사용하지 않으며 Windows 실행 wrapper는 아래 계약을 따른다. 표준 입력은 닫아 암묵적 승인 입력을 보내지 않는다. 환경 값은 프롬프트나 메타데이터에 기록하지 않는다.

Windows `.cmd`/`.bat` 실행은 resolver의 command wrapper 한 곳에서 처리한다. 기존 `_command`는 `list2cmdline` 결과를 `cmd.exe /c`에 넘기므로 임의 인자의 정확한 전달이 보장된 것으로 간주하지 않는다. resolver 단계에서 필요한 전송 수정을 하고 공백·Unicode·따옴표·shell 메타문자를 합성 실행으로 검증한 뒤 runner가 그 계약을 사용한다. 검증되지 않은 인자 조합을 문자열 보간으로 우회하지 않는다. argv 전송 오류는 launch 실패이며 더 넓은 실행 방식으로 재호출하지 않는다.

`--resume`은 확인된 동일 backend 세션 ID가 있을 때만 값과 함께 사용한다. 알 수 없는 ID를 파일명이나 최근 세션에서 추측하지 않는다. ID가 없으면 기존 SDD 방식으로 새 worker에 이전 보고서와 확정된 맥락을 제공하며, 이때도 새 attempt를 만든다.

저장 파일은 다음 여섯 개다.

| 파일 | 역할 |
| --- | --- |
| `brief.md` | 이번 시도에 전달한 완결된 브리프 사본 |
| `dispatch.md` | 이번 시도의 지시 원문 |
| `worker.jsonl` | CLI stdout 원문. 잘못된 JSON도 버리지 않는다. |
| `stderr.log` | CLI stderr 원문 |
| `run.json` | runner가 관측한 프로세스 상태와 실제 exit |
| `report.md` | worker가 작성할 보고서. runner는 대신 작성하지 않는다. |

`run.json`의 `schema_version`은 1이다. 나머지 필수 필드는 `backend`, `identity`, `model`, `worktree`, `attempt_dir`, `brief_sha256`, `resume_id`, `requested_effort`, `configured_effort`, `state`, `pid`, `exit_code`, `started_at`, `ended_at`, `error`다. 모르는 값은 null로 둔다. `model`과 `configured_effort`는 CLI에 명시한 값이며 모델 내부의 실제 적용을 입증하지 않는다. `state`는 `starting`, `running`, `exited`, `launch_failed`, `interrupted` 중 하나다. 이는 태스크 상태가 아니다.

메타데이터 갱신은 같은 디렉터리의 임시 파일과 atomic replace로 한다. raw 파일은 잘라 쓰거나 이전 시도에서 이어 쓰지 않는다. 프로세스가 멈췄는지 확인하지 못한 옛 `running` 기록은 마지막 관측값일 뿐이다. `status`는 PID 존재만으로 종료나 성공을 추측하지 않는다.

wrapper exit는 정상적으로 기다린 worker의 exit를 따른다. POSIX signal 종료는 `128 + signal`로 반환하되 `run.json.exit_code`에는 실제 음수 returncode를 보존한다. launch 실패는 2, 정상적으로 처리한 controller interrupt는 130이다. 중단 시 exit를 회수하지 못했다면 null로 남기고 성공으로 바꾸지 않는다. process exit 0과 clean DONE은 별개다.

### Grok 준비·정리

기존 `prepare_grok_sandbox.py`를 그대로 재사용한다. 컨트롤러가 기존 dispatch처럼 **prepare → run → worker와 관련 작업의 종료 확인 → cleanup** 순서를 지킨다. runner에는 prepare가 반환한 profile만 전달한다. 같은 계획의 journal 경로는 고정하고 정리가 끝나기 전 다음 worker를 시작하지 않는다.

runner는 프로세스 트리의 종료를 보장하지 않으므로 sandbox를 자동으로 정리하지 않는다. root CLI exit만으로 자식 작업 종료를 추정하지 않는다. 중단·host 재시작 후 종료가 불명확하면 원문과 journal을 보존하고 기존 host 실행 도구로 확인한다. 임의의 PID에 신호를 보내거나 journal을 삭제해 재실행하지 않는다. 이것은 새 복구 엔진을 만들지 않고 기존 안전한 cleanup 경계를 유지하는 선택이다.

### 조회와 증거

기본 `status`는 run 메타데이터, 로그 byte 크기, 보고서 존재 여부만 반환한다. 로그 본문을 자동 출력하지 않는다. `--stream stdout|stderr --offset N --max-bytes N`을 주면 해당 원문의 byte 구간을 읽는다. 기본 구간은 2,048 byte, 최대 8,192 byte다. JSON 직렬화된 응답은 64 KiB 이내로 제한한다.

구간 응답은 `stream`, `offset`, `next_offset`, `size`, `preview`, `has_more`, `decode_errors`, `pending_bytes`를 포함한다. `next_offset`은 실제 소비한 byte 위치다. 범위를 벗어난 offset은 오류이며 처음부터 몰래 재조회하지 않는다. UTF-8 경계에서 잘린 마지막 문자 byte는 다음 구간으로 남기고, 잘못된 byte는 표시하되 원본은 보존한다. 긴 단일 JSON 행도 같은 상한을 적용한다.

로그는 자라는 파일이므로 이번 조회의 EOF를 최종 입력 종료로 간주하지 않는다. 한 번 조회할 때 얻은 파일 크기 안에서만 읽고 decoder는 `final=False`를 사용한다. 미완성 UTF-8 suffix의 길이(0–3)를 `pending_bytes`로 반환하고 그 byte는 소비하지 않는다. 임시 EOF에 그 suffix만 있으면 빈 preview·같은 next_offset·`has_more=true`·`decode_errors=false`로 반환한다. 반면 이미 뒤에 byte가 있는데 `max_bytes`가 너무 작아 첫 문자조차 읽지 못하면 입력 오류다. 실제 로그 기록이 끝난 뒤에도 미완성 suffix는 그대로 남겨 원문 위치로 확인하며, 성공이나 완전한 증거로 바꾸지 않는다. 컨트롤러는 suffix를 기다리며 같은 조회를 짧게 반복하지 않는다.

이 미리보기는 JSON 이벤트나 호출·결과 한 쌍의 완결성을 보장하지 않는다. 공급자 session ID, call ID, 테스트 exit는 컨트롤러가 해당 원문을 확인해 기록한다. 첫 구현에서는 전체 공급자 이벤트 parser와 자동 ID 인덱스를 만들지 않는다. 크기가 제한된 요약이나 호출 수만으로 역할 PASS를 부여하지 않는다.

조회는 읽기 전용이며 worker 실행, 파일 갱신, 결제 상태 확인, retry를 하지 않는다. 기본 대기는 host의 실행 job wait를 사용한다. 새 결과가 없으면 동일 로그를 반복 출력하지 않는다.

## 7. 원장 한 곳에서 현재 상태 유지 — R5

기존 `progress.md`의 첫 줄 `# SDD ledger — plan: <plan file path>`를 그대로 보존하고, 바로 아래에 `<!-- sddx:current:start -->` / `<!-- sddx:current:end -->` 블록 하나를 두어 현재 사실을 **교체**한다. 계획 식별자는 블록 밖에 두며 원장의 첫 줄을 가리지 않는다. 기존 SDD가 읽는 `Task <ID>: complete`와 fix-round 이력도 보존한다. 컨트롤러가 기존 원장 편집 방식으로 갱신하며 별도 state writer나 DB를 만들지 않는다.

필드는 활성 계획·다음 계획, backend와 선택 근거, worktree/HEAD, task·fix round·attempt 경로, 확인된 worker session ID, 미해결 지적 링크, 승인된 작업 범위, host 검증 대기, 다음 행동, 증거 링크다. 리뷰 host/model/effort의 확인 정보와 제한은 최초 한 번 기록하고 바뀌었을 때만 갱신한다.

권장 분량은 약 30줄이다. 긴 미해결 내용은 상세 기록에 링크하되 현재 상태에서 누락하지 않는다. 같은 역할의 `controller-current-state.md`와 `controller-recovery.md`를 새로 만들지 않는다. 아래 이력에는 결정·위반·수정·전환을 한 번씩 남기고, 같은 설명을 리뷰마다 복사하지 않는다.

`run.json`은 한 시도의 프로세스 사실만 소유한다. 사용자 승인, 태스크 완료, 리뷰, 다음 계획은 원장이 소유한다. 둘을 양방향 동기화하는 체계는 만들지 않는다.

## 8. 오류·host 검증·리뷰 — R6

- helper의 자동 재시도는 0회다. 확인된 402 잔액 소진, 인증·권한 실패는 필요한 조건 변경을 현재 상태에 적고 같은 조건으로 재실행하지 않는다. 소스·테스트 본문의 숫자 `402`를 공급자 오류로 오인하지 않는다.
- 일시 오류도 무조건 재실행하지 않는다. 컨트롤러가 기존 SDD ruling으로 원인·변경 조건·재실행 근거를 남긴다. 수정 라운드는 기존 상한을 유지하며 backend 변경이나 context 보충으로 초기화하지 않는다.
- worker의 로컬 검증과 host 전용 검증을 브리프에서 구분한다. host 검증이 남으면 기존 `NEEDS_CONTEXT` 또는 `BLOCKED` 보고에 항목을 명시한다. host가 결과를 채우고 코드 변경이 필요할 때만 worker에 다시 보낸다. 새 worker 상태를 추가하지 않는다.
- report-only 정정은 증거 정정 기록으로 처리하고 코드 수정·새 커밋·전체 재리뷰를 강요하지 않는다. 실제 역할 위반 기록은 사과나 후속 성공으로 지우지 않는다.
- 기존 검증은 관련 소스·테스트·환경이 같은 경우에만 재사용한다. 코드·테스트·환경이 바뀌었거나 이전 검사가 결함을 놓쳤으면 필요한 새 검사를 한다. 별도 receipt 시스템은 만들지 않는다.
- 리뷰 dispatch는 실제 사용 방식과 근거를 기록한다. 상속 effort가 이미 XHigh 이상이면 그 사실로 충족하며 정의 부재를 반복 경고하지 않는다. 확인되지 않은 agent 이름이나 적용 effort를 실제 사용한 것처럼 적지 않는다.

## 9. 두 호스트 적용 — R7

| 항목 | Claude Code | Codex |
| --- | --- | --- |
| 호출 | `/sddx` | `$sddx` |
| backend 확인이 필요한 경우 | 사용 가능한 AskUserQuestion | 사용 가능한 질문 도구, 없으면 짧은 텍스트 질문 |
| 발췌·worker 실행·로그 조회 | 같은 제품 Python scripts | 같은 제품 Python scripts |
| 리뷰 | native Task, 모델 인자 없이 상속 | native spawn_agent, 모델 상속 |
| XHigh | 이미 충족하면 상속, 추가 승급 필요 시 설치된 정의 사용 | 이미 충족하면 상속, 그 외 host가 실제 제공하는 수단만 사용 |
| 승급 수단 없음 | 제약을 한 번 기록하고 기존 fallback | 제약을 한 번 기록하고 기존 fallback |

공통 제품 소스가 바뀌면 두 호스트의 새 실행에 동일하게 적용된다. 실제 로드 경로가 해당 제품을 가리키는지 확인하며 다른 위치의 오래된 복사본을 자동으로 고치지 않는다. 이미 실행 중인 컨텍스트는 자동 갱신된 것으로 간주하지 않는다. 새 실행에서 적용하고 기존 실행은 기록과 프로세스를 확인한 뒤 명시적으로 재개한다.

Windows 지원을 POSIX 코드로 대체하지 않는다. `.cmd` 실행과 `fchmod`가 없는 환경의 기존 회귀 검사를 유지한다. 로컬 macOS 검사를 Windows 또는 두 호스트의 실제 모델 동작 증거로 확대하지 않는다.

## 10. 수용 기준과 배포 — R8

| ID | 수용 기준 | 증거 |
| --- | --- | --- |
| AC1 | 명시적 backend·기존 선택 재사용, spec+plan 구분, 명시된 여러 계획 순서 유지 | 양 호스트 행동 시나리오. 문구 검사와 모델 행동 결과는 별도 기록 |
| AC2 | 여섯 제목 형식, fence, 중복, 빈 절, 경계, 개행 보존, 덮어쓰기 거절 | 합성 Markdown 단위 테스트 |
| AC3 | Cursor force/yolo 제거, 필요한 기능 없을 때 차단, 실제 alias·성공 stdout의 모델 ID만 사용, Windows 인자 보존 | fake CLI probe/resolver/argv 테스트 |
| AC4 | 시도 증거 보존, 실제 exit 기록, 명시적 resume, launch 실패·중단의 미완료 유지, 실제 child에 backend 제약 전달 | fake CLI 프로세스 및 child argv 테스트 |
| AC5 | 기본 조회에 원문 없음, byte 구간 상한·offset·자라는 로그의 Unicode 처리, 조회 시 실행 0회 | 거대 단일 행·부분 UTF-8 append·반복 status 테스트 |
| AC6 | 첫 줄 계획 식별자와 완료/round 이력 보존, 현재 블록 하나, backend 전환·압축 뒤 현재 승인/미해결 내용 유지 | 합성 원장 재개 시나리오 |
| AC7 | 402 동일 조건 retry 0회, host 검증으로 인한 불필요한 worker 호출 없음, exit와 PASS 분리 | fake CLI invocation 수 + 행동 시나리오 |
| AC8 | 두 호스트 지침, Windows 회귀, 기존 역할/리뷰 경계 유지, 미측정 표기 | 제품 검사·전체 오프라인 검사·문서 대조 |

제품 구현 시 목표 버전은 **2.0.0**이다. 필수 Cursor 기능과 기본 실행 계약이 바뀌므로 저장소 [버저닝 규칙](../maintainers/repository/versioning.md)에 따라 MAJOR로 잡는다. 공개 태그가 아직 없는 제품이어도 현재 개발 버전의 계약 변경을 숨기지 않는다. 이 설계 문서 작성만으로 버전을 올리지는 않는다.

구현 후 제품·전체 오프라인 검사를 한 번씩 통과시키고, 추가 승인이 있을 때만 양 호스트와 backend 조합의 실제 실행을 측정한다. 실제 Cursor 승인·격리, Claude 정의 로딩과 적용 effort가 확인되지 않은 항목은 `not_measured`로 남긴다. 기존 릴리스 문서의 라이브 로딩 확인 요구도 유지하며, 확인 없이 공개 릴리스 완료를 선언하지 않는다.

출시는 별도 요청 범위다. 이 계획은 태그·Release·카탈로그 채택·전역 설치 교체·기존 원장 자동 마이그레이션을 수행하지 않는다.
