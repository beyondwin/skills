# 시작하기

[English](../en/getting-started.md) · [호환성](compatibility.md) · [개인정보와 권리](privacy-and-rights.md) · [평가](evaluation.md)

버전 `2.0.0`의 설치 가능한 페이로드는 `skills/korean-writing-editor`와 `skills/image-workbench`뿐입니다. 라이선스는 Apache-2.0입니다.

## 기본 설치 (Codex)

공개 GitHub 스킬 경로와 `$skill-installer`를 씁니다. 대상이 이미 있으면 설치기는 중단합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

기본 설치 위치는 `$CODEX_HOME/skills/<skill-name>`이며, `CODEX_HOME`이 없으면 `~/.codex/skills`입니다. 설치 후 새 대화에서 호출하세요.

```text
$korean-writing-editor 오탈자만 고쳐줘: (한국어 원문)
$image-workbench 생성하지 말고 이 자산 브리프만 정리해줘.
```

## 선택적 제3자 설치기

한국어 편집기만 해당합니다.

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

이 `npx` 명령은 제3자 설치기이며 자체 릴리스와 텔레메트리 정책을 따릅니다. `image-workbench`는 Codex 전용이라 이 경로로 지원하지 않습니다.

## Git 클론과 호스트 폴더 설치

`npx`를 쓰지 않을 때는 저장소를 클론한 뒤, 호스트가 기대하는 스킬 폴더에 검증된 디렉터리만 복사합니다.

```bash
git clone https://github.com/beyondwin/skills.git
SKILL_SOURCE="$PWD/skills/korean-writing-editor"
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_SOURCE"
ls -ld "$SKILL_TARGET"
```

`$SKILL_TARGET`이 없거나, 이 스킬의 안전한 링크임이 확인된 경우에만 복사하세요. 이미 있는 실제 디렉터리는 덮어쓰지 말고 중단하세요. `image-workbench`도 같은 방식으로 정확한 폴더만 다룹니다.

다른 호스트 폴더는 `korean-writing-editor`의 Agent Skills 계약 이식 대상일 뿐입니다. 기록된 smoke가 있기 전에는 지원이라고 말하지 마세요.

## 갱신과 제거

갱신·제거 전에 정확한 대상을 확인하세요.

```bash
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_TARGET"
```

확인 항목:

- 경로가 이 스킬 이름과 일치하는가
- 실제 디렉터리인가, 심볼릭 링크인가, 다른 목적지를 가리키는가
- `SKILL.md`의 `name`과 `metadata.version`이 기대한 값인가

이 스킬임이 확인된 뒤에만 호스트의 일반 제거 방법으로 그 경로만 지우거나, 대상을 치운 뒤 `$skill-installer`로 다시 설치하세요. 상위 `skills` 디렉터리나 홈 디렉터리를 지우지 마세요. 기존 설치를 확인 없이 교체하지 마세요.

`image-workbench`도 같은 확인 순서를 `.../skills/image-workbench`에 적용합니다.

## 검증

공급자 없는 저장소 검증:

```bash
python3 scripts/verify.py
```

이 명령은 계약·오프라인 픽스처만 다룹니다. 라이브 실행을 승인하거나 품질을 증명하지 않습니다.
