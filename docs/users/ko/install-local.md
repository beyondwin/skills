# 로컬 링크

[English](../en/install-local.md) · [설치](installation.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md) · [검증](verification.md)

How It Works와 SDDx, 그리고 Grok에서 쓰는 Image Workbench는 이 저장소를 받은
뒤 스킬 폴더로 가는 바로가기(심볼릭 링크)를 겁니다. 스킬 폴더를 복사하지 않습니다.

순서는 세 스킬 모두 같습니다.

1. 저장소를 받고, 바로가기를 둘 폴더를 만듭니다.
2. 아래 Python 블록으로 바로가기를 겁니다. 바로가기(target)마다 한 번씩 실행합니다.
3. 새 대화에서 제품 README의 첫 호출을 씁니다.

## Python 블록이 하는 일

아래 Python은 how-it-works, sddx, image-workbench가 같습니다. 덮어쓰지 않는
바로가기를 만듭니다.

이 일회성 Python 블록은 source(스킬 폴더)와 target(바로가기 위치)을 인자로
받습니다. source가 실제 스킬 디렉터리인지 먼저 확인하고, 같은 링크는 성공으로
처리합니다. 다른 링크, 깨진 링크, 파일, 디렉터리는 자동으로 바꾸지 않습니다.
대상이 검사 뒤 생기는 경우에도 멈추므로 직접 확인한 뒤 다시 실행해야 합니다.

실행하는 법: 터미널에 각 절에 적힌 첫 줄(`python3 - ... <<'PY'`)을 쓰고, 다음
줄부터 Python 블록을 그대로 붙여 넣은 뒤, 마지막 줄에 `PY`만 씁니다. 이렇게
표준입력으로 넘기는 방식을 quoted here-document라고 합니다. source와 target
인자의 따옴표를 유지하세요.

## how-it-works

Codex와 Claude Code에서 씁니다. 공개 경로는 https://github.com/beyondwin/skills/tree/main/skills/how-it-works 입니다. 바로가기는 두 개입니다. 첫 링크는 Codex, 둘째는 Claude Code입니다. Codex는 `~/.agents/skills/how-it-works`에서 찾습니다. `~/.codex`나 `~/.grok` 복사본을 만들지 마세요.

1. 저장소를 받고 폴더를 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

2. 아래 블록을 target마다 따로 실행합니다.

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

Codex 호출은
`python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`,
Claude Code 호출은
`python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`로
시작합니다.

3. 첫 호출은 [`how-it-works` README](../../../skills/how-it-works/README.md)를 보세요. 호스트마다 따로 복사하지 마세요.

## sddx

Codex와 Claude Code에서 씁니다. 공개 경로는 https://github.com/beyondwin/skills/tree/main/skills/sddx 입니다. 바로가기는 두 개입니다. 첫 링크는 Codex, 둘째는 Claude Code입니다. Codex는 `~/.agents/skills/sddx`에서 찾습니다. `~/.codex`나 `~/.grok` 복사본을 만들지 마세요.

1. 저장소를 받고 폴더를 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

2. 아래 블록을 target마다 따로 실행합니다.

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

Codex 호출은
`python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<'PY'`,
Claude Code 호출은
`python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<'PY'`로
시작합니다.

3. 첫 호출은 [`sddx` README](../../../skills/sddx/README.md)를 보세요. 호스트마다 따로 복사하지 마세요.

## image-workbench

Grok에서 쓸 때만 이 방법을 씁니다. Codex는 [Codex 설치](install-codex.md)를 따릅니다. 공개 경로는 https://github.com/beyondwin/skills/tree/main/skills/image-workbench 입니다. 바로가기는 하나입니다. Grok는 `~/.agents/skills/image-workbench`에서 찾습니다. `~/.grok`나 `~/.codex`에 복사본을 만들지 마세요.

1. 저장소를 받고 폴더를 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

2. 아래 블록을 한 번 실행합니다. 스킬 폴더가 맞는지 확인하고, 이미 같은 바로가기가
있으면 그대로 둡니다. 다른 바로가기나 파일이 있으면 덮어쓰지 않습니다.

<!-- image-workbench-local-links -->
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

첫 줄은
`python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`
입니다.

3. 첫 호출은 [`image-workbench` README](../../../skills/image-workbench/README.md)를 보세요. 복사본을 만들지 마세요.

## 갱신과 제거

제거할 때는 `ls -ld`로 먼저 확인한 뒤 그 링크만 지웁니다.

`how-it-works` 링크:

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

`sddx` 링크:

```bash
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx
```

`image-workbench` 링크:

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

상위 `skills` 디렉터리나 홈 디렉터리를 지우지 마세요. 설치·갱신·제거는 정확한 대상만 다룹니다. 원격 스크립트를 셸에 파이프하지 마세요. 대상을 확인하지 않고 덮어쓰지 마세요. 기존 설치를 자동으로 바꾸지 마세요.
