# Korean Writing Editor

[English](README.en.md)

## 목적

이미 있는 한국어 글을 고칩니다. 맞춤법, 띄어쓰기, 어색한 문장을 다룹니다.
뜻과 말투, 이름, 날짜, 숫자는 그대로 둡니다.

## 사용할 때와 사용하지 않을 때

이미 있는 한국어 글을 고치거나 다듬을 때 씁니다.

번역, 초안 작성, 요약, 코드 리뷰, 일상 대화, AI가 쓴 글인지 판별, 검출기
회피에는 쓰지 않습니다.

## 지원 호스트

korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

지금 지원하는 호스트는 Codex뿐입니다. 다른 호스트는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을 보세요.

## 설치

Codex에서는 공개 GitHub 경로를 `$skill-installer`에 전달합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
```

공통 설치 방법은 [설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-codex.md)를 보세요.

## 첫 호출

다음처럼 부릅니다. 기본은 가볍게 다듬기입니다.

```text
$korean-writing-editor 자연스럽게 다듬어줘: (한국어 원문)
```

맞춤법과 띄어쓰기만 고치려면:

```text
$korean-writing-editor 오탈자만 고쳐줘: (한국어 원문)
```

`$korean-writing-editor`와 `/korean-writing-editor` 둘 다 됩니다. 두 형식 모두
Codex에서 확인했습니다.

## 예상 결과

- `polish`(기본): 읽기 쉽게 조금 다듬고, 뜻과 말투는 유지합니다.
- `diagnose`: 문제만 짚고, 글을 다시 쓰지 않습니다.
- `correct`: 맞춤법, 띄어쓰기, 분명히 틀린 문법만 고칩니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/korean-writing-editor/release.md)
