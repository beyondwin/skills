# Korean Writing Editor

[English](README.en.md)

## 이 스킬이 해결하는 문제

이미 있는 한국어 글을 받아서 고칩니다. 맞춤법, 띄어쓰기, 어색한 문장을 다루고, 원래 뜻과 글쓴이 말투, 이름·날짜·숫자 같은 값은 그대로 둡니다.

## 사용해야 할 때와 사용하지 말아야 할 때

이미 있는 한국어 글을 고치거나 다듬을 때 씁니다.

번역, 초안 작성, 요약, 코드 리뷰, 일상 대화, 사람 글인지 판별, 검출기 회피에는 쓰지 않습니다.

## 1분 설치와 첫 호출

기본 경로는 Codex `$skill-installer`와 공개 GitHub 스킬 경로입니다. 대상 디렉터리가 이미 있으면 설치기는 중단하며, 기존 설치를 자동으로 바꾸지 않습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
```

설치 후 다음 턴에서 명시 호출합니다.

```text
$korean-writing-editor 오탈자만 고쳐줘: (한국어 원문)
```

공유 설치·갱신·제거는 [설치](../../docs/users/ko/installation.md)를 따릅니다.

## 주요 흐름

이 스킬로 다룰 요청이면 기본은 `polish`입니다. 읽기 쉽게 조금 다듬되 뜻과 말투는 유지합니다. `diagnose`는 문제만 말하고 글을 고치지 않습니다. `correct`는 맞춤법, 띄어쓰기, 분명한 문법만 고칩니다.

## 안전과 개인정보

이 저장소는 텔레메트리를 넣지 않습니다. 사용자가 준 글을 픽스처, 로그, 말투 프로필로 저장하지 않습니다. 비공식 맞춤법 웹 서비스로 보내지 않고, 따로 요청하지 않으면 사실을 찾아오지 않습니다.

법률·의료·금융처럼 이해관계가 큰 글은 기계적 `correct` 또는 `diagnose`가 기본입니다.

자세한 경계는 [안전과 개인정보](../../docs/users/ko/safety-and-privacy.md)를 따릅니다.

## 호환성과 검증 수준

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

공유 지원 문장과 호스트 한계는 [호환성](../../docs/users/ko/compatibility.md)을 따릅니다. 증거 한계는 [검증](../../docs/users/ko/verification.md)을 따릅니다.

## 갱신과 버전 확인

갱신 전에 설치 대상을 확인하세요. 경로가 이 스킬 이름과 일치하는지, 실제 디렉터리인지, `SKILL.md`의 `name`과 `metadata.version`이 기대한 값인지 확인하세요. 확인 없이 기존 설치를 바꾸지 마세요.

현재 버전은 `SKILL.md`의 `metadata.version`과 [CHANGELOG](CHANGELOG.md)에서 확인합니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/korean-writing-editor/contract.md)
- [테스트](../../docs/maintainers/korean-writing-editor/testing.md)
- [릴리스](../../docs/maintainers/korean-writing-editor/release.md)
