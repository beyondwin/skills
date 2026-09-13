# SDDx Execution Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This document does not start implementation. Use SDDx only if the user requests an external implementer for that future execution.

**Goal:** 기존 SDD를 유지하면서 태스크 발췌·worker 실행 스크립트 재작성과 재개 시 중복 조회를 없앤다.

**Architecture:** SDDx에 정확한 제목 발췌와 CLI 실행·조회 도우미를 추가한다. 현재 상태는 기존 progress 원장이 소유하고 실행 도우미는 한 시도의 프로세스 사실만 저장한다. backend·리뷰 host 차이는 기존 overlay에서 처리한다.

**Tech Stack:** Python 3.11+, 표준 라이브러리, unittest, 기존 Git fixture, Markdown.

**Spec:** [2026-09-13-sddx-execution-design.md](2026-09-13-sddx-execution-design.md)

**Research:** [2026-09-13-sddx-orchestration-research.md](2026-09-13-sddx-orchestration-research.md)

**Status:** 구현 전. 아래 checkbox는 모두 미실행이다. 이번 문서 작성에서 제품 코드·테스트·버전은 바꾸지 않는다.

## Global Constraints

- 수정 대상은 `skills/sddx/`, `tests/products/sddx/`, `docs/maintainers/products/sddx/`이며 설계·계획은 `docs/history/`에 둔다.
- Superpowers 원본, 다른 제품, `catalog/`, 전역 호스트 설정은 수정하지 않는다.
- 지원 호스트는 `claude-code`, `codex`이며 backend는 `cursor`, `grok`이다.
- Python 3.11 이상과 표준 라이브러리를 사용하고 새 런타임 의존성은 추가하지 않는다.
- 공급자 호출·라이브 모델 검증은 별도 명시적 승인 없이 실행하지 않는다.
- 비공개 세션 원문·자격 증명·공급자 로그는 커밋하지 않고 테스트에는 합성 자료만 쓴다.
- 기존 SDD 수정 횟수, 네이티브 리뷰, 실제 테스트 exit 확인, 역할 PASS/FAIL/UNVERIFIED 판정을 유지한다.
- 기존 실행 이력과 실패를 보존하며 진행 중 실행을 자동 변환하거나 다시 시작하지 않는다.

## 실행 순서와 검증 원칙

Task 1 → 2 → 3 → 4 → 5 → 6 순서로 실행한다. 새 dependency, scheduler, retry 엔진, provider 이벤트 parser는 만들지 않는다. Task 3과 4는 같은 runner 파일을 차례로 수정하므로 동시에 실행하지 않는다.

작업 시작에 Git 상태와 제품 계약을 읽고 기존 변경을 보존한다. 아래 경로는 저장소 루트 기준이다. 새 task brief에는 이 문서의 Global Constraints와 선행 인터페이스를 포함한다.

코드 단계는 해당 동작을 깨뜨리는 테스트의 RED를 확인한 뒤 구현한다. 기존 테스트 함수 본문을 복사한 문자열 검사만으로 행동 개선을 입증하지 않는다. 변경 뒤 필요한 범위만 다시 검사한다. 문구만 수정하는 단계에는 억지 단위 테스트를 추가하지 않고 시나리오·기존 계약·diff를 확인한다.

## Task 1: 정확한 제목의 태스크 절 발췌

**Spec:** R2 / AC2.

**Files:**

- Create: `skills/sddx/scripts/extract_task.py`
- Create: `tests/products/sddx/test_extract_task.py`

**Interfaces:**

- Consumes: UTF-8 Markdown bytes와 `#`를 제외한 완전한 제목 문자열.
- Produces: `extract_task(plan: bytes, heading: str) -> bytes`, `main(argv: list[str] | None = None) -> int`.
- Errors: 절 없음·중복·빈 본문은 `ValueError`; CLI 절 오류 3, 파일/인자 오류 2, 성공 0.

- [ ] **Step 1: 경계 회귀 테스트를 작성한다.** 기존 제품 테스트처럼 scripts 경로를 테스트 import 경로에 추가한다. 핵심 표본은 다음과 같다.

```python
import unittest
from extract_task import extract_task

class ExtractTaskTests(unittest.TestCase):
    def test_fenced_heading_does_not_end_task(self):
        section = (
            "## Task P1: 저장\r\n"
            "요구사항\r\n```md\r\n## Task P2: 가짜\r\n```\r\n"
            "### 검증\r\n검증 내용\r\n"
        ).encode("utf-8")
        plan = b"# Plan\r\n" + section + "## Task P2: 다음\r\n다음 내용\r\n".encode("utf-8")
        self.assertEqual(extract_task(plan, "Task P1: 저장"), section)
```

같은 unittest 파일에 여섯 제목 형식, `P1`/`P10` 구분, tilde fence, 닫는 `#`, 상위 제목에서 종료, 마지막 절, 중복 제목, 빈 본문, 제목 없음, Unicode·CRLF, 이미 존재하는 output을 추가한다. 실패한 CLI 호출은 output을 만들지 않아야 한다.

- [ ] **Step 2: RED를 확인한다.**

Run: `python3 -m unittest discover -s tests/products/sddx -p test_extract_task.py -v`

Expected: 새 module/함수가 없어 실패. 이후 테스트가 해당 경계 오류를 실제로 잡는지 확인한다.

- [ ] **Step 3: byte 경계를 보존하는 작은 scanner를 구현한다.**

`splitlines(keepends=True)`로 원문을 유지하고, fence 밖에서만 ATX heading을 수집한다. fence의 문자와 열린 길이를 보관하고 같은 문자·충분한 길이의 닫힘만 인정한다. 절 선택은 제목 완전 일치다. 핵심 선택 동작은 다음 형태다.

```python
def select_bounds(headings, requested, line_count):
    matches = [(line, level) for line, level, title in headings if title == requested]
    if len(matches) != 1:
        raise ValueError("expected exactly one matching heading")
    start, level = matches[0]
    end = next((line for line, depth, _ in headings if line > start and depth <= level), line_count)
    return start, end
```

`extract_task`는 선택한 제목 다음에 공백 이외의 본문이 있는지 확인하고 원본 line bytes를 join한다. CLI는 추출·검증 완료 후에만 `open(..., "xb")`로 output을 쓴다. 쓰기 실패 시 이번 호출에서 새로 만든 부분 파일만 제거한다. 기존 파일을 지우지 않는다.

- [ ] **Step 4: GREEN과 diff를 확인한다.** 위 unittest 명령과 `git diff --check`를 실행한다. Superpowers 추출기나 계획 제목을 수정하지 않았는지 확인한다.
- [ ] **Step 5: 이 단계만 커밋한다.**

```bash
git add skills/sddx/scripts/extract_task.py tests/products/sddx/test_extract_task.py
git commit -m "feat(sddx): extract task sections by exact heading"
```

## Task 2: 실제 지원 기능으로 backend 실행 계약 확정

**Spec:** R3 / AC3, AC8.

**Files:**

- Modify: `skills/sddx/scripts/resolve_backend.py` — capability 확인, probe 결과 분리, available/unavailable 응답, Cursor prefix, 정확한 Windows 인자 전달에 필요한 `_command` 수정.
- Modify: `tests/products/sddx/test_resolve_backend.py` — fake help/model 목록의 exit/stdout/stderr, alias, Windows command wrapper의 특수문자 왕복 회귀.

**Interfaces:**

- Consumes: 기존 `_run(executable: str, arguments: list[str], timeout: float = 5.0) -> str`, `_command(executable: str, arguments: list[str]) -> list[str]`.
- Produces: 기존 `resolve(backend_arg: str) -> dict[str, Any]`; 기존 6개 필드에 스펙 R3의 `launch`, `model_ids`를 추가한다.
- `launch`의 keys는 `cwd_flag`, `prompt_flag`, `effort_flag`, `output_format`으로 고정한다. Cursor `prompt_flag`와 `effort_flag`는 null이다.
- Produces: `_probe(executable: str, arguments: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str] | None`. 결과에 returncode/stdout/stderr를 보존하며 OSError/timeout은 None이다. `_run`의 기존 문자열 반환 계약은 유지하고, 모델 목록 판정만 `_probe` 결과를 사용한다.
- Produces: 내부 `model_list_commands(help_text: str) -> list[list[str]]`. 실제 subcommand 선언의 `models`, 실제 option 선언의 `--list-models`만 그 순서로 반환한다. 둘 다 없으면 빈 목록이며 설명 본문의 단어는 후보가 아니다.
- Produces: 같은 `_command` signature로 Windows에서도 실제 지원 인자가 child에 그대로 전달되는 계약. Task 3에 wrapper 수정을 미루지 않는다.

- [ ] **Step 1: fake CLI로 RED를 만든다.** 기존 fixture의 help에 실제로 필요한 출력 형식·Cursor auto-review/sandbox를 추가하고, 각각 없는 fixture도 유지한다. 실제 공급자 worker는 실행하지 않고 읽기 전용 probe용 fake 프로세스로 resolver가 내보낼 값을 검사한다.

```python
def assert_cursor_contract(resolved):
    assert resolved["available"] is True
    argv = resolved["argv_prefix"]
    assert "--force" not in argv and "--yolo" not in argv
    assert "--auto-review" in argv
    assert argv[argv.index("--sandbox") + 1] == "enabled"
    assert resolved["launch"]["output_format"] == "stream-json"
    assert resolved["launch"]["effort_flag"] is None
    assert resolved["model_ids"] == ["grok-4"]
```

Grok `--prompt-file`/`--single`/`-p`, `--reasoning-effort`/`--effort`, Cursor print/cwd alias, 잘못된 identity, `agent` 제외, Grok 모델 없음, unavailable 필드도 검사한다. 모델 목록의 안내문에 `grok` 단어만 있는 경우를 ID로 채택하지 않는다.

모델 목록 fixture는 명령별 returncode/stdout/stderr를 지정한다. `exit 7 + stdout grok-4`, `exit 0 + stderr에만 grok-4`, 첫 alias 실패 후 확인된 두 번째 alias 성공, 첫 성공 뒤 두 번째 alias 호출 0회를 검사한다. 실패 출력만으로 `available=true`가 되면 실패다.

help가 `models`만 선언한 경우, `--list-models`만 선언한 경우, 둘 다 선언하지 않은 경우를 각각 만든다. 선언하지 않은 명령은 호출 0회여야 하며 마지막 경우는 목록 조회도 0회·`no_grok_model`이다. fake CLI가 help와 무관하게 두 alias를 항상 허용하지 않도록 고친다. 지원되지 않는 위치 인자를 받으면 worker invocation marker를 남기는 fixture도 두어, 이 marker가 모든 resolver 검사에서 0임을 확인한다. 두 후보가 모두 선언된 fixture에서는 기존 fallback·stderr·비0 exit 검사를 유지한다.

같은 테스트 파일에서 Windows native synthetic `.cmd`의 child argv를 비교한다. 공백·Unicode·따옴표·`&`·`%SYNTHETIC_VALUE%`를 포함한 인자를 그대로 받아야 하고 추가 명령 marker나 환경 치환이 없어야 한다. 실제 `.cmd` 왕복은 Windows에서 실행하며 다른 OS의 정적 wrapper 검사는 별도다. 합성 환경 값만 사용한다.

- [ ] **Step 2: RED를 확인한다.**

Run: `python3 -m unittest discover -s tests/products/sddx -p test_resolve_backend.py -v`

Expected: 기존 force prefix와 새 필드 부재 때문에 새 검사가 실패한다.

- [ ] **Step 3: resolver가 사용 가능한 alias와 형식을 한 번 결정하게 한다.** 도움말에서 option 선언을 읽고 지원 값까지 확인한다. 없는 flag를 고정 argv로 만들지 않는다. 모델 목록은 알려진 ID 행만 받아들이고 불명확하면 거절한다. 필요한 Cursor prefix는 다음과 같다.

```python
argv = [executable, print_flag, "--trust", "--auto-review", "--sandbox", "enabled"]
launch = {
    "cwd_flag": cwd_flag,
    "prompt_flag": None,
    "effort_flag": None,
    "output_format": "stream-json",
}
```

위 지역 변수는 기존 identity/help 분기에서 확인한 실행 파일·print/cwd alias다. Grok은 기존 prefix와 준비 profile 교체 방식을 유지하고 prompt/effort/output 정보를 반환한다. models 명령이 성공해 ID를 얻었으면 같은 정보를 얻기 위한 다른 alias 명령을 불필요하게 반복하지 않는다.

모델 목록은 `_probe`의 exit 0 stdout만 파싱한다. 기존 `_run`을 이용해 stderr와 합친 문자열에서 성공을 추정하지 않는다. `model_list_commands`는 앞 단계의 option/subcommand 선언 확인을 이용하며 명령을 실행해 지원 여부를 추측하지 않는다. 최소 판정 흐름은 다음과 같다. `parse_model_ids(text: str) -> list[str]`는 같은 파일 내부에서 확인된 모델 ID 행만 읽는다.

```python
model_ids = []
for arguments in model_list_commands(help_text):
    probe = _probe(executable, arguments)
    if probe is not None and probe.returncode == 0:
        model_ids = parse_model_ids(probe.stdout)
        if model_ids:
            break
```

기존 `_command`의 `list2cmdline`은 `cmd.exe` 메타문자 보존을 입증하지 않는다. 새 왕복 테스트가 실패하면 이 단계의 `_command`와 해당 fixture에서 필요한 전송을 수정한다. `.exe` 직접 실행과 기존 probe용 wrapper 사용은 유지한다. runner에서 별도의 shell 우회 경로를 만들거나 테스트를 단순 argv 모양 검사로 낮추지 않는다.

- [ ] **Step 4: GREEN을 확인한다.** 위 unittest 명령을 실행한다. 기존 Windows `_command`와 fake `.cmd` 테스트를 삭제하거나 POSIX 전용으로 바꾸지 않는다.
- [ ] **Step 5: 이 단계만 커밋한다.**

```bash
git add skills/sddx/scripts/resolve_backend.py tests/products/sddx/test_resolve_backend.py
git commit -m "fix(sddx): resolve supported worker execution flags"
```

## Task 3: 증거를 보존하는 공통 worker 실행

**Spec:** R4의 실행·Grok 준비/정리 / AC4, AC7.

**Files:**

- Create: `skills/sddx/scripts/run_worker.py`
- Create: `tests/products/sddx/test_run_worker.py`
- Read: `skills/sddx/scripts/prepare_grok_sandbox.py`, `skills/sddx/references/worker-prompt.md`, `skills/sddx/references/dispatch.md`.

**Interfaces:**

- Consumes: Task 2 `resolve(backend_arg: str) -> dict[str, Any]`, `_command(executable: str, arguments: list[str]) -> list[str]`.
- Produces: `RunOptions`, `build_argv(resolved: dict[str, Any], options: RunOptions, dispatch: Path, rules: str) -> list[str]`, `run_worker(options: RunOptions) -> int`, `main(argv: list[str] | None = None) -> int`.
- Grok prepare/cleanup는 기존 `prepare(worktree: Path, state: Path) -> str`, `cleanup(worktree: Path, state: Path) -> None`이며 이 단계는 그 동작을 수정하지 않는다.

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class RunOptions:
    backend: str
    worktree: Path
    brief: Path
    attempt_dir: Path
    effort: str
    model: str | None = None
    resume_id: str | None = None
    sandbox_profile: str | None = None
```

- [ ] **Step 1: 실제 subprocess를 쓰는 합성 테스트를 작성한다.** 임시 Git worktree와 `.superpowers` 아래 새 attempt를 만들고, resolver만 fake CLI로 연결한다. fixture는 계정·네트워크·기존 CLI를 사용하지 않는다. 다음 코드의 exit-7 worker와 같은 표본을 임시 실행 파일로 사용한다.

```python
import json
import sys

sys.stdout.write(json.dumps({"type": "assistant", "text": "reported success"}) + "\n")
sys.stderr.write("synthetic failure\n")
raise SystemExit(7)
```

기대 결과는 helper exit 7, `run.json.exit_code == 7`, `state == "exited"`, 원문 stdout/stderr 보존, report를 helper가 생성하지 않음이다. 별도 fixture에는 잘못된 JSON, 402 오류, 지연 종료, 큰 stdout/stderr, 실행 전 OSError, controller interrupt를 넣는다. 402 fixture의 invocation marker는 한 번만 증가해야 한다.

기존 attempt에 sentinel을 넣은 뒤 실행을 시도하면 프로세스 호출 0회와 sentinel 보존을 확인한다. worktree 밖·symlink 경로도 같은 방식으로 거절한다. resume 문자열은 UUID로 강제 변환하지 않고 정확히 전달하며, 값이 없을 때 bare `--resume`이나 `--continue`를 넣지 않는다.

backend별 argument-capturing fake child도 실행한다. probe 호출과 worker 호출 marker를 구분하고 실제 worker가 받은 argv를 확인한다. Cursor는 print·trust·auto-review, 정확히 한 번의 `--sandbox enabled`, 지정 model과 `stream-json`을 받아야 하며 force/yolo는 없어야 한다. Grok은 resolver 제약을 유지하면서 `--sandbox`가 정확히 한 번이고 그 값이 prepare가 반환한 profile이어야 하며, 전체 worker rules가 `--rules` 값으로 전달돼야 한다. Grok의 prepared profile이 없으면 worker 호출은 0회다. 시작 전에 해석한 prefix만 검사하지 않는다.

```python
def assert_grok_child_argv(received, prepared_profile, rules):
    assert received.count("--sandbox") == 1
    assert received[received.index("--sandbox") + 1] == prepared_profile
    assert received[received.index("--rules") + 1] == rules
    for flag in ("--no-plan", "--no-subagents", "--disable-web-search", "--always-approve"):
        assert flag in received
```

Cursor에서는 최종 prompt에 worker rules와 이번 brief/report 경로가 들어 있는지도 확인한다. 이 증거는 CLI에 보낸 경계만 입증하며 실제 모델의 준수나 OS 격리 성공으로 확대하지 않는다.

- [ ] **Step 2: RED를 확인한다.**

Run: `python3 -m unittest discover -s tests/products/sddx -p test_run_worker.py -v`

Expected: 새 runner 부재로 실패한다.

- [ ] **Step 3: argv와 고정 파일 layout을 구현한다.**

attempt를 배타적으로 만든 후 brief를 복사하고 dispatch에 worker rules·brief/report 절대 경로·스펙 R4의 읽기 경계를 넣는다. Grok은 준비된 profile만 사용하고 Cursor는 `model_ids`에 있는 명시적 model만 사용한다. subprocess 호출에는 `_command`를 거친 argv 배열을 사용한다.

```python
with stdout_path.open("xb") as out, stderr_path.open("xb") as err:
    process = subprocess.Popen(
        command, cwd=options.worktree,
        stdin=subprocess.DEVNULL, stdout=out, stderr=err,
    )
    metadata.update(state="running", pid=process.pid)
    write_metadata(metadata_path, metadata)
    code = process.wait()
    metadata.update(state="exited", exit_code=code, ended_at=utc_now())
    write_metadata(metadata_path, metadata)
return code if code >= 0 else 128 - code
```

`stdout_path`/`stderr_path`/`metadata_path`는 고정 파일 layout으로 만든 Path다. 내부 `write_metadata(path: Path, value: dict[str, Any]) -> None`는 임시 파일 + atomic replace, `utc_now() -> str`은 timezone이 있는 UTC ISO 문자열을 반환한다. 이 두 내부 함수도 같은 파일에 둔다.

초기 metadata는 스펙 R4의 필드를 모두 포함한다. OSError와 interrupt 분기는 실제 회수한 exit만 저장하고 모르면 null로 둔다. error 문자열에는 환경이나 prompt 전체를 붙이지 않는다. parent 종료를 자식 작업 종료로 해석하거나 Grok cleanup을 자동 호출하지 않는다.

- [ ] **Step 4: argv 전달과 실패 보존을 확인한다.** Task 2에서 검증한 `_command`를 소비하며 테스트의 합성 `.cmd`/실행 파일로 공백·Unicode·따옴표·`&`·`%`를 포함한 전체 실행 인자의 왕복을 확인한다. 위 backend별 실제 child 검사도 통과해야 한다. 전송 실패는 launch 실패로 보존하고 shell 문자열 보간으로 우회하지 않는다. POSIX signal 음수 exit와 wrapper exit 변환도 검사한다.
- [ ] **Step 5: GREEN 후 커밋한다.** 위 unittest 명령과 `git diff --check`를 실행한다.

```bash
git add skills/sddx/scripts/run_worker.py tests/products/sddx/test_run_worker.py
git commit -m "feat(sddx): preserve worker attempts with a shared runner"
```

## Task 4: 읽기 전용 상태와 제한된 로그 구간 조회

**Spec:** R4의 조회 / AC5.

**Files:**

- Modify: `skills/sddx/scripts/run_worker.py` — `status` subcommand.
- Create: `tests/products/sddx/test_worker_status.py`

**Interfaces:**

- Consumes: Task 3의 `run.json` schema 1, `worker.jsonl`, `stderr.log`, `report.md` 존재 여부.
- Produces: `read_status(attempt_dir: Path, *, stream: str | None = None, offset: int = 0, max_bytes: int = 2048) -> dict[str, Any]`.
- Output: 기본 metadata·파일 크기·report 존재. stream 지정 시 스펙 R4의 `stream`, `offset`, `next_offset`, `size`, `preview`, `has_more`, `decode_errors`, `pending_bytes`.
- Errors: 잘못된 stream, 음수/범위 밖 offset, 1–8192 밖 max_bytes, 읽을 수 없는 metadata는 `ValueError` 또는 `OSError`로 CLI exit 2.

- [ ] **Step 1: 조회 테스트를 작성한다.** 합성 attempt에 metadata와 1 MiB 단일 JSON 행을 만든다. 기본 조회에는 그 본문이 없어야 하고, 구간 조회는 실제 읽은 위치만 전진해야 한다.

```python
from run_worker import read_status

def assert_window(attempt):
    first = read_status(attempt, stream="stdout", offset=0, max_bytes=2048)
    assert 0 < first["next_offset"] <= 2048
    assert first["has_more"] is True
    second = read_status(attempt, stream="stdout", offset=first["next_offset"], max_bytes=2048)
    assert second["offset"] == first["next_offset"]
```

UTF-8 문자가 경계에 걸린 경우, 비정상 byte, offset==size, offset>size, 비JSON 행, metadata 손상, 보고서만 있고 exit가 없는 경우를 포함한다. 조회 전후 파일 bytes/mtime을 비교하고 subprocess 호출을 mock으로 금지해 반복 조회가 실행·갱신을 하지 않음을 확인한다.

같은 로그에 `한`의 첫 두 byte만 쓴 뒤 status를 읽고, 마지막 byte를 append한 뒤 반환된 offset으로 다시 읽는 테스트를 추가한다. 첫 조회는 문자를 대체하거나 offset을 전진시키면 안 된다. 다음은 테스트 본문에 사용할 검증이다.

```python
raw = "한".encode("utf-8")
log = attempt / "worker.jsonl"
log.write_bytes(raw[:2])
first = read_status(attempt, stream="stdout", max_bytes=2048)
assert (first["preview"], first["next_offset"], first["pending_bytes"]) == ("", 0, 2)
assert first["has_more"] is True and first["decode_errors"] is False
with log.open("ab") as out:
    out.write(raw[2:])
second = read_status(attempt, stream="stdout", offset=first["next_offset"])
assert (second["preview"], second["next_offset"], second["pending_bytes"]) == ("한", 3, 0)
```

고정된 완전한 `한`에서 `max_bytes=1`은 너무 작은 구간 오류지만, 임시 EOF에 첫 byte만 있는 경우는 `pending_bytes=1`의 대기 결과여야 한다. 둘을 같은 오류로 처리하는 구현을 거절한다.

- [ ] **Step 2: RED를 확인한다.**

Run: `python3 -m unittest discover -s tests/products/sddx -p test_worker_status.py -v`

Expected: `read_status` 부재로 실패한다.

- [ ] **Step 3: 구간 reader를 구현한다.** 전체 파일을 `read_text()` 하지 않는다. seek/read와 incremental UTF-8 decoder를 사용한다. 다음은 구간 핵심이다.

```python
decoder = codecs.getincrementaldecoder("utf-8")("replace")
preview = decoder.decode(chunk, final=False)
pending, _ = decoder.getstate()
consumed = len(chunk) - len(pending)
next_offset = offset + consumed
pending_bytes = len(pending)
```

`size`는 이번 호출에서 얻은 파일 크기이며 `chunk`는 그 안에서 `min(max_bytes, size - offset)`만큼 읽은 결과다. 이번 EOF를 최종 EOF로 간주하지 않는다. `decode_errors`는 소비 구간의 strict decoding 성공 여부로 판정한다. `consumed == 0`, `pending_bytes > 0`, `offset + len(chunk) < size`이면 더 큰 구간이 필요한 입력 오류다. 임시 EOF의 미완성 suffix는 소비하지 않고 `pending_bytes`·빈 preview·같은 next_offset을 반환한다. `has_more`는 `next_offset < size`다. 이때 caller는 새 byte나 실행 상태 변화가 생길 때까지 기존 host job을 기다리며 같은 조회를 반복하지 않는다. 종료 후 남은 미완성 suffix도 원문 위치를 보존한다. CLI JSON은 UTF-8 byte로 64 KiB 상한을 확인하고 초과 시 본문을 몰래 생략하지 말고 오류를 반환한다.

provider event의 `type`이나 본문의 `DONE`/`402`를 해석하지 않는다. raw 위치를 제공할 뿐이며 run 상태나 role 판정을 바꾸지 않는다.

- [ ] **Step 4: GREEN 후 runner 회귀를 확인한다.** 새 상태 테스트와 Task 3 runner 테스트를 각각 한 번 실행한다. 이후 같은 코드로 반복 실행하지 않는다.
- [ ] **Step 5: 커밋한다.**

```bash
git add skills/sddx/scripts/run_worker.py tests/products/sddx/test_worker_status.py
git commit -m "feat(sddx): add bounded read-only worker status"
```

## Task 5: 두 호스트의 입력·현재 상태·리뷰 지침 연결

**Spec:** R1, R5, R6, R7 / AC1, AC6, AC7, AC8.

**Files:**

- Modify: `skills/sddx/SKILL.md`
- Modify: `skills/sddx/references/dispatch.md`
- Modify: `skills/sddx/references/worker-prompt.md`
- Create: `skills/sddx/references/current-state.md`
- Modify: `tests/products/sddx/behavior-probes.md`
- Modify: `tests/products/sddx/test_contract.py` — 바뀐 계약의 기존 assertion과 참조 파일 존재 확인.
- Modify if existing cases change: `tests/products/sddx/cases.json` — 실제 사례 정의를 바꾼 경우에만 ID/기대를 함께 맞춘다.

**Interfaces:**

- Consumes: Task 1 CLI, Task 2 resolver JSON, Task 3/4 run/status CLI, 기존 Grok prepare/cleanup CLI.
- Produces: 같은 plan/backend 선택 의미와 같은 Python 도구를 사용하는 Claude/Codex dispatch 지침. `current-state.md`는 원장 블록 템플릿만 소유한다.

- [ ] **Step 1: 기존 지침과 새 스펙의 충돌을 먼저 제거한다.** '경로 인자가 없으면 항상 중단', '정의 부재를 매번 출력', Cursor force 요구를 새 규칙에 맞게 교체한다. 새 설명을 아래에 덧붙여 상충하는 두 규칙을 남기지 않는다. worker 본문 읽기 경계와 기존 역할 FAIL/UNVERIFIED 규칙은 유지한다.
- [ ] **Step 2: 현재 상태 템플릿을 작성한다.** 다음은 실제 값이 채워진 합성 예시다. runtime reference는 영어로 작성한다.

```markdown
# SDD ledger — plan: docs/plans/storage.md
<!-- sddx:current:start -->
## Current state
Plan: docs/plans/storage.md
Next plan: none
Backend: cursor — explicit user change
Worktree: /workspace/project; HEAD: abc1234
Task: P1; fix round: 2; attempt: worker-attempts/P1-fix2
Worker session: cursor-session-example
Review host: codex; model: inherited; effort: inherited xhigh
Open findings: P1-review.md#remaining
Authorized scope: local implementation and verification
Host checks pending: browser smoke
Next action: collect browser evidence before another worker call
Evidence: worker-attempts/P1-fix2/run.json
<!-- sddx:current:end -->
```

첫 줄 계획 식별자는 marker 밖에 보존하고 바로 아래 블록만 교체한다. 기존 `Task <ID>: complete`와 fix-round 이력은 그대로 두고 새 이력은 아래에 한 번 남긴다. 오래된 `Backend:` 한 줄이나 별도 recovery 문서를 현재 사실로 잘못 읽지 않도록 재개 순서를 명시한다. 상속 effort/host 제한은 최초 확인과 변경 시점에만 기록한다.

- [ ] **Step 3: 실행 예시를 새 도구로 연결한다.** 완결된 brief 생성 → Grok이면 기존 prepare → run → host job wait → 필요한 status 구간 → 실제 worker/관련 작업 종료 확인 → Grok cleanup → 기존 리뷰 순서를 쓴다. 같은 journal의 미정리 실행이 있으면 다음 실행을 시작하지 않는다. status의 `pending_bytes > 0`은 아직 완성되지 않은 문자이므로 같은 offset을 짧게 반복 조회하지 않는다. 원문을 통째로 출력하거나 실행 스크립트를 새로 만들라는 안내를 제거한다.
- [ ] **Step 4: host 전용 검증과 report-only 정정을 명확히 한다.** 브리프에 `Worker checks`와 `Host checks`를 넣고 미완료 host 검증은 기존 상태로 보고하게 한다. host가 결과를 채울 수 있고 코드 변경이 없으면 새 worker 호출을 요구하지 않는다. 자동 retry 0, 명시적 backend 변경, round 유지, 실제 호출 방식 기록을 예시와 맞춘다.
- [ ] **Step 5: 다음 행동 시나리오를 두 호스트용으로 기록하고 문서상 기대를 대조한다.**

| 입력/상황 | 기대 |
| --- | --- |
| spec+plan과 'Grok CLI로 구현' | backend 질문 0회, 활성 계획 하나 |
| backend 없음·현재 선택 없음 | 한 번 질문; 유일한 CLI 자동 선택 금지 |
| 현재 상태에 Cursor가 있고 '계속' | 같은 선택·round·미해결 지적 복구 |
| 식별자 첫 줄·`Task 1: complete`·진행 중 fix 이력이 있는 원장에 블록 갱신 후 재개 | 첫 줄과 이력 보존, 완료 Task 1 재호출 0회, 기존 fix round에서 계속 |
| 명시한 순서의 세 계획 | 순서 유지, 동시 활성 계획 하나 |
| 독립 계획 순서나 소유 파일 충돌 | 필요한 정보만 확인 |
| Grok에서 Cursor로 변경 승인 | 종료/cleanup 확인, 새 공급자 세션, 같은 task/round |
| 상속 XHigh로 여러 리뷰 | 실제 상속 방식 기록, 정의 부재 설명 반복 없음 |
| 402 이후 상태 조회 반복 | 새 worker 호출 0회 |
| host 검증만 미완료 | host 검증 수행, 동일 이유 worker 재호출 없음 |
| report-only 정정 | 증거 정정, 새 코드 커밋 요구 없음 |
| exit 0이지만 tool evidence 없음 | 역할 UNVERIFIED, clean DONE 금지 |

표는 테스트 설계이며 실제 모델 실행 결과가 아니다. 공급자 없는 assertion은 문구·참조 계약을 검사한다. 독립 모델 행동 probe나 라이브 실행은 명시적 승인 범위에서만 하고 미실행은 `not_measured`로 둔다.

- [ ] **Step 6: 기존 계약 검사를 실행하고 커밋한다.**

Run: `python3 -m unittest discover -s tests/products/sddx -p test_contract.py -v`

Expected: 제품 정체, 기존 worker 경계, reviewer 모델 상속, 새 reference 연결이 함께 통과한다. 실제 모델 준수라고 보고하지 않는다.

```bash
git add skills/sddx/SKILL.md skills/sddx/references/dispatch.md skills/sddx/references/worker-prompt.md skills/sddx/references/current-state.md tests/products/sddx/behavior-probes.md tests/products/sddx/test_contract.py
git commit -m "docs(sddx): simplify controller state and host handoffs"
```

`cases.json`을 실제 수정했다면 위 커밋에 해당 파일만 추가한다. unrelated 변경을 `git add -A`로 포함하지 않는다.

## Task 6: 계약·버전·통합 검증 마무리

**Spec:** R7, R8 / 전체 AC1–AC8 통합 확인.

**Files:**

- Modify: `skills/sddx/README.md`, `skills/sddx/README.en.md`, `skills/sddx/CHANGELOG.md`
- Modify: `skills/sddx/release.toml`, `skills/sddx/SKILL.md`, `skills/sddx/.claude-plugin/plugin.json`
- Modify: `docs/maintainers/products/sddx/contract.md`
- Modify: `docs/maintainers/products/sddx/compatibility.md`
- Modify: `docs/maintainers/products/sddx/testing.md`
- Modify: `docs/maintainers/products/sddx/release.md`
- Review only: `products.toml`, `docs/maintainers/repository/versioning.md`, 기존 SDDx sandbox 테스트.

**Interfaces:**

- Consumes: Task 1–5 결과, 스펙의 두 호스트 범위와 실제 검증 기록.
- Produces: 개발 목표 버전 `2.0.0`으로 일치한 배포 메타데이터, 현재 계약 문서, 오프라인 검증 결과와 분리된 `not_measured` 목록.

- [ ] **Step 1: 문서 소유권을 맞춘다.** 사용자 동작은 제품 README, 현재 계약은 contract, host/OS 지원·실제 측정은 compatibility, 검증 절차·결과는 testing, 출시는 release에 기록한다. 한국어·영어 README에서 backend 지정/재사용, effort 상속, 새 helper 사용, 실제 측정 한계를 함께 대조한다. 기존 설치 marker와 설치 코드 블록은 유지한다. 연구·설계 본문을 모두 복사하지 않는다. Python 3.11과 현재 호스트 ID를 유지한다.
- [ ] **Step 2: 필수 기능 변경을 버전에 반영한다.** `release.toml`, SKILL metadata, Claude plugin manifest의 버전을 `2.0.0`으로 맞춘다. CHANGELOG에 기존 Cursor CLI가 새 필수 flag를 지원하지 않으면 차단됨, 새 실행 도구, 현재 상태 규칙, 진행 중 실행 자동 전환 없음 등을 적는다. 다른 제품과 catalog 버전은 바꾸지 않는다.
- [ ] **Step 3: 전체 오프라인 검증을 실행한다.**

```bash
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py
python3 scripts/release.py check --product sddx
git diff --check
```

각 명령의 실제 exit와 실패/skip을 기록한다. 현재 기준에서 새 파일이 product verification의 compile/discovery에 포함되는지 결과로 확인한다. 이미 통과한 검사는 새로운 수정이나 미해결 실패가 없으면 반복하지 않는다. macOS에서 skip된 Windows 실행은 native Windows 통과로 쓰지 않는다.

- [ ] **Step 4: 시나리오와 플랫폼 한계를 정직하게 기록한다.** 오프라인 helper/argv 검사, 지침 문구 검사, native 행동 probe, 실제 공급자 실행을 별도 분류한다. Claude/Codex × Cursor/Grok 조합마다 새 버전 실제 실행 여부를 적는다. 승인이 없는 라이브 호출은 하지 않으며 모든 조합의 runtime 성공을 선언하지 않는다. release 문서의 Claude 정의 로딩 확인은 공개 출시 시 별도 수행할 요구로 유지한다.
- [ ] **Step 5: 변경 범위와 호환성을 리뷰한다.** 새 helper가 SDD의 태스크 순서·fix cap·리뷰를 소유하지 않는지, provider event parser·DB·retry 엔진이 추가되지 않았는지 확인한다. 실제 테스트·역할 증거가 없는데 DONE을 만드는 분기가 없어야 한다. Superpowers 원본, catalog, 다른 제품, 전역 설치 설정에 diff가 없어야 한다.
- [ ] **Step 6: 문서·메타데이터 변경을 커밋하고 구현 결과를 보고한다.**

```bash
git add skills/sddx/README.md skills/sddx/README.en.md skills/sddx/CHANGELOG.md skills/sddx/release.toml skills/sddx/SKILL.md skills/sddx/.claude-plugin/plugin.json docs/maintainers/products/sddx/contract.md docs/maintainers/products/sddx/compatibility.md docs/maintainers/products/sddx/testing.md docs/maintainers/products/sddx/release.md
git commit -m "chore(sddx): align execution contract and version 2.0"
```

구현 완료 보고에는 변경 내용, 실제 검사, 미측정 조합, 정리하지 못한 문제만 적는다. 태그·공개 Release·설치 교체·카탈로그 채택은 수행하지 않는다. 실행 중 작업의 문서 경로를 없애지 않도록 이 history 문서의 정리는 해당 실행이 끝난 뒤 저장소 규칙에 따라 처리한다.

## 스펙 대조와 작성 검토

| 수용 기준 | 구현 Task | 검증 위치 |
| --- | --- | --- |
| AC1 입력·계획 해석 | 5 | behavior-probes 및 contract 대조 |
| AC2 제목·본문 경계 | 1 | test_extract_task |
| AC3 CLI 기능과 argv | 2, 3 | test_resolve_backend, test_run_worker |
| AC4 실행 증거·실제 exit | 3 | test_run_worker |
| AC5 조회 상한·offset·읽기 전용 | 4 | test_worker_status |
| AC6 현재 상태 복구 | 5 | 합성 원장/재개 시나리오 |
| AC7 오류·host 검증·판정 분리 | 3, 5 | fake invocation 수, 행동 시나리오 |
| AC8 두 호스트·기존 경계·미측정 | 2, 5, 6 | 제품/전체 검사와 compatibility 대조 |

설계상 남는 한계는 의도적이다. 원시 도구 결과의 의미 판정은 컨트롤러/리뷰어가 맡고, 프로세스 트리 종료와 Grok cleanup 확인은 기존 host 절차를 따른다. 자동 로그 요약·자동 복구·신규 agent 정의를 추가해 이 범위를 넓히지 않는다.
