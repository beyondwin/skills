# SDDx

[English](README.en.md)

## 목적

지금 쓰는 Claude Code 또는 Codex 세션이 Superpowers SDD(과제 나누기, 리뷰,
수정 반복)를 진행하고, 코드 작성만 Cursor Agent 또는 Grok Build에 맡깁니다. 둘
다 Grok 4.7만 쓰고 `-fast` 변형은 쓰지 않습니다.

| 말 | 뜻 |
| --- | --- |
| 호스트 | `/sddx` 또는 `$sddx`를 받은 세션(계약의 controller)입니다. 과제를 나눠 주고, 결과를 확인하고, 리뷰를 돌립니다. |
| 워커(worker) | 과제 하나를 코딩하고 커밋하는 외부 CLI입니다. |
| 브리프(brief) | 워커가 받는 과제 한 건의 설명서입니다. 계획 전체에 걸린 제약도 담습니다. |
| 러너(runner) | 워커를 띄우고 시도를 기록하는 `run_worker.py`입니다. |
| High / XHigh | 추론 강도입니다. XHigh가 더 깊게 생각합니다. |

## 사용할 때와 사용하지 않을 때

- 쓸 때: 구현 계획 파일이 있고, 메시지에 `/sddx`(Claude Code) 또는
  `$sddx`(Codex)를 적었을 때만 씁니다.
- 쓰지 않을 때: 설계·계획 작성, `writing-plans`, `executing-plans`(Native
  포함), `pre-sdd-review`, 일반 SDD, 이 세션에서 직접 코딩, `/sddx`나 `$sddx`
  없는 “Grok으로 구현해 줘”.

## 지원 호스트

sddx: Claude Code and Codex supported for local or repository-based use.
(Claude Code와 Codex에서 로컬 또는 저장소 연결로 씁니다.)

- 호스트는 `claude-code`, `codex`입니다. Cursor Agent와 Grok Build는 워커이고
  호스트가 아닙니다.
- OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않고, Windows에서는 제품 CLI가
  거절합니다.
- Grok 워커는 linked worktree에서 Python 3.11+가 필요하고, MCP 호출 도구를 끄며,
  `--disallowed-tools`와 `--deny`가 없으면 실행하지 않습니다.
- Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다.
- 호스트·워커 네 조합을 macOS에서 실제로 돌려 보았습니다. 확인 범위는
  [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md),
  공통 한계는 [호환성 안내](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)를
  보세요.

## 설치

저장소를 받은 뒤 바로가기(심볼릭 링크) 두 개를 만듭니다. 하나는 Codex용,
하나는 Claude Code용입니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

아래 블록은 링크 하나를 만들고, 같은 링크가 이미 있으면 성공으로 봅니다. 다른
링크, 깨진 링크, 파일, 디렉터리는 자동으로 바꾸지 않고 멈추므로, 대상을 확인한
뒤 다시 실행하세요.

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

링크마다 한 번씩 실행합니다. 첫 줄은 Codex면
`python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<'PY'`, Claude Code면
`python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<'PY'`입니다. 다음
줄부터 위 블록을 그대로 붙이고 마지막 줄에 `PY`만 적습니다. 따옴표는 그대로 둡니다.

지울 때는 먼저 확인하고 그 링크만 지웁니다.

```bash
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx
```

`$skill-installer` 형식의 공개 경로는 아래와 같지만, Codex는
`~/.agents/skills/sddx` 링크에서 이 스킬을 찾습니다. [Codex 설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-codex.md)의
세 스킬에는 들지 않으니 `~/.codex`나 `~/.grok`에 복사본을 만들지 마세요.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/sddx
```

그 밖의 안내는 [로컬 링크](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를 보세요.

## 첫 호출

Claude Code는 `/sddx`, Codex는 `$sddx`입니다. 계획 파일 뒤에 워커를 적을 수
있습니다(`cursor`, `grok`, 줄여서 `c`, `g`).

```text
/sddx docs/history/plans/example.md
$sddx docs/history/plans/example.md grok
```

## 예상 결과

1. 워커: 적지 않았으면 계획마다 한 번 묻고, 하나만 쓸 수 있어도 확인받습니다.
   고른 쪽이 없으면 멈추며, 스스로 다른 쪽으로 바꾸지 않습니다.
2. 과제마다 새 워커와 브리프를 씁니다. 워커는 전체 계획을 읽지 않습니다.
3. 종료 코드 0은 완료가 아닙니다. 호스트가 보고서, 실제 테스트 결과, 커밋, 도구
   기록(무엇을 읽고 실행했는지)을 확인한 뒤 호스트와 같은 모델로 리뷰합니다. 보통
   High이고, 동시성·권한·비밀·샌드박스 변경과 4~5회차 재리뷰는 XHigh입니다.
4. 수정 1~3회차는 강도가 같으면 같은 워커 세션을 이어서(resume), 4~5회차는 새
   XHigh 워커가 합니다. 계획 밖 작업은 먼저 묻고, push나 게시가 필요하면 BLOCKED로 멈춥니다.

시도마다 작업 트리 `.superpowers/sdd/<계획이름>/` 아래 폴더에 `run.json`,
`report.md`, 로그가 남습니다. 진행 상황은 `run_worker.py status`로 봅니다. 세션
ID, 워커 생존 여부(`pid_alive`), 읽은 파일·검색·셸 목록만 짧게 보여 주며, 로그
전체는 붙여 넣지 않습니다.

| 상황 | 결과 | 다음 할 일 |
| --- | --- | --- |
| 워커가 `--idle-timeout` 동안 아무것도 출력하지 않음(기본 900초, `0`은 끔) | 워커 중지, `timed_out`, exit 124, `the worker wrote no output for 900 seconds` | 워크트리에 남은 변경을 확인하고, 그 세션을 잇지 말고, 이전 보고서와 커밋을 적은 브리프로 새 워커를 띄웁니다. |
| `--timeout` 초과(기본 `0`, 끔) | 워커 중지, `timed_out`, exit 124 | `status`와 보고서를 확인합니다. |
| 러너에 Ctrl-C 또는 SIGTERM | `interrupted`, 워커도 중지(SIGTERM, 10초 뒤 SIGKILL), exit 130 | 워커가 띄운 백그라운드 프로세스가 남았는지 확인합니다. |
| 잔액 부족(402), 인증·권한 실패 | 시도 종료 | 조건을 먼저 바꿉니다. 자동 재시도는 없습니다. |

시도를 멈출 때는 러너를 멈추고, 기록된 워커 pid나 `pkill -f`는 쓰지 마세요.
명령과 판정 규칙은 [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)을 보세요.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
