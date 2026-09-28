# How It Works

[English](README.md)

## 목적

한 가지 동작 원리를 채팅 답 하나로 설명합니다. 답에는 늘 Mermaid 도표와 번호
매긴 단계가 함께 나옵니다. 깊이는 넷 중 하나를 고르고, 고르지 않으면 그림으로
시작합니다.

- 그림: 한눈에 보는 전체 모습
- 길: 한 걸음씩 따라가는 흐름
- 뼈대: 안쪽 구조와 갈림길
- 허점: 이 그림이 어디서 맞지 않게 되는지

어느 깊이에서든 내용은 참으로 유지합니다. 귀여운 비유로 바꾸거나 어린이 말투로
낮추지 않습니다.

## 사용할 때와 사용하지 않을 때

무언가가 어떻게 돌아가는지 이해하고 싶을 때 씁니다.

디버깅, 구현, 리뷰, 번역, 한 줄 사실 조회, 어린이 말투 설명에는 쓰지 않습니다.
`/eli5`를 대신하지도 않습니다.

## 지원 호스트

how-it-works: Codex and Claude Code supported for local or repository-based use.

호스트 id는 `codex`, `claude-code`입니다. 지금 설치 파일의 실제 실행은 아직
확인하지 않았습니다(`not_measured`). Grok와 Cursor는 지원하지 않습니다.

Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다. 공통
한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을
보세요.

## 설치

저장소를 받은 뒤 스킬 폴더를 가리키는 링크를 두 개 만듭니다. 하나는 Codex용,
하나는 Claude Code용입니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

아래 Python 블록은 원본(source)과 링크 위치(target) 두 인자를 받아 링크를
만듭니다.

- 원본이 실제 스킬 폴더인지 먼저 확인합니다.
- 같은 링크가 이미 있으면 성공으로 봅니다.
- 다른 링크, 깨진 링크, 파일, 디렉터리는 자동으로 바꾸지 않습니다.
- 확인한 뒤 target이 새로 생겨도 멈춥니다. 살펴본 뒤 다시 실행하세요.

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

target마다 한 번씩, 두 번 실행합니다. 블록은 따옴표로 감싼 here-document
(`<<'PY'`)로 표준입력에 넣습니다.

- Codex:
  `python3 - "$PWD/skills/how-it-works" "$HOME/.agents/skills/how-it-works" <<'PY'`
- Claude Code:
  `python3 - "$PWD/skills/how-it-works" "$HOME/.claude/skills/how-it-works" <<'PY'`

첫 줄 다음에 위 Python 블록을 그대로 붙이고, 마지막 줄에 `PY`만 적어 닫습니다.
source와 target의 따옴표는 그대로 두세요.

Codex에서는 `$skill-installer`로 공개 GitHub 경로를 설치할 수도 있습니다. Codex는
`~/.agents/skills/how-it-works`에서 스킬을 찾으니 `~/.codex` 복사본은 만들지
마세요.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/how-it-works
```

갱신과 제거는
[설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를
보세요.

## 첫 호출

이름으로 부르려면 Codex에서는 `$how-it-works`, Claude Code에서는 `/how-it-works`를
씁니다. 주제만 적으면 기본 깊이인 그림으로 설명합니다.

```text
$how-it-works DNS
/how-it-works DNS
```

깊이를 고르려면 주제 뒤에 붙입니다.

```text
$how-it-works DNS 길
/how-it-works DNS 길
```

## 예상 결과

설명은 채팅 답 하나로 끝납니다. 호스트 페이지, Canvas, 브라우저, URL, 파일,
Mermaid 렌더러(도표를 그려 주는 도구)는 없어도 됩니다. 렌더러가 없어도 실패가
아닙니다.

답에는 다음 여섯 가지가 꼭 들어갑니다.

1. one-sentence claim — 무엇이 도는지 한 줄로
2. Mermaid — 도표
3. numbered hop list — 번호 매긴 단계
4. rung-specific body — 고른 깊이의 본문
5. adjacent slices — 이번 답에서 다루지 않은 옆 주제
6. one next move — 다음에 해 볼 일 하나

그림 깊이에서는 지도에 번호 단계(홉)가 Mermaid 소스보다 먼저 나오고, 본문은 그
단계를 다시 따라가지 않습니다.

답의 틀:

````markdown
# {slice} · {그림|길|뼈대|허점}

## 한 줄

## 지도

1. **H1** — {무엇이 움직이거나 바뀌는지}
2. **H2** — {무엇이 움직이거나 바뀌는지}

```mermaid
{도표 소스}
```

## 본문

## 지금 다루지 않은 것

다음: {다음 이동 하나}
````

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/how-it-works/release.md)
