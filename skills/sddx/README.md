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
구현 worker이지 호스트가 아닙니다. 이전 Codex/Grok linked-worktree 검사에서
직접 커밋·세션 재개·설정 복원은 성공했지만, 후속 검사에서 전체 계획 읽기와
보고 누락이 재현됐습니다. 버전별 관측과 한계는 아래 테스트 문서에 기록합니다. Cursor worker와 Claude Code host 실행은 `not_measured`입니다.
이 결과는 측정한 fixture와 버전의 범위 제한된 증거입니다. Claude.ai, Cowork,
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

argv가 있으면 그 backend로 진행하고, 없으면 이 계획에서 한 번만
backend를 고릅니다. 그다음 Superpowers SDD를 외부 implementer와 네이티브
리뷰어로 실행합니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
