# Image Workbench

[English](README.en.md)

## 목적

이 프로젝트에 넣을 PNG, JPG 같은 비트맵 이미지를 기획하고, 만들고, 고치고,
비교하고, 점검합니다. 프로젝트에 안 맞거나 주어진 조건을 어기는 결과는
쓰지 않습니다.

## 사용할 때와 사용하지 않을 때

프로젝트에 넣을 이미지가 필요할 때 씁니다.

재미로 한 장만 그리는 일, SVG나 코드로 만드는 UI, 실제 화면 구현, 외부
프롬프트 모음 베끼기에는 쓰지 않습니다.

## 지원 호스트

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

지금은 Codex에서만 지원합니다. 다른 호스트는
[호환성](../../docs/users/ko/compatibility.md)을 보세요.

## 설치

Codex에서는 공개 GitHub 경로를 `$skill-installer`에 전달합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

나머지 설치 방법은 [설치](../../docs/users/ko/installation.md)를 보세요.

## 첫 호출

설치 다음 대화에서 이렇게 부릅니다.

```text
$image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
```

## 예상 결과

먼저 모드를 하나만 고릅니다. `brief`는 어떤 이미지가 필요한지 정리만 하고
만들지 않습니다. `generate`는 새 이미지를 만듭니다. `edit`는 있는 이미지를
고칩니다. `audit`은 점검만 하고 만들지 않습니다. `brief`와 `audit`은 읽기
전용입니다. 생성·편집 요청이 분명할 때만 이미지를 만듭니다.

최종 파일은 스킬 폴더에서 `python3 scripts/inspect_asset.py`로 파일 형식과
크기를 확인합니다.

## 안전과 개인정보

입력 이미지의 역할은 하나입니다. 역할은 `edit_target`, `subject_reference`,
`style_reference`, 또는 `compositing_input`입니다. 참조 이미지는 사람,
상표, 보호된 작업을 복제할 권리를 주지 않습니다. 인물·상표·예시 이미지의
consent가 불명하면 보류합니다.

자세한 내용은 [안전과 개인정보](../../docs/users/ko/safety-and-privacy.md)를
보세요.

## 검증

오프라인 검사는 계약만 확인합니다. 실제 이미지 품질을 증명하지 않습니다.
증거 한계는 [검증](../../docs/users/ko/verification.md)을 보세요.

## 업데이트와 제거

바꾸거나 지우기 전에 설치 폴더를 확인하세요. 절차는
[설치](../../docs/users/ko/installation.md)를 보세요.

현재 버전은 `SKILL.md`의 `metadata.version`과 [CHANGELOG](CHANGELOG.md)에서
봅니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/image-workbench/contract.md)
- [테스트](../../docs/maintainers/products/image-workbench/testing.md)
- [호환성](../../docs/maintainers/products/image-workbench/compatibility.md)
- [릴리스](../../docs/maintainers/products/image-workbench/release.md)
