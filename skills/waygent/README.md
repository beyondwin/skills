# Waygent

[English](README.en.md)

## 목적

구현 계획을 과제 하나씩 끝까지 돌리는 가벼운 워크플로입니다. `/waygent`나
`$waygent`를 받은 세션(컨트롤러)은 코드를 직접 쓰지 않고, 과제마다 새 구현 서브에이전트를 하나 띄워
짧은 브리프와 공유 가이드 파일을 줍니다.

| 말 | 뜻 |
| --- | --- |
| 컨트롤러 | `/waygent` 또는 `$waygent`를 받은 세션입니다. 과제를 나눠 주고, 결과를 확인하고, 진행 파일을 적습니다. |
| 구현 서브에이전트 | 과제 하나를 테스트부터 쓰고 구현해 커밋하는 새 서브에이전트입니다. |
| 가이드 파일 | 테스트·린트 명령과 계획 전체 규칙을 한 번 적어 둔 `guide.md`입니다. 모든 구현 서브에이전트가 읽습니다. |
| 진행 파일 | 과제별 상태를 적는 `progress.md`입니다. 커밋하지 않습니다. |
| 리뷰 기록 | 리뷰어가 전체 지적을 적는 `reviews/task-N.md`, `reviews/final.md`입니다. 컨트롤러는 짧은 요약만 받습니다. |

## 사용할 때와 사용하지 않을 때

- 쓸 때: 과제가 여러 개인 구현을 맡길 때, 메시지에 `/waygent`를 적었을 때만
  씁니다. 계획 파일이 없으면 요청으로 과제 목록을 만들어 한 번 확인받습니다.
- 쓰지 않을 때: 브레인스토밍, 설계·스펙·계획 작성, 작은 수정 하나, `/sddx`,
  Superpowers `subagent-driven-development`.

## 지원 호스트

waygent: Claude Code, Codex, and Cursor Agent supported for local or repository-based use.
(Claude Code, Codex, Cursor Agent에서 로컬 또는 저장소 연결로 씁니다.)

- 호스트는 `claude-code`, `codex`, `cursor`입니다. 서브에이전트를 띄울 수 있는 호스트여야
  합니다. Codex는 `~/.codex/config.toml`에 `[features]` `multi_agent = true`를 켜야
  서브에이전트 도구(`spawn_agent`)를 씁니다.
- 실측: 2026-09-27에 Claude Code(opus, fable)와 Cursor Agent(grok-4.7-high)에서 돌렸습니다. 기록은 [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md)에 있고, Codex 측정 기록도 그 문서에 있습니다.
- OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다.
- Git 저장소 안에서만 씁니다.
- Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다.
  공통 한계는 [호환성 안내](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)를 보세요.

## 설치

저장소를 받은 뒤 바로가기(심볼릭 링크)를 만듭니다. Claude Code는
`~/.claude/skills`, Codex는 `~/.agents/skills`, Cursor Agent는 `~/.cursor/skills`에서 찾습니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills
```

아래 블록은 링크 하나를 만들고, 같은 링크가 이미 있으면 성공으로 봅니다. 다른
링크, 깨진 링크, 파일, 디렉터리는 자동으로 바꾸지 않고 멈추므로, 대상을 확인한
뒤 다시 실행하세요.

<!-- waygent-local-links -->
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

링크마다 한 번씩 실행합니다. 첫 줄은 Claude Code면
`python3 - "$PWD/skills/waygent" "$HOME/.claude/skills/waygent" <<'PY'`, Codex면
`python3 - "$PWD/skills/waygent" "$HOME/.agents/skills/waygent" <<'PY'`, Cursor
Agent면 `python3 - "$PWD/skills/waygent" "$HOME/.cursor/skills/waygent" <<'PY'`입니다.
다음 줄부터 위 블록을 그대로 붙이고 마지막 줄에 `PY`만 적습니다.

지울 때는 먼저 확인하고 그 링크만 지웁니다.

```bash
ls -ld ~/.claude/skills/waygent ~/.agents/skills/waygent ~/.cursor/skills/waygent
unlink ~/.claude/skills/waygent
unlink ~/.agents/skills/waygent
unlink ~/.cursor/skills/waygent
```

`$skill-installer` 형식의 공개 경로는 아래와 같지만, Codex는
`~/.agents/skills/waygent` 링크에서 이 스킬을 찾습니다. [Codex 설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-codex.md)의
세 스킬에는 들지 않으니 `~/.codex`에 복사본을 만들지 마세요.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/waygent
```

그 밖의 안내는 [로컬 링크](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를 보세요.

## 첫 호출

Claude Code와 Cursor Agent는 `/waygent`, Codex는 `$waygent`입니다. 계획 파일을
주거나, 계획 없이 요청을 적습니다.

```text
/waygent docs/plan.md
$waygent docs/plan.md
/waygent 로그인 폼에 비밀번호 표시 버튼을 추가해 줘
```

## 예상 결과

1. `main`이나 `master`에 있으면 `waygent/<계획이름>` 브랜치를 만듭니다. `main`,
   `master`에는 커밋하지 않고, push·merge·PR은 하지 않습니다.
2. 과제마다 새 구현 서브에이전트가 테스트를 먼저 쓰고 실패를 본 뒤 구현합니다.
   커밋에는 `Waygent-Task: N` 트레일러가 붙습니다.
3. 과제마다 리뷰를 한 번 하고, 찾은 문제는 한 번 고칩니다. 다시 리뷰하지 않습니다.
4. 마지막 과제 뒤에 전체 리뷰를 한 번 하고, 고친 뒤 테스트를 한 번 더 돌립니다.
5. 실패하면 먼저 원인을 한 줄로 적고 한 번만 다시 시도합니다. 두 번째 실패에서
   멈추고 보고합니다.
6. 구현 서브에이전트와 과제별 리뷰어는 이 세션과 같은 모델을 씁니다. 더 싼 모델이나
   낮은 effort로 바꾸지 않습니다. 호스트가 모델을 고를 수 있으면 최종 리뷰와 실패 뒤
   재시도만 한 등급 위 모델(Claude Code: sonnet → opus → fable)을 씁니다. Codex는
   모델 이름을 적지 않고 세션 모델을 물려받게 하며, 한 등급 위는 같은 모델에서
   `reasoning_effort`만 `xhigh`로 적습니다. 서브에이전트는 서브에이전트를
   또 띄우지 않습니다.

기록은 저장소 최상위 `.waygent/<계획이름>/`에 둡니다(`progress.md`, `guide.md`,
`reviews/`). `.waygent/.gitignore`(내용 `*`)가 폴더 전체를 git에서 빼므로 커밋되지
않고, 저장소의 `.gitignore`는 건드리지 않습니다.
다시 `/waygent`(Codex는 `$waygent`)를 부르면 이어서 합니다. 트레일러가 붙은 커밋이 있는 과제는 끝난
것으로 보고 다시 하지 않습니다. 커밋되지 않은 변경은 버리지 않고 새 구현
서브에이전트에게 넘깁니다. 사용량 한도에 걸리면 `paused: limit`을 적고 멈춥니다. `git clean -fdx`로 기록이
지워져도 트레일러 커밋에서 진행 파일을 다시 만듭니다.

일부러 하지 않는 것: 브레인스토밍·스펙 단계, 과제별 브리프 파일, 재리뷰 반복,
구현 서브에이전트 병렬 실행, 과제마다 사람 확인.

한계: 리뷰가 과제마다 한 번이라 고친 코드는 최종 리뷰에서만 다시 봅니다. 결과
품질은 모델과 계획에 달려 있습니다. 규칙은
[계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/contract.md)을 보세요.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/waygent/release.md)
