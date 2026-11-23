# KWS Book Writer

Claude Code 에서 `/kws-book-writer` 로 직접 호출할 때만 사용합니다.
요청 내용이 맞아도 자동 활성화하지 않습니다.

[English](README.md)

## 목적

한국어 기술서나 논픽션 책의 초고를 사용자가 고른 작업 폴더에 씁니다. 정해진 단계를
따르고, 작업 파일은 모두 그 폴더에 남깁니다.

- 기획(`brief.md`)과 출처를 적은 조사 장부(`research/ledger.md`)
- 장 계획(`plan.md`). 사용자가 승인해야 본문을 쓰기 시작합니다.
- 첫 장 보정(기본으로 켜짐): 첫 장을 읽고 바꿀 점을 말하면 `voice.md` 에 기록합니다.
  끝까지 쓰라고 하면 건너뜁니다.
- 나머지 장(`chapters/NN.md`)은 순서대로, 장마다 새 서브에이전트가 씁니다. 묶음마다
  사실 확인을 하고, 고친 문장의 전과 후를 `checks/factcheck.md` 에 남깁니다.
- `manuscript.md` 로 합치고 `scripts/book_check.py` 로 기계 검사
- 새 서브에이전트의 수용 판정(ACCEPT 또는 BLOCK), 고치기 한 번, 그다음 사용자의 결정을
  기록

책 메타데이터는 `book.json` 에 둡니다. 결과물은 Markdown 입니다.

## 사용할 때와 사용하지 않을 때

한국어 기술서나 논픽션 책의 첫 초고 전체가 필요하고, 장 계획 승인과 첫 장 검토를 직접
할 수 있을 때 씁니다.

글 한 편이나 블로그 글, 이미 쓴 한국어 글의 교정·교열(`korean-writing-editor`), 한
가지 동작 원리 설명(`/how-it-works`), 소설, 번역, EPUB 이나 인쇄용 파일 만들기에는 쓰지
않습니다. EPUB 빌드는 아직 들어 있지 않습니다.

## 지원 호스트

kws-book-writer: Claude Code supported for local or repository-based use.

호스트 id 는 `claude-code` 입니다. 서브에이전트, 작업 폴더 쓰기 권한, 그리고
`scripts/book_check.py` 를 돌릴 Python 3 이 필요합니다. 이 스크립트는 표준 라이브러리만
씁니다. macOS 실제 실행 기록은 저장소의 평가 기록에 있습니다. 최종 설치 파일로 처음부터 끝까지 돌려 보지는 않았습니다. Codex,
Grok, Cursor 는 지원하지 않습니다.

Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다. 공통
한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을
보세요.

## 설치

저장소를 받은 뒤 스킬 폴더를 Claude Code 스킬 폴더에 링크합니다.

공개 경로: https://github.com/beyondwin/skills/tree/main/skills/kws-book-writer

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.claude/skills
```

아래 Python 블록은 원본(source)과 링크 위치(target) 두 인자를 받아 링크를
만듭니다.

- 원본이 실제 스킬 폴더인지 먼저 확인합니다.
- 같은 링크가 이미 있으면 성공으로 봅니다.
- 다른 링크, 깨진 링크, 파일, 디렉터리는 자동으로 바꾸지 않습니다.
- 확인한 뒤 target 이 새로 생겨도 멈춥니다. 살펴본 뒤 다시 실행하세요.

<!-- kws-book-writer-local-links -->
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

따옴표 친 here-document(`<<'PY'`)로 블록을 표준 입력에 넣습니다.

`python3 - "$PWD/skills/kws-book-writer" "$HOME/.claude/skills/kws-book-writer" <<'PY'`

이 첫 줄 다음에 Python 블록을 그대로 붙이고, 마지막 줄에 `PY` 만 씁니다. source 와
target 의 따옴표는 그대로 둡니다.

업데이트와 제거는
[설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를
보세요.

## 첫 호출

책을 쓸 빈 폴더에서 Claude Code 를 열거나 폴더를 알려 주고, 주제와 독자를 붙여
이름으로 부릅니다.

```text
/kws-book-writer
/kws-book-writer 백엔드 개발자를 위한 PostgreSQL 인덱스 책, 10장 안팎
```

## 예상 결과

작업 폴더에 `brief.md`, `research/ledger.md`, `plan.md`, `voice.md`, `chapters/NN.md`,
`checks/`, `book.json`, `manuscript.md` 가 생기고, 짧은 채팅 보고가 나옵니다.

중간에 두 번 멈춥니다. 장 계획 승인 때, 그리고 끝까지 쓰라고 하지 않았다면 첫 장을
쓴 뒤입니다. 마지막 채팅 보고에는 검사 결과, 수용 판정(ACCEPT 또는 BLOCK), 고치기
단계에서 고친 것, 사용자가 정할 남은 일이 들어갑니다.

`book_check.py check` 는 남은 표식, 수용 뒤 바뀐 원고(SHA-256 이
`checks/acceptance.json` 과 다름), 잘못된 `book.json` 메타데이터, `manuscript.md` 와
다른 장 파일에서 실패합니다. `--final` 이면 통과 판정이 없을 때도 실패합니다. 코드 밖에
남은 자리표시, 장 사이 상호 참조, 분량 비율, 출처 없는 숫자, 용어 표기 차이, 제목 구조,
독자에게 보이는 작업 용어, 렌더링되지 않는 굵은 글씨, 책 전체에서 되풀이되는
도입·마무리 문장은 실패시키지 않고 보고합니다.

원고는 초고입니다. 사실 확인에서 출처를 찾지 못한 내용은 숨기지 않고 보고합니다. 작업
폴더는 사용자의 원고이므로 비공개로 두세요.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-book-writer/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-book-writer/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-book-writer/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-book-writer/release.md)
