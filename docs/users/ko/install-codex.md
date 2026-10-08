# Codex 설치

[English](../en/install-codex.md) · [설치](installation.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md) · [검증](verification.md)

## `$skill-installer`로 설치

Codex에서 [`korean-writing-editor`](../../../skills/korean-writing-editor/README.ko.md)와 [`image-workbench`](../../../skills/image-workbench/README.ko.md)를 `$skill-installer`로 설치합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

각 스킬은 `$CODEX_HOME/skills/<skill-name>`에 들어갑니다(`CODEX_HOME`이 없으면 `~/.codex/skills`). 그 폴더가 이미 있으면 설치기가 멈춥니다.

그다음 새 대화에서 제품 README의 첫 호출을 써 보세요.

How It Works는 이 방법으로 설치하지 않습니다. [로컬 링크](install-local.md)를 쓰세요.

## 선택: 제3자 설치기

한국어 편집기만 다음 명령으로도 설치할 수 있습니다.

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

이것은 제3자 도구이며 자체 릴리스·텔레메트리 정책을 따릅니다.

## 선택: Git 클론에서 복사

두 설치기를 모두 쓰지 않으려면 저장소를 클론하고 스킬 폴더 하나를 직접 복사합니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
SKILL_SOURCE="$PWD/skills/korean-writing-editor"
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_SOURCE"
ls -ld "$SKILL_TARGET"
```

`$SKILL_TARGET`이 없거나, 이 스킬을 가리키는 링크임을 확인한 경우에만 복사하세요. 실제 폴더가 이미 있으면 멈추고 덮어쓰지 마세요. `image-workbench`도 같습니다.

## 갱신과 제거

먼저 정확한 대상을 확인합니다.

```bash
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_TARGET"
```

확인할 것:

- 경로가 이 스킬 이름으로 끝나는가
- 예상한 종류인가(실제 폴더인지 링크인지, 링크라면 어디를 가리키는지)
- 그 안 `SKILL.md`의 `name`과 `metadata.version`이 예상한 값인가

그런 뒤에만 그 경로 하나를 지우고, 갱신이라면 `$skill-installer`로 다시 설치하세요. `.../skills/image-workbench`도 같은 순서로 합니다.

상위 `skills` 폴더나 홈 폴더를 지우지 마세요. 원격 스크립트를 셸에 파이프하지 말고, 확인하지 않은 설치를 바꾸지 마세요.
