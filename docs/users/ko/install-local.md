# 로컬 링크

[English](../en/install-local.md) · [설치](installation.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md) · [검증](verification.md)

`how-it-works`는 저장소를 받은 뒤 바로가기 두 개를 겁니다. 공개 경로는 https://github.com/beyondwin/skills/tree/main/skills/how-it-works 입니다. 첫 링크는 Codex, 둘째는 Claude Code입니다. Codex는 `~/.agents/skills/how-it-works`에서 찾습니다. `~/.codex`나 `~/.grok` 복사본을 만들지 마세요.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

아래 일회성 Python 블록은 source와 target을 인자로 받습니다. source가 실제 스킬
디렉터리인지 먼저 확인하고, 같은 링크는 성공으로 처리합니다. 다른 링크, 깨진 링크,
파일, 디렉터리는 자동으로 바꾸지 않습니다. 대상이 검사 뒤 생기는 경우에도 멈추므로
직접 확인한 뒤 다시 실행해야 합니다.

<!-- how-it-works-local-links -->
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
`python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`,
Claude Code 호출은
`python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`로
시작합니다. 각 호출의 다음 줄에 위 Python 블록을 그대로 넣고 마지막 줄을 `PY`로
닫습니다. source와 target 인자의 따옴표를 유지하세요.

호스트마다 따로 복사하지 마세요. 첫 호출은 [`how-it-works` README](../../../skills/how-it-works/README.md)를 보세요.

## sddx

`sddx`는 저장소를 받은 뒤 바로가기 두 개를 겁니다. 공개 경로는 https://github.com/beyondwin/skills/tree/main/skills/sddx 입니다. 첫 링크는 Codex, 둘째는 Claude Code입니다. Codex는 `~/.agents/skills/sddx`에서 찾습니다. `~/.codex`나 `~/.grok` 복사본을 만들지 마세요.

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

호스트마다 따로 복사하지 마세요. 첫 호출은 [`sddx` README](../../../skills/sddx/README.md)를 보세요.

## 갱신과 제거

`how-it-works` 링크는 확인한 뒤에만 제거합니다.

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

`sddx` 링크는 확인한 뒤에만 제거합니다.

```bash
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx
```

상위 `skills` 디렉터리나 홈 디렉터리를 지우지 마세요. 설치·갱신·제거는 정확한 대상만 다룹니다. 원격 스크립트를 셸에 파이프하지 마세요. 대상을 확인하지 않고 덮어쓰지 마세요. 기존 설치를 자동으로 바꾸지 마세요.
