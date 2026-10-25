# Grok Image

Grok에게 정지 이미지를 부탁할 때 쓰는 스킬입니다. 맞는 요청이면 켜집니다. `$grok-image` 또는 `/grok-image`로도 부를 수 있습니다.

[English](README.md)

## 목적

요청을 한 장면으로 적고, 빛과 카메라와 장소는 채웁니다. 주제, 개수, 넣을 글자, 실존 인물이 빠졌을 때만 질문을 하나 합니다. 그다음 정지 이미지 한 장을 만들고, 적은 대상이 나왔는지 확인합니다.

## 사용할 때와 사용하지 않을 때

새 정지 이미지나 한 장의 수정에 씁니다.

프로젝트에 저장하고 검사해야 하는 이미지는 image-workbench입니다. 영상, SVG, 차트, 화면 코드, 프롬프트 모음에는 쓰지 않습니다.

## 지원 호스트

grok-image: Grok supported; still generation uses the host's built-in image tool and local image viewing.

호스트 id는 `grok`입니다. Codex, Claude Code, Cursor는 지원하지 않습니다. 현재 설치본의 자동 호출 확인은 `not_measured`입니다. 프롬프트 절차는 2026-10-25에 Grok 정지 이미지로 확인했습니다.

Claude.ai, Cowork, Skills API 업로드, 마켓플레이스 게시는 지원하지 않습니다.

## 설치

저장소를 클론하고 `~/.agents/skills`에 링크를 겁니다. `~/.grok`나 `~/.codex`에 복사본을 만들지 마세요.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

<!-- grok-image-local-links -->
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

한 번만 실행합니다. 첫 줄은 다음과 같습니다.

`python3 - "$PWD/skills/grok-image" "$HOME/.agents/skills/grok-image" <<'PY'`

그 다음 줄부터 Python 블록을 붙이고, 마지막 줄에 `PY`만 씁니다.

Codex에서는 공개 GitHub 경로로도 설치할 수 있습니다. 그 설치는 Grok 지원이 아닙니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/grok-image
```

갱신과 제거는
[설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를 보세요.

링크를 확인한 뒤 제거합니다.

```bash
ls -ld ~/.agents/skills/grok-image
unlink ~/.agents/skills/grok-image
```

## 첫 호출

평범한 말로 부탁하거나 스킬 이름을 붙입니다.

```text
밝은 여름 채식 그릭 샐러드 사진.
$grok-image 밝은 여름 채식 그릭 샐러드 사진.
/grok-image 밝은 여름 채식 그릭 샐러드 사진.
```

## 예상 결과

정지 이미지 한 장입니다. 답에는 경로와, 프롬프트에 적은 주제·개수·재질이 그림에 있는지 적습니다. 적은 항목이 하나 빠지면 한 번만 다시 만들고 멈춥니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [변경 이력](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-image/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-image/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-image/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-image/release.md)
