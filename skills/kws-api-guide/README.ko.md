# API Guide

Claude Code 에서 `/kws-api-guide` 로 직접 호출할 때만 사용합니다.
요청 내용이 맞아도 자동 활성화하지 않습니다.

[English](README.md)

## 목적

새로 생기거나 바뀐 API 를 다른 팀 개발자가 붙일 수 있게 안내 페이지 하나를 만듭니다.
읽는 사람은 웹, 앱, 서버 개발자 누구든 됩니다. 페이지에 적는 서버 사실은 모두 기록한
커밋의 서버 코드에서 읽고, 결과는 공유할 수 있는 Claude 아티팩트로 올립니다.

페이지 모양은 정해져 있습니다.

- 모든 API 공통 규칙, 표 두 개: 코드에서 처리할 것(인증, 응답 몸통, 오류)과 형식(타입, 날짜, 헤더)
- API 하나에 카드 하나, 늘 같은 순서: 요청, 응답, 오류, 호출하는 쪽 처리
- 업로드나 작업처럼 여러 단계인 흐름, 호출하는 쪽이 보는 상태별 표
- 호출하는 쪽 코드를 알려 주면 그쪽 할 일 표(선택)

문장은 짧은 글쓰기 규칙을 따릅니다. 표 칸에는 두 문장까지, 한국어는 한 문체로, 직역한 말 대신
읽는 팀이 쓰는 말로 씁니다.

## 사용할 때와 사용하지 않을 때

API 를 더하거나 바꾼 뒤, 다른 개발자가 그걸 붙여야 할 때 씁니다.

OpenAPI 파일 쓰기나 고치기, 스펙에서 레퍼런스 사이트 만들기, 코드 리뷰, 클라이언트
구현, 한 가지 동작 원리 설명(`/how-it-works`)에는 쓰지 않습니다.

## 지원 호스트

kws-api-guide: Claude Code supported for local or repository-based use.

호스트 id 는 `claude-code` 입니다. Artifact 도구와 서버 소스 읽기 권한이 필요합니다.
지금 설치 파일의 실제 실행은 아직 확인하지 않았습니다(`not_measured`). Codex, Grok,
Cursor 는 지원하지 않습니다.

Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다. 공통
한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을
보세요.

## 설치

저장소를 받은 뒤 스킬 폴더를 Claude Code 스킬 폴더에 링크합니다.

공개 경로: https://github.com/beyondwin/skills/tree/main/skills/kws-api-guide

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

<!-- kws-api-guide-local-links -->
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

`python3 - "$PWD/skills/kws-api-guide" "$HOME/.claude/skills/kws-api-guide" <<'PY'`

이 첫 줄 다음에 Python 블록을 그대로 붙이고, 마지막 줄에 `PY` 만 씁니다. source 와
target 의 따옴표는 그대로 둡니다.

업데이트와 제거는
[설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를
보세요.

## 첫 호출

서버 저장소에서 이름으로 부릅니다. 범위를 주지 않으면 지금 브랜치와 기본 브랜치의
차이를 다룹니다.

```text
/kws-api-guide
/kws-api-guide 내보내기 API, 앱 개발자용, 앱 코드는 ../mobile-app
```

## 예상 결과

비공개 Claude 아티팩트 하나와 짧은 채팅 보고가 나옵니다.

페이지 차례는 이렇습니다. 기본 경로, 날짜, 서버 커밋이 든 머리, 호출하는 쪽 코드를
줬을 때의 할 일 표, 공통 규칙, API 카드, 흐름, 대조한 파일을 적은 부록. 예시는 실행
중인 서버에서 받았으면 받은 것, 아니면 응답 타입으로 지은 것이라고 밝힙니다.

채팅 보고에는 무엇을 어느 커밋에서 확인했는지, 확인하지 못한 것(예: 배포 환경의 설정
값), OpenAPI 같은 계약 파일에서 찾은 빈 곳이 들어갑니다. 빈 곳은 알리기만 하고
고치지 않습니다.

공유는 페이지의 공유 메뉴에서 합니다. 페이지 링크를 주고 다시 부르면 같은 페이지를
고칩니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-api-guide/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-api-guide/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-api-guide/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/kws-api-guide/release.md)
