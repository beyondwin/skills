# Image Workbench

[English](README.en.md)

## 이 스킬이 해결하는 문제

로컬 프로젝트에 맞는 래스터 자산을 계획·생성·편집·비교·점검합니다. 프로젝트 맥락, 입력 제약, 저장과 연동을 지킵니다.

## 사용해야 할 때와 사용하지 말아야 할 때

프로젝트에 묶인 래스터 산출물이 필요할 때 씁니다.

재미용 일회성 이미지, SVG·네이티브 UI, 실제 프론트엔드 구현, 외부 프롬프트 갤러리 복제에 쓰지 않습니다.

## 1분 설치와 첫 호출

기본 경로는 Codex `$skill-installer`와 공개 GitHub 스킬 경로입니다. 대상 디렉터리가 이미 있으면 설치기는 중단하며, 기존 설치를 자동으로 바꾸지 않습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench
```

설치 후 다음 턴에서 명시 호출합니다.

```text
$image-workbench 이 프로젝트 랜딩 페이지 hero 이미지를 만들어줘.
```

공유 설치·갱신·제거는 [설치](../../docs/users/ko/installation.md)를 따릅니다.

## 주요 흐름

모드를 먼저 고릅니다: `brief`, `generate`, `edit`, `audit`. `brief`와 `audit`은 읽기 전용이며 생성을 승인하지 않습니다. 생성·편집만 이미지 호출을 승인합니다. 최종 파일은 스킬 루트의 `python3 scripts/inspect_asset.py`로 기계 사실을 점검합니다.

## 안전과 개인정보

이 저장소는 텔레메트리를 넣지 않습니다. 입력 이미지는 역할이 하나입니다: `edit_target`, `subject_reference`, `style_reference`, 또는 `compositing_input`. 참조 이미지는 사람, 상표, 보호된 작업을 복제할 권리를 주지 않습니다. 인물·상표·예시 이미지의 consent가 불명하면 보류합니다.

자세한 경계는 [안전과 개인정보](../../docs/users/ko/safety-and-privacy.md)를 따릅니다.

## 호환성과 검증 수준

image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing.

공유 지원 문장과 호스트 한계는 [호환성](../../docs/users/ko/compatibility.md)을 따릅니다. 증거 한계는 [검증](../../docs/users/ko/verification.md)을 따릅니다.

## 갱신과 버전 확인

갱신 전에 설치 대상을 확인하세요. 경로가 이 스킬 이름과 일치하는지, 실제 디렉터리인지, `SKILL.md`의 `name`과 `metadata.version`이 기대한 값인지 봅니다. 확인 없이 기존 설치를 바꾸지 마세요.

현재 버전은 `SKILL.md`의 `metadata.version`과 [CHANGELOG](CHANGELOG.md)에서 확인합니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [관리자 문서](../../docs/maintainers/image-workbench.md)
