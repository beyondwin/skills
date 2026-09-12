# Image Workbench

[English](README.en.md)

## 목적

이 프로젝트에 넣을 PNG, JPG 같은 비트맵 이미지를 기획하고, 만들고, 고치고,
비교하고, 점검합니다. 프로젝트에 안 맞거나 주어진 조건을 어기는 결과는
쓰지 않습니다.

## 사용할 때와 사용하지 않을 때

프로젝트에 넣을 이미지가 필요할 때 씁니다.

재미로 한 장만 그리는 일, SVG나 코드로 만드는 UI, 실제 화면 구현, 외부
프롬프트 모음 베끼기에는 쓰지 않습니다.

## 지원 호스트

image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.

지원 호스트 id는 `codex`, `grok`입니다. 생성·편집은 현재 호스트의 내장 이미지
도구와 로컬 이미지 보기가 필요합니다. 공유 한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을 보세요.

## 설치

Codex에서는 공개 GitHub 경로를 `$skill-installer`에 전달합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

나머지 Codex 설치 방법은 [설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-codex.md)를 보세요.

Grok에서는 저장소를 클론한 뒤 `~/.agents/skills`에 링크 하나를 겁니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

아래 일회성 Python 블록은 source와 target을 인자로 받습니다. source가 실제 스킬
디렉터리인지 먼저 확인하고, 같은 링크는 성공으로 처리합니다. 다른 링크, 깨진 링크,
파일, 디렉터리는 자동으로 바꾸지 않습니다. 대상이 검사 뒤 생기는 경우에도 멈추므로
직접 확인한 뒤 다시 실행해야 합니다.

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

이 블록을 quoted here-document의 표준입력으로 넣고 한 번 실행합니다. 호출은
`python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`로
시작합니다. 다음 줄에 위 Python 블록을 그대로 넣고 마지막 줄을 `PY`로 닫습니다.
source와 target 인자의 따옴표를 유지하세요.

링크는 확인한 뒤에만 제거합니다.

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

`~/.grok`나 `~/.codex` 복사본을 만들지 마세요. 나머지 로컬 링크 방법은
[설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를
보세요.

## 첫 호출

설치 다음 대화에서 이렇게 부릅니다. Codex는 `$image-workbench`, Grok는
`/image-workbench`입니다.

```text
$image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
/image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
```

## 예상 결과

먼저 모드를 하나만 고릅니다. `brief`는 어떤 이미지가 필요한지 정리만 하고
만들지 않습니다. `generate`는 새 이미지를 만듭니다. `edit`는 있는 이미지를
고칩니다. `audit`은 점검만 하고 만들지 않습니다. `brief`와 `audit`은 읽기
전용입니다. 생성·편집 요청이 분명할 때만 이미지를 만듭니다.

최종 파일은 스킬 폴더에서 `python3 scripts/inspect_asset.py`로 파일 형식과
크기를 확인합니다.

검사기는 PNG·JPEG·WebP의 필수 구조만 확인합니다. 통과해도
파일을 끝까지 해석했거나, 그림이 좋아 보이거나, 써도 되는 권리가
있다는 뜻은 아닙니다. 최종
후보는 반드시 열어서 확인합니다. `--output facts.json`은 별도 JSON 보고서를
갱신할 수 있지만 입력 이미지와 같은 파일을 가리키면 쓰기 전에 거부합니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/release.md)
