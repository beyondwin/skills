# SDDx

[English](README.en.md)

## 목적

Superpowers SDD를 현재 Claude Code 또는 Codex 세션이 오케스트레이터로
돌리고, 구현만 Cursor CLI 또는 Grok Build CLI에 넘깁니다.

## 사용할 때와 사용하지 않을 때

구현 계획이 있고 외부 Grok/Cursor implementer로 SDD를 실행할 때 씁니다.

설계·계획 작성, `pre-sdd-review`, 네이티브 서브에이전트 구현에는 쓰지
않습니다.

## 지원 호스트

sddx: Claude Code and Codex supported for local or repository-based use.

지원 호스트 id는 `claude-code`, `codex`입니다. Cursor와 Grok CLI는
구현 worker이지 호스트가 아닙니다. 이 버전은 Claude Code·Codex와
Cursor·Grok의 네 조합 가운데 어느 것도 실제 공급자 실행으로 측정하지
않았습니다. 네 조합 모두 `not_measured`입니다. 이전 버전에서 얻은 Codex/Grok
관측은 그 버전의 기록이며 이번 버전의 증거가 아닙니다. 조합별 측정 상태는 아래
호환성 문서의 표에 있습니다. Claude.ai, Cowork,
Skills API 업로드, marketplace 게시는 지원하지 않습니다. 공유 한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을
보세요.

## 작업 범위와 리뷰

작업자는 완결된 task brief와 지정 참고자료를 받아 구현하고, 전체 계획을 다시
읽지 않습니다. 보고서의 scope deviations와 실제 도구 기록을 비교합니다. 역할
위반은 FAIL, 도구 기록 부족은 UNVERIFIED이며 clean DONE으로 처리하지 않습니다.
`Search paths`는 내용 검색을 제한합니다. 현재 worktree의 파일명 목록 조회와
작업에 필요한 ignore·빌드·테스트 설정 직접 읽기는 허용하며, 이 행동만으로
우려사항을 보고하지 않습니다. 전체 계획 본문과 비밀정보는 계속 읽지 않습니다.

Task 리뷰·재리뷰·최종 리뷰는 모두 현재 오케스트레이터 모델을 따릅니다. 리뷰
effort는 별도로 지정합니다. Claude Code에서 High는 `model` 인자 없이 평소대로
dispatch하는 것이고, XHigh는 `model` 인자 없이 `subagent_type`을
`sddx-reviewer-xhigh`로 지정하는 것입니다. XHigh는 lock·순서·공유 상태 변경,
auth·권한·secret·sandbox 경계 변경, round 4–5 재리뷰, 반복해서 놓친 결함일 때만
씁니다. diff 길이나 구현 난이도, 최종 리뷰라는 사실은 근거가 아닙니다. 승급 정의는
Claude Code 전용이며, 없는 호스트에서는 그 한계를 보고한 뒤 진행합니다.

## Backend 선택과 유지

`sddx <plan-file> [cursor|grok|c|g]`에서 `c`는 `cursor`, `g`는 `grok`입니다.
backend는 이 요청의 명시적 선택, 같은 실행의 현재 상태, 한 번의 질문 순서로
정합니다. 명시적 선택은 이후 task에서 다시 승인받지 않습니다. 쓸 수 있는
backend가 하나뿐이어도 그 사실과 빠진 backend의 `reason`을 보여 주고 확인을
받은 뒤에 진행합니다. 요청한 backend가 없으면 다른 쪽으로 바꾸지 않고 멈춥니다.

이번 메이저 변경부터 Cursor CLI는 headless print(`--print` 또는 `-p`), `--trust`,
`--auto-review`, `--sandbox`, 확인된 `stream-json` 출력 형식, 그리고 모델 목록
명령이 실제로 돌려준 Grok 모델 id를 모두 선언해야 합니다. 조건을 채우지 못하는
기존 Cursor 설치본은 `available: false`와 `reason: missing_flags`로 나옵니다.
예전처럼 `--force`/`--yolo` 일괄 승인으로 물러나지 않으며, 이를 되살리는 옵션도
없습니다. 없는 backend의 `reason`은 `not_found`, `identity_mismatch`,
`missing_flags`, `no_grok_model` 중 하나입니다.

backend를 바꾸면 이전 공급자의 session ID를 넘기지 않고 fix 라운드 수도
초기화하지 않습니다. 리뷰는 계속 현재 오케스트레이터 모델을 상속하고 effort만
따로 지정합니다. 리뷰어에 `model` 오버라이드를 넘기지 않습니다.

## 실행 도구와 증거

계획에서 task 구간을 뽑을 때는 컨트롤러가
`scripts/extract_task.py <plan-file> --heading "<# 없는 제목 전체>" --output <file>`을
씁니다. exit 0은 성공, 2는 파일·인자 오류, 3은 제목이 없거나 중복이거나 본문이
비었다는 뜻입니다. 이미 있는 출력 파일은 덮어쓰지 않습니다.

worker 실행 경로는 `scripts/run_worker.py run` 하나입니다. 공급자 명령을 직접
조합하거나 실행마다 새 스크립트를 쓰지 않습니다. 한 번의 시도는 worktree의
`.superpowers/` 아래 새 디렉터리에 `brief.md`, `dispatch.md`, `worker.jsonl`,
`stderr.log`, `run.json`, `report.md` 여섯 파일을 남깁니다. `report.md`는 worker가
직접 쓰며 러너가 대신 쓰지 않습니다. 러너는 Grok 프로파일 prepare·cleanup을 하지
않습니다. 순서는 컨트롤러가 지키는 prepare → run → 종료 확인 → cleanup입니다.
자동 재시도는 어디에도 없습니다.

`--timeout <초>`는 한 시도의 경과 시간을 제한합니다. 기본값은 3600이고
`--timeout 0`은 제한 없이 기다립니다. 제한에 걸리면 러너는 worker에 SIGTERM을
보내고 10초 뒤에도 살아 있으면 kill한 다음 `state`를 `timed_out`으로 적고 124로
끝냅니다. 신호는 worker 프로세스 하나에만 보내므로 worker가 시작한 자식
프로세스는 쫓아가지 않습니다. 프로세스 트리를 정리했다고 적지 않습니다.

진행 중이거나 끝난 시도는 `scripts/run_worker.py status`로만 읽습니다. 이 명령은
읽기 전용이고 아무것도 해석하지 않습니다. 기본 응답은 메타데이터, 로그 크기,
`report.md` 존재 여부이며 로그 본문은 나오지 않습니다. 본문 창은 `--stream`으로
요청하고 기본 2048바이트, 최대 8192바이트이며 JSON 응답 전체는 64 KiB로
제한됩니다. 로그 전체를 세션에 쏟지 않습니다.

`run.json`은 프로세스 사실만 담습니다. `schema_version`은 2이고, `state`는
`starting`, `running`, `exited`, `launch_failed`, `timed_out`, `interrupted` 중
하나이며 task 상태가 아닙니다. 프로세스 exit 0은 깨끗한 DONE이 아닙니다. 래퍼
exit는 worker의 exit를 따르고, POSIX 시그널은 `128 + signal`을 반환하며
`run.json.exit_code`에는 실제 음수 반환값이 남습니다. 실행 실패는 2, 처리된
중단은 130, 시간 제한에 걸린 시도는 124입니다. exit 2는 실행 실패와 worker가 정말
2로 끝난 경우가 겹치므로 `run.json.state`로 구분하며, 시도 디렉터리가 없거나
`run.json` 없이 있으면 시도가 만들어지기 전에 실행이 거부된 것이고 stderr의
`BLOCKED:` 줄이 그 이유입니다.

실행의 현재 상태는 Superpowers SDD ledger 맨 위의 블록 한 곳에만 둡니다. 별도
상태 파일을 만들지 않습니다. Cursor는 effort를 플래그가 아니라 모델 ID에 담으므로,
러너는 선언된 effort가 `--effort`와 어긋나는 모델을 거부하고 `configured_effort`에는
ID에서 읽은 effort가 들어갑니다. ID가 effort를 선언하지 않으면 `null`로 남고 실제
적용 effort는 `unknown`입니다. 요청 effort와 설정 effort를 따로 적으며, 둘 중 어느
쪽도 모델이 실제로 쓴 effort를 증명하지 않습니다. 공유 제품 소스를 고쳐도 진행
중인 실행은 자동으로 바뀌거나 다시 시작되지 않고 새 실행부터 적용됩니다.

## 실제 측정 한계

Windows에서 npm 방식 `.cmd` 래퍼로 실행하면 launch failure로 기록됩니다. worker
규칙과 Cursor dispatch 텍스트가 여러 줄인데 `cmd.exe` 명령줄은 줄바꿈을 담지
못하기 때문이며, 조용히 망가뜨리는 대신 실패로 남기는 쪽을 택했습니다. Windows
argv 전송 자체는 이 브랜치에서 실제로 측정하지 않았습니다. Grok의 `--rules`는
명령줄로만 전달되고 시도 디렉터리의 여섯 파일에 남지 않으므로,
`references/worker-prompt.md`를 고치면 과거 Grok 시도를 저장된 증거만으로 그대로
재현할 수 없습니다. 미측정 항목 전체는 아래 호환성 문서에 있습니다.

## Grok worktree 실행

Grok backend로 linked worktree에서 실행하려면 Python 3.11+가 필요합니다.
SDDx는 worker가 커밋할 수 있도록 작업용 Git 쓰기 프로파일을 준비합니다.
이때 만든 설정과 복원 상태는 설치 파일과 커밋에서 제외하고, worker가 종료되면
기존 설정을 복원하거나 생성한 설정을 제거합니다.

## 설치

저장소를 클론한 뒤 링크 두 개를 겁니다. 첫 링크는 Codex, 둘째는 Claude
Code입니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

아래 일회성 Python 블록은 source와 target을 인자로 받습니다. source가 실제 스킬
디렉터리인지 먼저 확인하고, 같은 링크는 성공으로 처리합니다. 다른 링크, 깨진 링크,
파일, 디렉터리는 자동으로 바꾸지 않습니다. 대상이 검사 뒤 생기는 경우에도 멈추므로
직접 확인한 뒤 다시 실행해야 합니다.

<!-- sddx-local-links -->
```python
import os
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: python3 - SOURCE TARGET")
source = Path(sys.argv[1]).expanduser().resolve(strict=True)
target = Path(os.path.abspath(os.path.expanduser(sys.argv[2])))
if not source.is_dir() or not (source / "SKILL.md").is_file():
    raise SystemExit("source must be a skill directory")
if target.is_symlink():
    try:
        same = target.resolve(strict=True) == source
    except (OSError, RuntimeError):
        same = False
    if same:
        print("already linked")
        raise SystemExit(0)
    raise SystemExit("refusing different or dangling link")
if target.exists():
    raise SystemExit("refusing existing file or directory")
target.parent.mkdir(parents=True, exist_ok=True)
try:
    target.symlink_to(source, target_is_directory=True)
except FileExistsError:
    raise SystemExit("target appeared during installation; inspect it before retrying")
print("linked")
```

이 블록을 quoted here-document의 표준입력으로 넣고 target마다 별도로 실행합니다.
Codex 호출은
`python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<'PY'`,
Claude Code 호출은
`python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<'PY'`로
시작합니다. 각 호출의 다음 줄에 위 Python 블록을 그대로 넣고 마지막 줄을 `PY`로
닫습니다. source와 target 인자의 따옴표를 유지하세요.

링크는 확인한 뒤에만 제거합니다.

```bash
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx
```

`$skill-installer`는 공개 GitHub 경로를 가리킵니다. Codex는
`~/.agents/skills/sddx`에서 찾습니다. `install-codex.md`의 세 Codex 전용
명령에는 넣지 않습니다. `~/.codex`나 `~/.grok` 복사본을 만들지 마세요.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/sddx
```

나머지 설치 방법은
[설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를
보세요.

## 첫 호출

명시 호출은 Codex에서 `$sddx`, Claude Code에서 `/sddx`입니다.

```text
$sddx docs/history/plans/example.md
/sddx docs/history/plans/example.md
```

## 예상 결과

명시적 backend 선택이 있으면 그 backend로 진행하고, 없으면 이 계획에서 한 번만
고릅니다. 그다음 Superpowers SDD를 외부 implementer와 네이티브 리뷰어로
실행합니다. 시도마다 증거 디렉터리 하나와 ledger의 현재 상태 블록이 남고,
완료 판정은 프로세스 exit가 아니라 보고서·실제 테스트 exit·커밋·도구 기록·
네이티브 리뷰로 정합니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)

## Grok 실행 범위

Grok worker는 MCP 호출 도구를 CLI에서 제외하고, 해당 프로세스에서만
Cursor/Claude MCP 설정 가져오기를 끕니다. 이를 지원하는 `--disallowed-tools`와
`--deny` 옵션이 없으면 실행하지 않습니다. 전역 설정은 바꾸지 않으며 Grok 자체의
MCP 초기화나 다른 시작 경고가 모두 사라진다는 뜻은 아닙니다.
