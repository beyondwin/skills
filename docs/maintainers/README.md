# 관리자 문서

이 인덱스는 저장소 공통 규칙과 제품별 변경 프로토콜의 위치만 안내합니다. 사용자 설치 안내는 각 제품 README와 `docs/users/`에 있습니다.

관리자 문서는 한국어가 원본입니다. 명령, 파일 경로, 계약 식별자는 영어로 둡니다.

## 저장소 공통

| 문서 | 소유 |
| --- | --- |
| [구조](repository/architecture.md) | 설치 페이로드와 개발 증거 경계 |
| [버저닝](repository/versioning.md) | 제품·카탈로그 SemVer 판정표 |
| [카탈로그 릴리스](repository/catalog-release.md) | lock 채택과 원격 바이트 게이트 |
| [Archive 출처](repository/archive-migration.md) | 가져오기 pin과 provenance |

## 제품 프로토콜

각 제품은 계약, 테스트, 릴리스 문서를 가집니다. 한 제품의 동작 변경이 다른 제품 버전을 요구하지 않습니다.

### korean-writing-editor

- [계약](korean-writing-editor/contract.md) — 트리거, 기본값, 출력, 안전, 함께 고칠 파일
- [테스트](korean-writing-editor/testing.md) — 결정적 픽스처, 명령, 증거 한계
- [릴리스](korean-writing-editor/release.md) — 버전 원본, SemVer 예시, check/build/download, 실패 복구

### image-workbench

- [계약](image-workbench/contract.md) — 트리거, 기본값, 출력, 안전, 함께 고칠 파일
- [테스트](image-workbench/testing.md) — 결정적 픽스처, 명령, 증거 한계
- [릴리스](image-workbench/release.md) — 버전 원본, SemVer 예시, check/build/download, 실패 복구

### graspic

- [계약](graspic/contract.md) — 트리거, 기본값, 출력, 안전, 함께 고칠 파일
- [테스트](graspic/testing.md) — 결정적 픽스처, 명령, 증거 한계
- [릴리스](graspic/release.md) — 버전 원본, SemVer 예시, check/build/download, 실패 복구
