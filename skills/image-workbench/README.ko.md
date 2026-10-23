# Image Workbench

[English](README.md)

## 목적

프로젝트에 넣을 PNG, JPG 같은 비트맵 이미지를 기획·생성·편집·비교·점검합니다.
프로젝트에 안 맞거나 주어진 조건을 어긴 결과는 쓰지 않습니다.

## 사용할 때와 사용하지 않을 때

프로젝트에 넣을 이미지가 필요할 때 씁니다.

다음에는 쓰지 않습니다.

- 재미로 한 장만 그리는 일
- SVG나 코드로 만드는 UI
- 데이터 차트
- 실제 화면 구현
- 외부 프롬프트 모음 베끼기

## 지원 호스트

image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.

지금은 `codex`와 `grok`에서 씁니다. 그림을 만들거나 고치려면 지금 쓰는
프로그램(호스트)에 그림 도구가 있고, 결과를 열어 볼 수 있어야 합니다. 한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을 보세요.

## 설치

Codex에서는 공개 GitHub 주소를 `$skill-installer`에 넣습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

자세한 Codex 설치는 [Codex 설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-codex.md)를 보세요.

Grok에서는 이 저장소를 받은 뒤, Grok가 스킬을 찾는 폴더에 바로가기(심볼릭
링크) 하나만 만듭니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills
```

아래 Python 코드가 바로가기를 만듭니다. 원본이 스킬 폴더인지 먼저 확인합니다.
같은 바로가기가 이미 있으면 그대로 둡니다. 다른 바로가기나 파일, 폴더가 있으면
덮어쓰지 않습니다.

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

터미널에서 한 번 실행합니다.

1. 첫 줄: `python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'`
2. 다음 줄부터: 위 Python 코드를 그대로 붙여 넣습니다.
3. 마지막 줄: `PY`

경로 따옴표는 빼지 마세요.

지울 때는 바로가기인지 먼저 확인합니다.

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

Codex도 `~/.agents/skills`를 읽으므로 이 링크 하나로 Codex와 Grok에서 모두
씁니다. 두 호스트를 다 쓴다면 한 가지만 설치하세요. 이 링크를 쓰거나, Codex만
쓴다면 `$skill-installer`를 씁니다. 둘 다 설치하면 Codex에 두 번 나옵니다.

`~/.grok`나 `~/.codex`에 복사본을 만들지 마세요. 같은 방법이
[로컬 링크](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)에도
있습니다.

## 첫 호출

설치한 뒤 다음 대화에서 부릅니다. Codex는 `$image-workbench`, Grok는
`/image-workbench`입니다.

```text
$image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
/image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
```

## 첫 결과의 완성도를 높이려면

이미지를 넣을 화면, 피사체, 비워 둘 영역, 끝까지 보여야 할 부분을 먼저 알려 주세요.
그다음 재질과 빛을 지정합니다. 히어로라면 HTML 문구와 피사체가 각각 어느 쪽에
있는지 적습니다. 물체가 여러 개라면 개수만 구분하면 되는지, 각각의 윤곽 전체가
보여야 하는지도 구분합니다. 스타일 수식어를 늘리는 것만으로는 이 차이가 해결되지
않습니다.

스킬은 상세한 첫 프롬프트를 유지하고 결과를 원래 요청과 대조합니다. 구도나 가림에
실패했다면 시점이나 배치를 표적으로 고칠 수 있습니다.
생성 전에 도구가 지원하는 캔버스 값을 확인합니다. 요청 비율에 맞춰 자르거나
여백을 붙여야 한다면 그 변환을 알리고 최종 이미지를 다시 확인합니다. 이 과정에서
주어진 조건이 깨진 결과는 수용하지 않습니다.

수정할 때는 보이는 실패와 그대로 둘 부분을 짚어 주세요. 여러 번 시도하려면 이미지
호출 예산을 정합니다. 명시한 도구 호출 예산에는 거절된 호출도 포함됩니다.
파일 검사를 통과하거나 보기 좋다는 이유만으로 모든 조건을 충족한 것은 아닙니다.

이 스킬은 프로젝트에 넣을 이미지의 작업 절차를 관리하며, 호스트의 일반 생성보다
더 아름다운 결과를 보장하지 않습니다. 로컬 비교에서 지침을 늘려도 일관된 미적
우위는 확인되지 않았습니다. 에이전트의 시각 검수도 가림을 놓치고 보이는 부분의
개수를 잘못 셌습니다. 개수나 전체 가시성이 중요한 최종 이미지는 직접 확인하거나
독립된 검수자가 실제 이미지를 보게 하세요. 같은 모델이 다시 확신한다고 해서
독립적인 확인이 된 것은 아닙니다.

보정할 때 스킬은 원래 그리기 요청 전체를 유지하고 필요한 변경만 덧붙입니다.
호출 전에 피사체, 개수, 가시성, 구도, 재질, 빛, 금지 조건과 화면비가 남았는지
확인하고, 결과에서 원래 필수 조건을 전부 다시 검사합니다. 호출 예산을 정하고
실패 후보도 남깁니다. 추가 시도에서 새 결함이 생길 수 있으므로 원래 조건을
통과한 후보 중에서 고릅니다.

Grok 보정 비교 한 쌍에서는 기존 절차가 금지 조건을 빠뜨려 출력에 글자가
생긴 반면, 개선 절차는 조건을 보존하고 사용 가능한 결과를 만들었습니다.
한 번 확인한 결함 수정이며 미적 우위를 보장하지 않습니다. 확대 보기와 검수
순서를 바꾼 개수·가림 개선안 세 개는 실패해 설치본에 넣지 않았습니다.
개수나 완전한 윤곽이 필수인 결과는 독립된 시각 검수를 함께 사용하세요.

조건 보존만 남긴 최종판도 새 후보 12장 중 정상 후보 3장을 잘못 탈락시켜,
기존판의 2장보다 나빴습니다. 두 버전 모두 실패 후보 2장은 정확히 거절했지만
최종 선택 검증의 비퇴행 기준은 통과하지 못했습니다. 이번 수정은 조건 보존을
위해 유지하며, 전체 검수 절차가 개선됐다고 주장하지 않습니다.

## 예상 결과

먼저 모드를 하나만 고릅니다.

- `brief`: 어떤 이미지가 필요한지 정리만 합니다. 만들지 않습니다.
- `generate`: 새 이미지를 만듭니다.
- `edit`: 있는 이미지를 고칩니다.
- `audit`: 점검만 합니다. 만들지 않습니다.

`brief`와 `audit`은 읽기 전용입니다. 생성·편집 요청이 분명할 때만 이미지를
만듭니다.

프로젝트에 넣을 최종 파일은
`python3 <skill-root>/scripts/inspect_asset.py <absolute-asset-path>`로
확인합니다. `<skill-root>`는 설치된 스킬 폴더입니다. 보고서에는 형식, 너비,
높이, 알파, 바이트 크기, SHA-256, `extension_matches`(파일 확장자가 실제 형식과
맞는지), `trailing_bytes`(이미지 끝 뒤에 붙은 바이트 수)가 나옵니다. 대화 창에만
보이는 미리보기 경로는 최종 파일이 아닙니다. Grok는 투명도 없는 JPEG를
돌려주므로 결과의 `.jpg` 확장자를 그대로 둡니다.

이 검사는 PNG·JPEG·WebP의 기본 구조만 봅니다. 통과해도 그림이 좋다거나, 파일을
끝까지 읽었다거나, 써도 될 권리가 있다는 뜻은 아닙니다. 최종 후보는 반드시
열어서 확인합니다. `--output`에는 스킬 폴더 밖의 절대 경로를 줍니다. 이미 있는
JSON 보고서나 빈 파일만 갱신하고, 이미지 파일 이름, 입력 이미지나 다른 이미지,
그 밖의 파일은 거부하며, 실패하면 출력 경로를 알려 줍니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/release.md)
