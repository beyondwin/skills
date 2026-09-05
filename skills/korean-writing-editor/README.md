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
[호환성](../../docs/users/ko/compatibility.md)을 보세요.

## 설치

Codex에서는 공개 GitHub 경로를 `$skill-installer`에 전달합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor
```

나머지 설치 방법은 [설치](../../docs/users/ko/installation.md)를 보세요.

## 첫 호출

설치 다음 대화에서 이렇게 부릅니다.

```text
$korean-writing-editor 오탈자만 고쳐줘: (한국어 원문)
```

## 예상 결과

기본은 `polish`입니다. 읽기 쉽게 조금 다듬되 뜻과 말투는 유지합니다.
`diagnose`는 문제만 말하고 글을 고치지 않습니다. `correct`는 맞춤법,
띄어쓰기, 분명한 문법만 고칩니다.

## 안전과 개인정보

준 글을 픽스처, 로그, 말투 프로필로 남기지 않습니다. 비공식 맞춤법
사이트로 보내지 않습니다. 따로 시키지 않으면 사실을 찾아오지 않습니다.

법률·의료·금융처럼 이해관계가 큰 글은 기계적 `correct` 또는 `diagnose`가
기본입니다.

자세한 내용은 [안전과 개인정보](../../docs/users/ko/safety-and-privacy.md)를
보세요.

## 검증

오프라인 검사는 계약만 확인합니다. 실제 교정 품질을 증명하지 않습니다.
증거 한계는 [검증](../../docs/users/ko/verification.md)을 보세요.

## 업데이트와 제거

바꾸거나 지우기 전에 설치 폴더를 확인하세요. 절차는
[설치](../../docs/users/ko/installation.md)를 보세요.

현재 버전은 `SKILL.md`의 `metadata.version`과 [CHANGELOG](CHANGELOG.md)에서
봅니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/korean-writing-editor/contract.md)
- [테스트](../../docs/maintainers/products/korean-writing-editor/testing.md)
- [호환성](../../docs/maintainers/products/korean-writing-editor/compatibility.md)
- [릴리스](../../docs/maintainers/products/korean-writing-editor/release.md)
