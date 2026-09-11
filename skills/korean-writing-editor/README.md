# Korean Writing Editor

[English](README.en.md)

## 목적

이미 있는 한국어 글을 고칩니다. 맞춤법, 띄어쓰기, 어색한 문장을 다룹니다.
뜻과 말투는 그대로 둡니다. 이름, 날짜, 숫자도 그대로 둡니다.

## 사용할 때와 사용하지 않을 때

있는 한국어 글을 다듬을 때 씁니다.

번역, 초안 작성, 요약, 코드 리뷰, 일상 대화, 사람 글인지 판별, 검출기
회피에는 쓰지 않습니다.

## 지원 호스트

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

지금은 Codex에서만 지원합니다. 다른 호스트는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을 보세요.

## 설치

Codex에서는 공개 GitHub 경로를 `$skill-installer`에 전달합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
```

나머지 설치 방법은 [설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-codex.md)를 보세요.

## 첫 호출

설치 다음 대화에서 이렇게 부릅니다.

```text
$korean-writing-editor 오탈자만 고쳐줘: (한국어 원문)
```

## 예상 결과

기본은 `polish`입니다. 읽기 쉽게 조금 다듬되 뜻과 말투는 유지합니다.
`diagnose`는 문제만 말하고 글을 고치지 않습니다. `correct`는 맞춤법,
띄어쓰기, 분명히 고쳐야 하는 국소 문법만 고칩니다. `polish`도 이 필수
교정을 먼저 하고, 필요할 때만 가독성과 국소 흐름을 추가로 다듬습니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/release.md)
