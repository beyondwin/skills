# SDDx

[English](README.en.md)

## 목적

Superpowers SDD는 지금 쓰는 Claude Code 또는 Codex가 진행하고, 구현만
Cursor CLI 또는 Grok CLI에 넘깁니다.

## 사용할 때와 사용하지 않을 때

구현 계획이 있고, 구현을 외부 Cursor/Grok에 맡길 때 씁니다.

설계·계획 작성, `pre-sdd-review`, 이 세션 안에서 직접 구현하기에는 쓰지
않습니다.

## 지원 호스트

sddx: Claude Code and Codex supported for local or repository-based use.

지원 호스트는 `claude-code`, `codex`입니다. Cursor와 Grok CLI는 구현만 맡는
외부 프로그램입니다. 계약에서는 이를 worker라고 부릅니다. 호스트가 아닙니다.

macOS에서 Claude Code·Codex와 Cursor·Grok의 네 조합은 실제로 돌려 보았습니다.
무엇을 확인했고 무엇을 아직 안 봤는지는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
표를 보세요. Claude.ai, Cowork, Skills API 업로드, marketplace 게시는
지원하지 않습니다. 공유 한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을
보세요.

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

구현 프로그램은 `sddx <plan-file> [cursor|grok|c|g]`에서 고릅니다. `c`는
cursor, `g`는 grok입니다. 요청에 없으면 이 계획에서 한 번만 묻습니다.
쓸 수 있는 프로그램이 하나뿐이어도 그 사실과 빠진 쪽의 이유를 보여 주고
확인한 뒤에 진행합니다. 요청한 쪽이 없으면 다른 쪽으로 바꾸지 않습니다.

작업자는 완결된 과제와 지정 자료만 받고 전체 계획은 다시 읽지 않습니다.
완료는 프로세스 종료 코드가 아니라 보고서, 실제 테스트, 커밋, 도구 기록,
네이티브 리뷰로 판단합니다. 실행 기록은 작업 폴더 `.superpowers/` 아래에
남습니다. 실행 중에도 `run_worker.py status`로 세션 ID, 프로세스 생존
여부, 읽은 파일·검색·셸 목록을 봅니다. 로그 전체를 붙여 넣지 않습니다.
명령과 판정 규칙은
[계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)을
보세요.

Grok linked worktree는 Python 3.11+가 필요합니다. Grok는 MCP 호출 도구를
끄고, `--disallowed-tools`와 `--deny`가 없으면 실행하지 않습니다. 지원 OS는
macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. Windows에서 제품 CLI는
거절합니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
