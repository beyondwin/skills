# SDDx

[English](README.md)

## 목적

구현 계획을 [waygent](https://github.com/beyondwin/skills/blob/main/skills/waygent/README.ko.md)
방식으로 끝까지 돌리되, 코드 작성만 외부 CLI에 맡깁니다. 지금 쓰는 Claude Code
또는 Codex 세션이 계획을 과제로 나누고, 결과를 확인하고, 리뷰를 돌립니다. 코드
작성과 커밋은 Cursor Agent 또는 Grok Build가 과제 하나씩 맡습니다. 두 워커 모두
Grok 4.7만 쓰고 `-fast` 변형은 쓰지 않습니다.

```text
/sddx docs/plan.md grok
  │
  ├─ 과제 1 ─ 워커: 브리프 → 테스트 먼저 → 코드 → 커밋 → 보고서
  │           호스트: 보고서·테스트·커밋 확인 → 리뷰 한 번 → 수정 한 번
  ├─ 과제 2 ─ …
  │
  └─ 끝 ──── 호스트에서 최종 리뷰 한 번 → 수정 → 보고
```

| 말 | 뜻 |
| --- | --- |
| 호스트 | 스킬을 실행하는 Claude Code 또는 Codex입니다. `/sddx`나 `$sddx`를 받은 그 세션이 과제를 나눠 주고, 결과를 확인하고, 리뷰를 돌립니다. |
| 워커(worker) | 과제 하나를 코딩하고 커밋하는 외부 CLI입니다. |
| 브리프(brief) | 워커가 받는 과제 한 건의 설명서입니다. 계획 전체에 걸린 규칙도 담습니다. |
| 러너(runner) | 워커를 띄우고 시도를 기록하는 `run_worker.py`입니다. |
| High / XHigh | 모델이 얼마나 깊게 생각하는지입니다. XHigh가 더 깊게 생각합니다. |

## 사용할 때와 사용하지 않을 때

- 쓸 때: 구현 계획 파일이 있고, 메시지에 `/sddx`(Claude Code) 또는
  `$sddx`(Codex)를 적었을 때만 씁니다.
- 계획에는 계획 전체에 걸린 규칙을 담은 절이 하나 있어야 합니다. 보통
  `## Global Constraints`입니다. 워커가 계획을 읽지 않기 때문입니다. 제목이
  다르면 SDDx가 그 절을 정해 기록하고, 그런 절이 없으면 한 번 묻습니다.
- 쓰지 않을 때: 설계·계획 작성, `/waygent`, `writing-plans`,
  `executing-plans`(Native 포함), `pre-sdd-review`, 일반 SDD, 이 세션에서 직접
  코딩, `/sddx`나 `$sddx` 없는 “Grok으로 구현해 줘”.

## 지원 호스트

sddx: Claude Code and Codex supported for local or repository-based use.
(Claude Code와 Codex에서 로컬 또는 저장소 연결로 씁니다.)

- 호스트는 `claude-code`, `codex`입니다. Cursor Agent와 Grok Build는 워커이고
  호스트가 아닙니다.
- Codex는 대화형 세션에서 씁니다. `codex exec`는 명시 호출 전용 스킬을 읽지
  않으므로 거기서는 `$sddx`가 아무 일도 하지 않습니다.
- waygent 스킬이 이 스킬 옆에 설치되어 있어야 합니다(아래와 같은 방식의 링크).
  없으면 SDDx는 멈춥니다.
- OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않고, Windows에서는 제품 CLI가
  거절합니다.
- Grok 워커는 샌드박스 준비에 Python 3.11+가 필요합니다. MCP 호출 도구를 끄며,
  `--disallowed-tools`와 `--deny`를 지원하지 않는 Grok CLI로는 실행하지 않습니다.
- Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다.
- 실제로 돌려 본 범위는
  [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md),
  공통 한계는 [호환성 안내](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)를
  보세요.

## 설치

저장소를 받은 뒤 바로가기(심볼릭 링크) 두 개를 만듭니다. 하나는 Codex용,
하나는 Claude Code용입니다. waygent도 같은 방식으로 링크합니다(waygent README 참고).

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
2. `waygent/<계획>` 브랜치에서 일하고, 기록은 `.waygent/<계획>/`에 둡니다(커밋하지
   않음): `progress.md`, `guide.md`, `reviews/`, 워커 실행마다 `attempts/` 폴더 하나.
3. 과제마다 새 워커와 브리프를 씁니다. 워커는 전체 계획을 읽지 않습니다. 실패하는
   테스트를 먼저 쓰고, 코드를 쓰고, `Waygent-Task: N`이 붙은 커밋으로 끝냅니다.
4. 종료 코드 0은 완료가 아닙니다. 호스트가 보고서, 실제 테스트 결과, 커밋, 도구
   기록(무엇을 읽고 실행했는지)을 확인한 뒤 호스트의 리뷰어가 한 번 리뷰하고, 같은
   워커가 High·Medium 지적을 한 번 고칩니다.
5. 그래도 실패한 과제는 새 XHigh 워커로 한 번 다시 합니다. 두 번째 실패면 원인을
   적고 멈춥니다.
6. `progress.md`에 과제마다 실제로 코드를 쓴 모델과 리뷰한 모델, 그 강도가 남습니다.
   예: `impl=grok:grok-4.7/high reviewer=claude-opus-5-5/high`. 무엇으로도 확인하지
   못한 값에는 `(requested)`가 붙습니다.
7. 계획 밖 작업은 먼저 묻습니다. push나 게시가 필요하면 `BLOCKED`로 멈춥니다.

호스트는 `run_worker.py wait`로 기다리며(한 번에 최대 9분), 워커가 도는 동안
턴을 끝내지 않습니다. 헤드리스 호스트는 턴이 끝나면 러너를 멈추기 때문입니다.
워커 진행 상황은 `run_worker.py status`로 봅니다. 세션 ID, 워커 생존
여부(`pid_alive`), 읽은 파일·검색·셸 목록만 짧게 보여 주며, 로그 전체는 붙여
넣지 않습니다.

| 상황 | 결과 | 다음 할 일 |
| --- | --- | --- |
| 워커가 `--idle-timeout` 동안 아무것도 출력하지 않음(기본 900초, `0`은 끔) | 워커 중지, `timed_out`, exit 124, `the worker wrote no output for 900 seconds` | 워크트리에 남은 변경을 확인하고, 그 세션을 잇지 말고, 이전 보고서와 커밋을 적은 브리프로 새 워커를 띄웁니다. |
| `--timeout` 초과(기본 `0`, 끔) | 워커 중지, `timed_out`, exit 124 | `status`와 보고서를 확인합니다. |
| 러너에 Ctrl-C 또는 SIGTERM | `interrupted`, 워커도 중지(SIGTERM, 10초 뒤 SIGKILL), exit 130 | 워커가 띄운 백그라운드 프로세스가 남았는지 `pgrep -f <worktree 경로>`로 확인합니다. 다른 프로세스의 API 키가 보일 수 있으니 `ps aux` 출력은 찍지 않습니다. 그다음 그 과제의 트레일러 커밋과 `report.md`가 이미 있지 않으면 그 워커의 세션을 이어 갑니다. 러너가 멈춘 것은 과제 실패가 아닙니다. |
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
