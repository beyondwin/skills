# Pre-SDD Review

[English](README.en.md)

## 목적

승인된 설계와 구현 계획을 SDD 직전에 저장소 현실과 대조해 검토하고, 승인된 범위에서 고친 뒤 다시 검토합니다. 이 스킬은 SDD를 스스로 시작하지 않습니다.

## 사용할 때와 사용하지 않을 때

기본은 review-repair-re-review입니다. `review-only`는 명시적으로 요청할 때만 사용합니다. 새 설계나 계획 작성, 코드 리뷰, 구현, 교정, 릴리스 준비에는 사용하지 않습니다.

## 지원 호스트

pre-sdd-review: Codex만 측정된 지원 호스트입니다. 다른 호스트는 측정되지 않았습니다.

## 설치

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/pre-sdd-review
```

공유 설치 안내는 [설치](../../docs/users/ko/installation.md)에 있습니다.

## 첫 호출

```text
$pre-sdd-review docs/design.md docs/plan.md
```

## 예상 결과

검토 결과, 필요한 문서 보완, 그리고 재검토 상태를 받습니다. SDD는 시작하지 않습니다.

## 안전과 개인정보

읽은 저장소와 문서의 경계를 지키고, 비공개 자료를 테스트 자료나 로그로 저장하지 않습니다.

## 검증

Codex만 측정되었으며, 이 제품의 계약 검증은 결정적 오프라인 증거입니다.

## 업데이트와 제거

업데이트 또는 제거 전에 정확한 설치 대상과 `SKILL.md`의 이름·버전을 확인하세요.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/pre-sdd-review/contract.md)
- [테스트](../../docs/maintainers/products/pre-sdd-review/testing.md)
- [호환성](../../docs/maintainers/products/pre-sdd-review/compatibility.md)
- [릴리스](../../docs/maintainers/products/pre-sdd-review/release.md)
