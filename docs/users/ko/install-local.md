# 로컬 링크

[English](../en/install-local.md) · [설치](installation.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md) · [검증](verification.md)

How It Works, SDDx, Waygent, 그리고 Grok에서 쓰는 Image Workbench는 복사하지 않습니다. 저장소를 한 번 클론하고, 각 호스트의 스킬 폴더에서 클론 안 스킬 폴더로 가는 링크(심볼릭 링크)를 겁니다. 그러면 클론에서 `git pull` 한 번으로 모든 호스트가 함께 갱신됩니다.

아래 절은 모두 같은 세 단계입니다.

1. 저장소를 클론하고 호스트 폴더를 만듭니다.
2. 링크마다 Python 블록을 한 번 실행합니다.
3. 새 대화에서 제품 README의 첫 호출을 써 봅니다.

## Python 블록 실행법

블록은 모든 절에서 같습니다. 인자는 둘입니다. 스킬 폴더(source)와 링크를 둘 곳(target)입니다. source가 스킬 폴더인지 확인하고, 같은 링크가 이미 있으면 성공으로 봅니다. 다른 링크, 깨진 링크, 파일, 폴더는 절대 바꾸지 않습니다. 실행 중에 target에 무언가 생기면 멈춥니다. target을 확인한 뒤 다시 실행하세요.

터미널에 절마다 적힌 첫 줄(`python3 - ... <<'PY'`)을 쓰고, 다음 줄부터 블록을 그대로 붙여 넣은 뒤, 마지막 줄에 `PY`만 씁니다. 두 인자의 따옴표는 그대로 두세요.

## how-it-works

Codex와 Claude Code용입니다. 공개 경로: https://github.com/beyondwin/skills/tree/main/skills/how-it-works. 링크는 두 개입니다. Codex는 `~/.agents/skills/how-it-works`, Claude Code는 `~/.claude/skills/how-it-works`를 읽습니다. `~/.codex`나 `~/.grok`에 복사본을 만들지 마세요. SDDx는 waygent 위에서 돌아가므로 `waygent`도 같은 방식으로 링크하세요(해당 절 참고).

1. 클론하고 폴더를 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

2. 링크마다 블록을 한 번 실행합니다.

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

- Codex: `python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`
- Claude Code: `python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`

3. 첫 호출은 [`how-it-works` README](../../../skills/how-it-works/README.ko.md)를 보세요.

## sddx

Codex와 Claude Code용입니다. 공개 경로: https://github.com/beyondwin/skills/tree/main/skills/sddx. 링크는 두 개입니다. Codex는 `~/.agents/skills/sddx`, Claude Code는 `~/.claude/skills/sddx`를 읽습니다. `~/.codex`나 `~/.grok`에 복사본을 만들지 마세요. SDDx는 waygent 위에서 돌아가므로 `waygent`도 같은 방식으로 링크하세요(해당 절 참고).

1. 클론하고 폴더를 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

2. 링크마다 블록을 한 번 실행합니다.

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

- Codex: `python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<'PY'`
- Claude Code: `python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<'PY'`

3. 첫 호출은 [`sddx` README](../../../skills/sddx/README.ko.md)를 보세요.

## waygent

Claude Code, Codex, Cursor Agent, Grok Build용입니다. 공개 경로: https://github.com/beyondwin/skills/tree/main/skills/waygent. 쓰는 호스트마다 링크를 하나씩 겁니다. Claude Code는 `~/.claude/skills/waygent`, Codex는 `~/.agents/skills/waygent`, Cursor Agent는 `~/.cursor/skills/waygent`를 읽습니다. Grok Build는 셋 중 어느 것이든 읽으므로 링크를 따로 걸 필요가 없습니다. `~/.codex`에 복사본을 만들지 마세요. Codex는 `~/.codex/config.toml`의 `[features]`에 `multi_agent = true`도 있어야 합니다.

1. 클론하고 폴더를 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills
```

2. 링크마다 블록을 한 번 실행합니다.

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

- Claude Code: `python3 - "$PWD/skills/waygent" "$HOME/.claude/skills/waygent" <<'PY'`
- Codex: `python3 - "$PWD/skills/waygent" "$HOME/.agents/skills/waygent" <<'PY'`
- Cursor Agent: `python3 - "$PWD/skills/waygent" "$HOME/.cursor/skills/waygent" <<'PY'`

3. 첫 호출은 [`waygent` README](../../../skills/waygent/README.ko.md)를 보세요.

## image-workbench

Grok용입니다. 공개 경로: https://github.com/beyondwin/skills/tree/main/skills/image-workbench. `~/.agents/skills`에 링크 하나를 겁니다. Codex도 이 폴더를 읽으므로 두 호스트를 다 쓰면 이 링크 하나로 충분하고, `$skill-installer`로 Codex 사본을 또 설치하지 마세요. Codex만 쓴다면 대신 [Codex 설치](install-codex.md)를 따르세요. `~/.grok`나 `~/.codex`에 복사본을 만들지 마세요.

1. 클론하고 폴더를 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

2. 블록을 한 번 실행합니다.

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

- Grok: `python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`

3. 첫 호출은 [`image-workbench` README](../../../skills/image-workbench/README.ko.md)를 보세요.

## 갱신과 제거

갱신은 클론에서 `git pull`을 하면 됩니다. 링크가 바뀐 내용을 그대로 씁니다. 제거할 때는 `ls -ld`로 링크를 먼저 확인한 뒤 그 링크만 지웁니다.

```bash
# how-it-works
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works

# sddx
ls -ld ~/.agents/skills/sddx ~/.claude/skills/sddx
unlink ~/.agents/skills/sddx
unlink ~/.claude/skills/sddx

# waygent
ls -ld ~/.claude/skills/waygent ~/.agents/skills/waygent ~/.cursor/skills/waygent
unlink ~/.claude/skills/waygent
unlink ~/.agents/skills/waygent
unlink ~/.cursor/skills/waygent

# image-workbench
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

상위 `skills` 폴더나 홈 폴더를 지우지 마세요. 원격 스크립트를 셸에 파이프하지 말고, 확인하지 않은 설치를 바꾸지 마세요.
