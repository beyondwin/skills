# Codex 설치

[English](../en/install-codex.md) · [설치](installation.md) · [호환성](compatibility.md) · [안전과 개인정보](safety-and-privacy.md) · [검증](verification.md)

이 안내는 Codex에서 [`korean-writing-editor`](../../../skills/korean-writing-editor/README.ko.md)와
[`image-workbench`](../../../skills/image-workbench/README.ko.md)를 설치하는 방법입니다.
How It Works는 [로컬 링크](install-local.md) 안내를 따르세요.

## `$skill-installer`로 설치

Codex 대화에 아래에서 필요한 스킬의 설치 요청을 입력합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

스킬은 `$CODEX_HOME/skills/<skill-name>`에 설치됩니다. `CODEX_HOME`이 설정되지
않았다면 `~/.codex/skills`를 사용합니다. 대상 폴더가 이미 있으면 설치기가 멈춥니다.
기존 설치를 바꾸려는 경우에는 아래의 갱신과 제거 절차에 따라 대상을 먼저 확인하세요.

설치가 끝나면 새 대화에서 제품 README의 첫 요청 예시를 입력해 보세요.

## 선택: 제3자 설치기

Korean Writing Editor에 한해 터미널에서 다음 명령으로도 설치할 수 있습니다.

```text
npx skills add beyondwin/skills --skill korean-writing-editor
```

이 설치기는 제3자 도구입니다. 업데이트와 사용 정보 수집(텔레메트리)에는
해당 도구의 정책이 적용됩니다.

## 선택: Git 클론에서 복사

직접 복사하려면 저장소를 클론한 뒤 원본과 설치 대상 경로를 확인합니다.
아래 명령은 경로를 확인하는 단계이며, 파일을 복사하지는 않습니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
SKILL_SOURCE="$PWD/skills/korean-writing-editor"
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_SOURCE"
ls -ld "$SKILL_TARGET"
```

확인 결과에 따라 다음과 같이 진행하세요. `image-workbench`를 직접 복사할 때도
같은 조건을 적용합니다.

- `$SKILL_TARGET`이 없으면 스킬 폴더를 복사할 수 있습니다.
- 링크가 있으면 이 스킬을 가리키는지 확인한 경우에만 복사합니다.
- 실제 폴더가 이미 있으면 복사를 멈추고 덮어쓰지 않습니다.

## 갱신과 제거

갱신과 제거 모두 기존 설치를 확인하는 것부터 시작합니다. 아래는
`korean-writing-editor`의 예시입니다. `image-workbench`도 스킬 이름을 바꿔
같은 순서로 진행합니다.

```bash
SKILL_TARGET="${CODEX_HOME:-$HOME/.codex}/skills/korean-writing-editor"
ls -ld "$SKILL_TARGET"
```

삭제하기 전에 다음 세 가지를 모두 확인하세요.

- 경로가 제거하거나 갱신할 스킬 이름으로 끝납니다.
- 실제 폴더인지 링크인지 확인했고, 링크라면 가리키는 위치도 예상한 대상입니다.
- 그 안의 `SKILL.md`에서 `name`과 `metadata.version`이 예상한 값과 일치합니다.

세 가지를 모두 확인한 뒤 해당 경로 하나만 삭제합니다. 제거가 목적이면 여기서
끝나고, 갱신이 목적이면 `$skill-installer`로 다시 설치합니다.

상위 `skills` 폴더나 홈 폴더를 지우지 마세요. 원격 스크립트를 셸에 파이프하지 말고, 확인하지 않은 설치를 바꾸지 마세요.
